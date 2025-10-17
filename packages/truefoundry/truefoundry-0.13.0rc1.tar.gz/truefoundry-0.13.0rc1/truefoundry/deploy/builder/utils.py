import os
import shlex
from typing import List, Optional, Set

from truefoundry.common.constants import ENV_VARS
from truefoundry.deploy.builder.constants import (
    BUILDKIT_SECRET_MOUNT_PIP_CONF_ID,
    BUILDKIT_SECRET_MOUNT_POETRY_ENV_ID,
    BUILDKIT_SECRET_MOUNT_UV_CONF_ID,
    BUILDKIT_SECRET_MOUNT_UV_ENV_ID,
    PIP_CONF_BUILDKIT_SECRET_MOUNT,
    PIP_CONF_SECRET_MOUNT_AS_ENV,
    POETRY_ENV_BUILDKIT_SECRET_MOUNT,
    POETRY_ENV_SECRET_MOUNT_AS_ENV,
    UV_CONF_BUILDKIT_SECRET_MOUNT,
    UV_CONF_SECRET_MOUNT_AS_ENV,
    UV_ENV_BUILDKIT_SECRET_MOUNT,
    UV_ENV_SECRET_MOUNT_AS_ENV,
)


def _get_id_from_buildkit_secret_value(value: str) -> Optional[str]:
    parts = value.split(",")
    secret_config = {}
    for part in parts:
        kv = part.split("=", 1)
        if len(kv) != 2:
            continue
        key, value = kv
        secret_config[key] = value

    if "id" in secret_config and "src" in secret_config:
        return secret_config["id"]

    return None


def has_python_package_manager_conf_secret(docker_build_extra_args: List[str]) -> bool:
    args = [arg.strip() for arg in docker_build_extra_args]
    for i, arg in enumerate(args):
        if (
            arg == "--secret"
            and i + 1 < len(args)
            and (
                _get_id_from_buildkit_secret_value(args[i + 1])
                in (
                    BUILDKIT_SECRET_MOUNT_PIP_CONF_ID,
                    BUILDKIT_SECRET_MOUNT_UV_CONF_ID,
                    BUILDKIT_SECRET_MOUNT_UV_ENV_ID,
                    BUILDKIT_SECRET_MOUNT_POETRY_ENV_ID,
                )
            )
        ):
            return True
    return False


def get_available_secrets(docker_build_extra_args: List[str]) -> Set[str]:
    available_secrets = set()
    args = [arg.strip() for arg in docker_build_extra_args]
    for i, arg in enumerate(args):
        if arg == "--secret" and i + 1 < len(args):
            secret_id = _get_id_from_buildkit_secret_value(args[i + 1])
            if secret_id:
                available_secrets.add(secret_id)
    return available_secrets


def generate_secret_mounts(
    available_secrets: Set[str], python_dependencies_type: str, package_manager: str
) -> str:
    mounts = []

    if python_dependencies_type == "pip":
        if (
            package_manager == "pip"
            and BUILDKIT_SECRET_MOUNT_PIP_CONF_ID in available_secrets
        ):
            mounts.append(PIP_CONF_BUILDKIT_SECRET_MOUNT)
        elif (
            package_manager == "uv"
            and BUILDKIT_SECRET_MOUNT_UV_CONF_ID in available_secrets
        ):
            mounts.append(UV_CONF_BUILDKIT_SECRET_MOUNT)
    elif python_dependencies_type == "uv":
        if BUILDKIT_SECRET_MOUNT_UV_CONF_ID in available_secrets:
            mounts.append(UV_CONF_BUILDKIT_SECRET_MOUNT)
        if BUILDKIT_SECRET_MOUNT_UV_ENV_ID in available_secrets:
            mounts.append(UV_ENV_BUILDKIT_SECRET_MOUNT)
    elif python_dependencies_type == "poetry":
        if BUILDKIT_SECRET_MOUNT_POETRY_ENV_ID in available_secrets:
            mounts.append(POETRY_ENV_BUILDKIT_SECRET_MOUNT)

    return " ".join(mounts)


def generate_secret_env_commands(
    available_secrets: Set[str], python_dependencies_type: str, package_manager: str
) -> List[str]:
    env_commands = []

    if python_dependencies_type == "pip":
        if (
            package_manager == "pip"
            and BUILDKIT_SECRET_MOUNT_PIP_CONF_ID in available_secrets
        ):
            env_commands.append(PIP_CONF_SECRET_MOUNT_AS_ENV)
        elif (
            package_manager == "uv"
            and BUILDKIT_SECRET_MOUNT_UV_CONF_ID in available_secrets
        ):
            env_commands.append(UV_CONF_SECRET_MOUNT_AS_ENV)
    elif python_dependencies_type == "uv":
        if BUILDKIT_SECRET_MOUNT_UV_CONF_ID in available_secrets:
            env_commands.append(UV_CONF_SECRET_MOUNT_AS_ENV)
        if BUILDKIT_SECRET_MOUNT_UV_ENV_ID in available_secrets:
            env_commands.append(UV_ENV_SECRET_MOUNT_AS_ENV)
    elif python_dependencies_type == "poetry":
        if BUILDKIT_SECRET_MOUNT_POETRY_ENV_ID in available_secrets:
            env_commands.append(POETRY_ENV_SECRET_MOUNT_AS_ENV)

    return env_commands


