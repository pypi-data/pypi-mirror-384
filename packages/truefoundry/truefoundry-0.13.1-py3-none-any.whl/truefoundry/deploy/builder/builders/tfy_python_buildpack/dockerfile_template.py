from copy import deepcopy
from typing import Dict, List, Optional, Set, Union

from jinja2 import Template

from truefoundry.common.constants import ENV_VARS, PythonPackageManager
from truefoundry.deploy._autogen.models import UV, Pip, Poetry
from truefoundry.deploy.builder.utils import (
    check_whether_poetry_toml_exists,
    generate_apt_install_command,
    generate_command_to_install_from_uv_lock,
    generate_pip_install_command,
    generate_poetry_install_command,
    generate_secret_mounts,
    generate_uv_pip_install_command,
    get_available_secrets,
)
from truefoundry.deploy.v2.lib.patched_models import (
    CUDAVersion,
    PythonBuild,
    _resolve_requirements_path,
)
from truefoundry.pydantic_v1 import BaseModel


class TemplateContext(BaseModel):
    """Pydantic model for template context used in Dockerfile generation."""

    # Common fields
    python_image_repo: str
    python_version: str
    apt_install_command: Optional[str] = None
    package_manager_config_secret_mount: str = ""

    # Pip-specific fields
    requirements_path: Optional[str] = None
    requirements_destination_path: Optional[str] = None
    python_packages_install_command: Optional[str] = None

    # UV-specific fields
    final_uv_sync_command: Optional[str] = None

    # Poetry-specific fields
    final_poetry_install_command: Optional[str] = None
    poetry_version_expression: Optional[str] = None
    poetry_toml_exists: bool = False


CUDA_BASE_IMAGE_TEMPLATE = """\
FROM nvidia/cuda:{{ cuda_image_tag }} AS base
SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-c"]

ENV PATH=/virtualenvs/venv/bin:$PATH
ENV VIRTUAL_ENV=/virtualenvs/venv/
RUN echo "deb https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu $(cat /etc/os-release | grep UBUNTU_CODENAME | cut -d = -f 2) main" >> /etc/apt/sources.list && \\
    echo "deb-src https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu $(cat /etc/os-release | grep UBUNTU_CODENAME | cut -d = -f 2) main" >> /etc/apt/sources.list && \\
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776 && \\
    apt update && \\
    DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends git python{{ python_version }}-dev python{{ python_version }}-venv && \\
    python{{ python_version }} -m venv /virtualenvs/venv/ && \\
    rm -rf /var/lib/apt/lists/* && \\
    python -m pip install -U pip setuptools wheel
"""

STANDARD_BASE_IMAGE_TEMPLATE = """\
FROM {{ python_image_repo }}:{{ python_version }} AS base
SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-c"]

ENV PATH=/virtualenvs/venv/bin:$PATH
ENV VIRTUAL_ENV=/virtualenvs/venv/
RUN apt update && \\
    DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends git && \\
    python -m venv /virtualenvs/venv/ && \\
    rm -rf /var/lib/apt/lists/* && \\
    python -m pip install -U pip setuptools wheel
"""


APT_PACKAGES_TEMPLATE = """
{% if apt_install_command %}
RUN {{ apt_install_command }}
{% endif %}
"""


PIP_DEPENDENCIES_TEMPLATE = """\
{% if requirements_path %}
COPY {{ requirements_path }} {{ requirements_destination_path }}
{% endif %}

{% if python_packages_install_command %}
RUN {{ package_manager_config_secret_mount }} {{ python_packages_install_command }}
{% endif %}

COPY . /app
WORKDIR /app
"""

UV_DEPENDENCIES_TEMPLATE = """\
# Set up UV environment
WORKDIR /app
COPY pyproject.toml uv.lock .
{% if python_packages_install_command %}
RUN {{ package_manager_config_secret_mount }} {{ python_packages_install_command }}
{% endif %}

COPY ./ .
{% if final_uv_sync_command %}
RUN {{ package_manager_config_secret_mount }} {{ final_uv_sync_command }}
{% endif %}
"""

