from typing import List, Optional

from mako.template import Template

from truefoundry.common.constants import ENV_VARS, PythonPackageManager
from truefoundry.deploy._autogen.models import TaskPySparkBuild
from truefoundry.deploy.builder.utils import (
    generate_apt_install_command,
    generate_pip_install_command,
    generate_secret_mounts,
    generate_uv_pip_install_command,
    get_available_secrets,
)

# TODO[GW]: Switch to a non-root user inside the container
_POST_PYTHON_INSTALL_TEMPLATE = """
% if apt_install_command is not None:
RUN ${apt_install_command}
% endif
% if requirements_path is not None:
COPY ${requirements_path} ${requirements_destination_path}
% endif
% if python_packages_install_command is not None:
RUN ${package_manager_config_secret_mount} ${python_packages_install_command}
% endif
COPY . /app
WORKDIR /app
"""

# TODO[GW]: Check if the entrypoint for the image needs to change
# Using /opt/venv/ because flyte seems to be using it and this doesn't look configurable
# TODO[GW]: Double check this^
DOCKERFILE_TEMPLATE = Template(
    """
FROM ${spark_image_repo}:${spark_version}
ENV PATH=/opt/venv/bin:$PATH
USER root
RUN mkdir -p /var/lib/apt/lists/partial && \
    apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends git && \
    python -m venv /opt/venv/ && \
    rm -rf /var/lib/apt/lists/*
"""
    + _POST_PYTHON_INSTALL_TEMPLATE
)


def get_additional_pip_packages(build_configuration: TaskPySparkBuild):
    return [
        f"pyspark=={build_configuration.spark_version}",
    ]


def generate_dockerfile_content(
    build_configuration: TaskPySparkBuild,
    package_manager: str = ENV_VARS.TFY_PYTHON_BUILD_PACKAGE_MANAGER,
    docker_build_extra_args: Optional[List[str]] = None,
) -> str:
    # Get available secrets from docker build extra args
    available_secrets = set()
    if docker_build_extra_args:
        available_secrets = get_available_secrets(docker_build_extra_args)

    # TODO (chiragjn): Handle recursive references to other requirements files e.g. `-r requirements-gpu.txt`
    requirements_path = build_configuration.requirements_path
    requirements_destination_path = (
        "/tmp/requirements.txt" if requirements_path else None
    )
    pip_packages = get_additional_pip_packages(build_configuration) + (
        build_configuration.pip_packages or []
    )
    if package_manager == PythonPackageManager.PIP.value:
        python_packages_install_command = generate_pip_install_command(
            requirements_path=requirements_destination_path,
            pip_packages=pip_packages,
            available_secrets=available_secrets,
        )
    elif package_manager == PythonPackageManager.UV.value:
        python_packages_install_command = generate_uv_pip_install_command(
            requirements_path=requirements_destination_path,
            pip_packages=pip_packages,
            available_secrets=available_secrets,
        )
    else:
        raise ValueError(f"Unsupported package manager: {package_manager}")

    apt_install_command = generate_apt_install_command(
        apt_packages=build_configuration.apt_packages
    )
    template_args = {
        "spark_image_repo": ENV_VARS.TFY_TASK_PYSPARK_BUILD_SPARK_IMAGE_REPO,
        "spark_version": build_configuration.spark_version,
        "apt_install_command": apt_install_command,
        "requirements_path": requirements_path,
        "requirements_destination_path": requirements_destination_path,
        "python_packages_install_command": python_packages_install_command,
    }

    if available_secrets:
        template_args["package_manager_config_secret_mount"] = generate_secret_mounts(
            available_secrets=available_secrets,
            python_dependencies_type="pip",
            package_manager=package_manager,
        )
    else:
        template_args["package_manager_config_secret_mount"] = ""

    template = DOCKERFILE_TEMPLATE

    dockerfile_content = template.render(**template_args)
    return dockerfile_content
