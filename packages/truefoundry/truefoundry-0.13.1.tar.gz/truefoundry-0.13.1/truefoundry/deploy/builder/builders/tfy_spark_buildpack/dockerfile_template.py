from typing import List, Optional

from mako.template import Template

from truefoundry.common.constants import ENV_VARS, PythonPackageManager
from truefoundry.deploy._autogen.models import SparkBuild
from truefoundry.deploy.builder.utils import (
    generate_pip_install_command,
    generate_secret_mounts,
    generate_uv_pip_install_command,
    get_available_secrets,
)

# TODO (chiragjn): Switch to a non-root user inside the container

_POST_PYTHON_INSTALL_TEMPLATE = """
% if requirements_path is not None:
COPY ${requirements_path} ${requirements_destination_path}
% endif
% if python_packages_install_command is not None:
RUN ${package_manager_config_secret_mount} ${python_packages_install_command}
% endif
ENV PYTHONDONTWRITEBYTECODE=1
ENV IPYTHONDIR=/tmp/.ipython
USER 1001
COPY . /app
"""

_POST_USER_TEMPLATE = """
COPY tfy_execute_notebook.py /app/tfy_execute_notebook.py
"""

_ALMOND_INSTALL_TEMPLATE = """
ENV COURSIER_CACHE=/opt/coursier-cache
RUN install_packages curl
RUN curl -Lo coursier https://git.io/coursier-cli && \
    chmod +x coursier && \
    ./coursier launch almond:0.14.1 -- --install --global && \
    chown -R 1001:0 /usr/local/share/jupyter && \
    chown -R 1001:0 /opt/coursier-cache && \
    rm -f coursier
"""

# Docker image size with almond - 1.26GB
# Docker image size without almond - 1.1GB
# Not much harm in packaging almond by default
DOCKERFILE_TEMPLATE = Template(
    """
FROM ${spark_image_repo}:${spark_version}
USER root
RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*
"""
    + _ALMOND_INSTALL_TEMPLATE
    + _POST_PYTHON_INSTALL_TEMPLATE
    + _POST_USER_TEMPLATE
)

ADDITIONAL_PIP_PACKAGES = [
    "papermill>=2.6.0,<2.7.0",
    "ipykernel>=6.0.0,<7.0.0",
    "nbconvert>=7.16.6,<7.17.0",
    "boto3>=1.38.43,<1.40.0",
]


def generate_dockerfile_content(
    build_configuration: SparkBuild,
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
    if not build_configuration.spark_version:
        raise ValueError(
            "`spark_version` is required for `tfy-spark-buildpack` builder"
        )

    if package_manager == PythonPackageManager.PIP.value:
        python_packages_install_command = generate_pip_install_command(
            requirements_path=requirements_destination_path,
            pip_packages=ADDITIONAL_PIP_PACKAGES,
            available_secrets=available_secrets,
        )
    elif package_manager == PythonPackageManager.UV.value:
        python_packages_install_command = generate_uv_pip_install_command(
            requirements_path=requirements_destination_path,
            pip_packages=ADDITIONAL_PIP_PACKAGES,
            available_secrets=available_secrets,
        )
    else:
        raise ValueError(f"Unsupported package manager: {package_manager}")

    template_args = {
        "spark_image_repo": ENV_VARS.TFY_SPARK_BUILD_SPARK_IMAGE_REPO,
        "spark_version": build_configuration.spark_version,
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

    dockerfile_content = DOCKERFILE_TEMPLATE.render(**template_args)
    return dockerfile_content