POETRY_DEPENDENCIES_TEMPLATE = """\
RUN python -m venv /opt/poetry
ENV PATH="/opt/poetry/bin:$PATH"
RUN pip install -q --no-cache-dir -U "poetry{{ poetry_version_expression }}"

WORKDIR /app
COPY pyproject.toml poetry.lock .
{% if poetry_toml_exists %}
COPY poetry.toml .
{%- endif %}
RUN poetry config virtualenvs.create false --local \\
    && poetry config virtualenvs.in-project false --local

ENV PATH="/virtualenvs/venv/bin:$PATH"
ENV VIRTUAL_ENV="/virtualenvs/venv/"

{% if python_packages_install_command %}
RUN {{ package_manager_config_secret_mount }} {{ python_packages_install_command }}
{% endif %}

COPY ./ .

{% if final_poetry_install_command %}
RUN {{ package_manager_config_secret_mount }} {{ final_poetry_install_command }}
{% endif %}

RUN rm -rf /opt/poetry
"""

DOCKERFILE_TEMPLATE = """\
{{ base_image_setup }}
{{ apt_packages_section }}
{{ python_dependencies_section }}
"""


CUDA_VERSION_TO_IMAGE_TAG: Dict[str, str] = {
    CUDAVersion.CUDA_11_0_CUDNN8.value: "11.0.3-cudnn8-runtime-ubuntu20.04",
    CUDAVersion.CUDA_11_1_CUDNN8.value: "11.1.1-cudnn8-runtime-ubuntu20.04",
    CUDAVersion.CUDA_11_2_CUDNN8.value: "11.2.2-cudnn8-runtime-ubuntu20.04",
    CUDAVersion.CUDA_11_3_CUDNN8.value: "11.3.1-cudnn8-runtime-ubuntu20.04",
    CUDAVersion.CUDA_11_4_CUDNN8.value: "11.4.3-cudnn8-runtime-ubuntu20.04",
    CUDAVersion.CUDA_11_5_CUDNN8.value: "11.5.2-cudnn8-runtime-ubuntu20.04",
    CUDAVersion.CUDA_11_6_CUDNN8.value: "11.6.2-cudnn8-runtime-ubuntu20.04",
    CUDAVersion.CUDA_11_7_CUDNN8.value: "11.7.1-cudnn8-runtime-ubuntu22.04",
    CUDAVersion.CUDA_11_8_CUDNN8.value: "11.8.0-cudnn8-runtime-ubuntu22.04",
    CUDAVersion.CUDA_12_0_CUDNN8.value: "12.0.1-cudnn8-runtime-ubuntu22.04",
    CUDAVersion.CUDA_12_1_CUDNN8.value: "12.1.1-cudnn8-runtime-ubuntu22.04",
    CUDAVersion.CUDA_12_2_CUDNN8.value: "12.2.2-cudnn8-runtime-ubuntu22.04",
    CUDAVersion.CUDA_12_3_CUDNN9.value: "12.3.2-cudnn9-runtime-ubuntu22.04",
    # From 12.4+ onwards, the image tags drop the cudnn version
    CUDAVersion.CUDA_12_4_CUDNN9.value: "12.4.1-cudnn-runtime-ubuntu22.04",
    CUDAVersion.CUDA_12_5_CUDNN9.value: "12.5.1-cudnn-runtime-ubuntu22.04",
    CUDAVersion.CUDA_12_6_CUDNN9.value: "12.6.3-cudnn-runtime-ubuntu22.04",
    CUDAVersion.CUDA_12_8_CUDNN9.value: "12.8.1-cudnn-runtime-ubuntu22.04",
    CUDAVersion.CUDA_12_9_CUDNN9.value: "12.9.1-cudnn-runtime-ubuntu22.04",
}