def generate_shell_command_with_secrets(
    env_commands: List[str], command: List[str]
) -> str:
    """Generate a shell command that properly handles source commands and environment variables."""
    if not env_commands:
        return shlex.join(command)

    # Separate source commands from env var assignments
    source_commands = [
        cmd for cmd in env_commands if cmd.startswith(". ") or cmd.startswith("source ")
    ]
    env_assignments = [
        cmd
        for cmd in env_commands
        if not cmd.startswith(". ") and not cmd.startswith("source ")
    ]

    if source_commands:
        # If we have source commands, join them with the command
        shell_command_parts = source_commands.copy()

        # Add environment variable assignments and command together
        if env_assignments:
            final_command = shlex.join(env_assignments + command)
        else:
            final_command = shlex.join(command)

        shell_command_parts.append(final_command)
        return " && ".join(shell_command_parts)

    return shlex.join(env_assignments + command)


def generate_pip_install_command(
    requirements_path: Optional[str],
    pip_packages: Optional[List[str]],
    available_secrets: Optional[Set[str]] = None,
) -> Optional[str]:
    command = ["python", "-m", "pip", "install", "--use-pep517", "--no-cache-dir"]
    args = []
    if requirements_path:
        args.append("-r")
        args.append(requirements_path)

    if pip_packages:
        args.extend(pip_packages)

    if not args:
        return None

    secret_env_commands = []
    if available_secrets:
        secret_env_commands = generate_secret_env_commands(
            available_secrets, python_dependencies_type="pip", package_manager="pip"
        )

    final_pip_install_command = generate_shell_command_with_secrets(
        secret_env_commands, command + args
    )

    return final_pip_install_command


def generate_uv_pip_install_command(
    requirements_path: Optional[str],
    pip_packages: Optional[List[str]],
    available_secrets: Optional[Set[str]] = None,
) -> Optional[str]:
    uv_mount = f"--mount=from={ENV_VARS.TFY_PYTHON_BUILD_UV_IMAGE_REPO}:{ENV_VARS.TFY_PYTHON_BUILD_UV_IMAGE_TAG},source=/uv,target=/usr/local/bin/uv"

    envs = [
        "UV_LINK_MODE=copy",
        "UV_PYTHON_DOWNLOADS=never",
        "UV_INDEX_STRATEGY=unsafe-best-match",
    ]

    secret_env_commands = []
    if available_secrets:
        secret_env_commands = generate_secret_env_commands(
            available_secrets, python_dependencies_type="pip", package_manager="uv"
        )

    command = ["uv", "pip", "install", "--no-cache-dir"]

    args = []

    if requirements_path:
        args.append("-r")
        args.append(requirements_path)

    if pip_packages:
        args.extend(pip_packages)

    if not args:
        return None

    uv_pip_install_command = generate_shell_command_with_secrets(
        secret_env_commands, envs + command + args
    )
    final_docker_run_command = " ".join([uv_mount, uv_pip_install_command])

    return final_docker_run_command


def generate_apt_install_command(apt_packages: Optional[List[str]]) -> Optional[str]:
    packages_list = None
    if apt_packages:
        packages_list = " ".join(p.strip() for p in apt_packages if p.strip())
    if not packages_list:
        return None
    apt_update_command = "apt update"
    apt_install_command = f"DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends {packages_list}"
    clear_apt_lists_command = "rm -rf /var/lib/apt/lists/*"
    return " && ".join(
        [apt_update_command, apt_install_command, clear_apt_lists_command]
    )


def generate_command_to_install_from_uv_lock(
    sync_options: Optional[str],
    uv_version: Optional[str],
    install_project: bool = False,
    available_secrets: Optional[Set[str]] = None,
):
    uv_image_uri = f"{ENV_VARS.TFY_PYTHON_BUILD_UV_IMAGE_REPO}:{uv_version if uv_version is not None else ENV_VARS.TFY_PYTHON_BUILD_UV_IMAGE_TAG}"
    uv_mount = f"--mount=from={uv_image_uri},source=/uv,target=/usr/local/bin/uv"

    envs = [
        "UV_LINK_MODE=copy",
        "UV_PYTHON_DOWNLOADS=never",
        "UV_INDEX_STRATEGY=unsafe-best-match",
    ]

    secret_env_commands = []
    if available_secrets:
        secret_env_commands = generate_secret_env_commands(
            available_secrets, python_dependencies_type="uv", package_manager="uv"
        )

    command = ["uv", "sync"]
    sync_options_list = shlex.split(sync_options or "")
    if "--active" not in sync_options_list:
        sync_options_list.append("--active")

    if not install_project and "--no-install-project" not in sync_options_list:
        sync_options_list.append("--no-install-project")

    command.extend(sync_options_list)

    uv_sync_install_command = generate_shell_command_with_secrets(
        secret_env_commands, envs + command
    )
    final_docker_run_command = " ".join([uv_mount, uv_sync_install_command])

    return final_docker_run_command


def generate_poetry_install_command(
    install_options: Optional[str],
    install_project: bool = False,
    available_secrets: Optional[Set[str]] = None,
) -> Optional[str]:
    command = ["poetry", "install"]
    install_options_list = shlex.split(install_options or "")

    if "--no-interaction" not in install_options_list:
        command.append("--no-interaction")

    if not install_project and "--no-root" not in install_options_list:
        command.append("--no-root")

    command.extend(install_options_list)

    secret_env_commands = []
    if available_secrets:
        secret_env_commands = generate_secret_env_commands(
            available_secrets=available_secrets,
            python_dependencies_type="poetry",
            package_manager="poetry",
        )

    poetry_install_cmd = generate_shell_command_with_secrets(
        secret_env_commands, command
    )

    return poetry_install_cmd


def check_whether_poetry_toml_exists(
    build_context_path: str,
) -> bool:
    required_filename = "poetry.toml"
    possible_path = os.path.join(build_context_path, required_filename)

    if os.path.isfile(possible_path):
        return True

    return False
