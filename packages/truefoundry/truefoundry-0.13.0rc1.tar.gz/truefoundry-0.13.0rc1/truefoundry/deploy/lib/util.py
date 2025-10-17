import os
import re
from typing import Union

from truefoundry.common.utils import get_expanded_and_absolute_path
from truefoundry.deploy._autogen.models import (
    UV,
    Build,
    DockerFileBuild,
    Pip,
    Poetry,
    PythonBuild,
)


def get_application_fqn_from_deployment_fqn(deployment_fqn: str) -> str:
    if not re.search(r":\d+$", deployment_fqn):
        raise ValueError(
            "Invalid `deployment_fqn` format. A deployment fqn is supposed to end with a version number"
        )
    application_fqn, _ = deployment_fqn.rsplit(":", 1)
    return application_fqn


def get_deployment_fqn_from_application_fqn(
    application_fqn: str, version: Union[str, int]
) -> str:
    return f"{application_fqn}:{version}"


def find_list_paths(data, parent_key="", sep="."):
    list_paths = []
    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            list_paths.extend(find_list_paths(value, new_key, sep))
    elif isinstance(data, list):
        list_paths.append(parent_key)
        for i, value in enumerate(data):
            new_key = f"{parent_key}[{i}]"
            list_paths.extend(find_list_paths(value, new_key, sep))
    return list_paths


def _validate_file_path(
    parent_path: str, relative_file_path: str, parent_dir_type: str
):
    parent_abs = get_expanded_and_absolute_path(parent_path)
    file_path_abs = get_expanded_and_absolute_path(
        os.path.join(parent_abs, relative_file_path)
    )
    # Ensure the file path is actually inside the build context
    outside_context = False
    try:
        # Use os.path.commonpath to check if file_path is inside build_context_abs
        common_path = os.path.commonpath([parent_abs, file_path_abs])
        outside_context = common_path != parent_abs
    except ValueError:
        # os.path.commonpath raises ValueError if paths are on different drives (Windows)
        outside_context = True

    if outside_context:
        raise ValueError(
            f"Referenced file `{relative_file_path}` is outside the {parent_dir_type} `{parent_abs}`. "
            f"It must exist in {parent_dir_type} `{parent_abs}`."
        )

    if not os.path.exists(file_path_abs):
        raise ValueError(
            f"Referenced file `{relative_file_path}` not found. It must exist in {parent_dir_type} `{parent_abs}`."
        )


def validate_dockerfile_build_paths(
    dockerfile_build: DockerFileBuild, project_root_path: str
):
    _validate_file_path(
        parent_path=project_root_path,
        relative_file_path=dockerfile_build.dockerfile_path,
        parent_dir_type="project root",
    )


def validate_python_build_paths(python_build: PythonBuild, build_context_path: str):
    if not python_build.python_dependencies:
        # Old style flat requirements file
        if python_build.requirements_path:
            _validate_file_path(
                parent_path=build_context_path,
                relative_file_path=python_build.requirements_path,
                parent_dir_type="build context",
            )
        return

    if (
        isinstance(python_build.python_dependencies, Pip)
        and python_build.python_dependencies.requirements_path
    ):
        _validate_file_path(
            parent_path=build_context_path,
            relative_file_path=python_build.python_dependencies.requirements_path,
            parent_dir_type="build context",
        )
    elif isinstance(python_build.python_dependencies, UV):
        _validate_file_path(
            parent_path=build_context_path,
            relative_file_path="pyproject.toml",
            parent_dir_type="build context",
        )
        _validate_file_path(
            parent_path=build_context_path,
            relative_file_path="uv.lock",
            parent_dir_type="build context",
        )
    elif isinstance(python_build.python_dependencies, Poetry):
        _validate_file_path(
            parent_path=build_context_path,
            relative_file_path="pyproject.toml",
            parent_dir_type="build context",
        )
        _validate_file_path(
            parent_path=build_context_path,
            relative_file_path="poetry.lock",
            parent_dir_type="build context",
        )


def validate_local_source_paths(component_name: str, build: Build):
    source_dir = get_expanded_and_absolute_path(build.build_source.project_root_path)
    if not os.path.exists(source_dir):
        raise ValueError(
            f"Project root path {source_dir!r} of component {component_name!r} does not exist"
        )

    build_context_path = get_expanded_and_absolute_path(
        os.path.join(source_dir, build.build_spec.build_context_path)
    )
    if not os.path.exists(build_context_path):
        raise ValueError(
            f"Build context path {build_context_path!r} "
            f"of component {component_name!r} does not exist"
        )

    if isinstance(build.build_spec, DockerFileBuild):
        validate_dockerfile_build_paths(
            dockerfile_build=build.build_spec, project_root_path=source_dir
        )
    elif isinstance(build.build_spec, PythonBuild):
        validate_python_build_paths(
            python_build=build.build_spec, build_context_path=build_context_path
        )