def generate_dockerfile_content(
    build_configuration: PythonBuild,
    package_manager: str = ENV_VARS.TFY_PYTHON_BUILD_PACKAGE_MANAGER,
    docker_build_extra_args: Optional[List[str]] = None,
) -> str:
    if isinstance(build_configuration, dict):
        build_configuration = PythonBuild(**build_configuration)
    if not build_configuration.python_version:
        raise ValueError(
            "`python_version` is required for `tfy-python-buildpack` builder"
        )

    # Set up Python dependencies
    python_dependencies = deepcopy(build_configuration.python_dependencies)
    if not python_dependencies:
        python_dependencies = Pip(
            type="pip",
            requirements_path=build_configuration.requirements_path,
            pip_packages=build_configuration.pip_packages,
        )

    # Get available secrets from docker build extra args
    available_secrets = set()
    if docker_build_extra_args:
        available_secrets = get_available_secrets(docker_build_extra_args)

    # Prepare template context
    context = _build_template_context(
        build_configuration=build_configuration,
        python_dependencies=python_dependencies,
        package_manager=package_manager,
        available_secrets=available_secrets,
    )

    # Build sections
    base_image_setup = _build_base_image_section(build_configuration)
    apt_packages_section = _build_apt_packages_section(context.apt_install_command)
    python_dependencies_section = _build_python_dependencies_section(
        python_dependencies.type, context
    )

    template = Template(DOCKERFILE_TEMPLATE)
    return template.render(
        base_image_setup=base_image_setup,
        apt_packages_section=apt_packages_section,
        python_dependencies_section=python_dependencies_section,
    )


def _build_template_context(
    build_configuration: PythonBuild,
    python_dependencies: Union[Pip, UV, Poetry],
    package_manager: str,
    available_secrets: Set[str],
) -> TemplateContext:
    if not build_configuration.python_version:
        raise ValueError(
            "`python_version` is required for `tfy-python-buildpack` builder"
        )
    # Set up package manager config secret mount
    python_dependencies_type = python_dependencies.type
    package_manager_config_secret_mount = ""
    if available_secrets:
        package_manager_config_secret_mount = generate_secret_mounts(
            available_secrets=available_secrets,
            python_dependencies_type=python_dependencies_type,
            package_manager=package_manager,
        )

    # Configure dependencies based on type
    if isinstance(python_dependencies, UV):
        uv_context = _build_uv_context(
            python_dependencies,
            available_secrets,
        )
        return TemplateContext(
            python_image_repo=ENV_VARS.TFY_PYTHONBUILD_PYTHON_IMAGE_REPO,
            python_version=build_configuration.python_version,
            apt_install_command=generate_apt_install_command(
                apt_packages=build_configuration.apt_packages
            ),
            package_manager_config_secret_mount=package_manager_config_secret_mount,
            python_packages_install_command=uv_context[
                "python_packages_install_command"
            ],
            final_uv_sync_command=uv_context["final_uv_sync_command"],
        )
    elif isinstance(python_dependencies, Poetry):
        poetry_toml_exists = check_whether_poetry_toml_exists(
            build_context_path=build_configuration.build_context_path,
        )
        poetry_context = _build_poetry_context(python_dependencies, available_secrets)
        return TemplateContext(
            python_image_repo=ENV_VARS.TFY_PYTHONBUILD_PYTHON_IMAGE_REPO,
            python_version=build_configuration.python_version,
            apt_install_command=generate_apt_install_command(
                apt_packages=build_configuration.apt_packages
            ),
            package_manager_config_secret_mount=package_manager_config_secret_mount,
            python_packages_install_command=poetry_context[
                "python_packages_install_command"
            ],
            final_poetry_install_command=poetry_context["final_poetry_install_command"],
            poetry_version_expression=poetry_context["poetry_version_expression"],
            poetry_toml_exists=poetry_toml_exists,
        )
    elif isinstance(python_dependencies, Pip):
        pip_context = _build_pip_context(
            build_configuration,
            python_dependencies,
            package_manager,
            available_secrets,
        )
        return TemplateContext(
            python_image_repo=ENV_VARS.TFY_PYTHONBUILD_PYTHON_IMAGE_REPO,
            python_version=build_configuration.python_version,
            apt_install_command=generate_apt_install_command(
                apt_packages=build_configuration.apt_packages
            ),
            package_manager_config_secret_mount=package_manager_config_secret_mount,
            requirements_path=pip_context["requirements_path"],
            requirements_destination_path=pip_context["requirements_destination_path"],
            python_packages_install_command=pip_context[
                "python_packages_install_command"
            ],
        )
    else:
        raise ValueError(f"Unsupported dependency type: {python_dependencies_type}")


