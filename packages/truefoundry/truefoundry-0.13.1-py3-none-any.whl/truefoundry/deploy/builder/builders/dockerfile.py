import os
from typing import Dict, List, Optional

from truefoundry.deploy._autogen.models import DockerFileBuild
from truefoundry.deploy.builder.docker_service import build_docker_image
from truefoundry.logger import logger

__all__ = ["build"]


def _get_expanded_and_absolute_path(path: str):
    return os.path.abspath(os.path.expanduser(path))


def _build_docker_image(
    tag: str,
    dockerfile: str,
    path: str = ".",
    build_args: Optional[Dict[str, str]] = None,
    extra_opts: Optional[List[str]] = None,
):
    dockerfile = _get_expanded_and_absolute_path(dockerfile)
    path = _get_expanded_and_absolute_path(path)

    build_docker_image(
        path=path,
        tag=tag,
        # TODO: can we pick target platform(s) picked from cluster
        platform="linux/amd64",
        dockerfile=dockerfile,
        build_args=build_args,
        extra_opts=extra_opts,
    )


def build(
    tag: str,
    build_configuration: DockerFileBuild,
    extra_opts: Optional[List[str]] = None,
):
    dockerfile_path = _get_expanded_and_absolute_path(
        build_configuration.dockerfile_path
    )
    with open(dockerfile_path) as f:
        dockerfile_content = f.read()
        logger.info("Dockerfile content:-")
        logger.info(dockerfile_content)

    _build_docker_image(
        tag=tag,
        dockerfile=build_configuration.dockerfile_path,
        path=build_configuration.build_context_path,
        build_args=build_configuration.build_args,
        extra_opts=extra_opts,
    )