def _build_base_image_section(build_configuration: PythonBuild) -> str:
    if build_configuration.cuda_version:
        cuda_image_tag = CUDA_VERSION_TO_IMAGE_TAG.get(
            build_configuration.cuda_version, build_configuration.cuda_version
        )
        template = Template(CUDA_BASE_IMAGE_TEMPLATE)
        return template.render(
            cuda_image_tag=cuda_image_tag,
            python_version=build_configuration.python_version,
        )
    else:
        template = Template(STANDARD_BASE_IMAGE_TEMPLATE)
        return template.render(
            python_image_repo=ENV_VARS.TFY_PYTHONBUILD_PYTHON_IMAGE_REPO,
            python_version=build_configuration.python_version,
        )


def _build_apt_packages_section(apt_install_command: Optional[str]) -> str:
    template = Template(APT_PACKAGES_TEMPLATE)
    return template.render(apt_install_command=apt_install_command)


def _build_python_dependencies_section(
    python_dependencies_type: str, context: TemplateContext
) -> str:
    if python_dependencies_type == "pip":
        template = Template(PIP_DEPENDENCIES_TEMPLATE)
        return template.render(**context.dict())
    elif python_dependencies_type == "uv":
        template = Template(UV_DEPENDENCIES_TEMPLATE)
        return template.render(**context.dict())
    elif python_dependencies_type == "poetry":
        template = Template(POETRY_DEPENDENCIES_TEMPLATE)
        return template.render(**context.dict())
    else:
        raise ValueError(f"Unsupported dependency type: {python_dependencies_type}")


def _build_uv_context(python_dependencies: UV, available_secrets: Set[str]) -> Dict:
    python_packages_install_command = generate_command_to_install_from_uv_lock(
        sync_options=python_dependencies.sync_options,
        uv_version=python_dependencies.uv_version,
        available_secrets=available_secrets,
    )
    final_uv_sync_command = generate_command_to_install_from_uv_lock(
        sync_options=python_dependencies.sync_options,
        uv_version=python_dependencies.uv_version,
        install_project=True,
        available_secrets=available_secrets,
    )

    return {
        "python_packages_install_command": python_packages_install_command,
        "final_uv_sync_command": final_uv_sync_command,
    }


def _build_poetry_context(
    python_dependencies: Poetry, available_secrets: Set[str]
) -> Dict:
    python_packages_install_command = generate_poetry_install_command(
        install_options=python_dependencies.install_options,
        available_secrets=available_secrets,
    )
    final_poetry_install_command = generate_poetry_install_command(
        install_options=python_dependencies.install_options,
        install_project=True,
        available_secrets=available_secrets,
    )

    poetry_version = python_dependencies.poetry_version
    # Handle "latest" poetry version by using major version constraint
    if poetry_version == "latest":
        major_version = ENV_VARS.TFY_PYTHON_BUILD_LATEST_POETRY_MAJOR_VERSION
        poetry_version_expression = f">={major_version},<{major_version + 1}"
    else:
        # For regular versions, use ~= operator for compatibility
        poetry_version_expression = f"~={poetry_version}"

    return {
        "python_packages_install_command": python_packages_install_command,
        "final_poetry_install_command": final_poetry_install_command,
        "poetry_version_expression": poetry_version_expression,
    }


def _build_pip_context(
    build_configuration: PythonBuild,
    python_dependencies: Pip,
    package_manager: str,
    available_secrets: Set[str],
) -> Dict:
    # TODO (chiragjn): Handle recursive references to other requirements files e.g. `-r requirements-gpu.txt`
    requirements_path = _resolve_requirements_path(
        build_context_path=build_configuration.build_context_path,
        requirements_path=python_dependencies.requirements_path,
    )
    requirements_destination_path = (
        "/tmp/requirements.txt" if requirements_path else None
    )

    if package_manager == PythonPackageManager.PIP.value:
        python_packages_install_command = generate_pip_install_command(
            requirements_path=requirements_destination_path,
            pip_packages=python_dependencies.pip_packages,
            available_secrets=available_secrets,
        )
    elif package_manager == PythonPackageManager.UV.value:
        python_packages_install_command = generate_uv_pip_install_command(
            requirements_path=requirements_destination_path,
            pip_packages=python_dependencies.pip_packages,
            available_secrets=available_secrets,
        )
    else:
        raise ValueError(f"Unsupported package manager: {package_manager}")

    return {
        "requirements_path": requirements_path,
        "requirements_destination_path": requirements_destination_path,
        "python_packages_install_command": python_packages_install_command,
    }
