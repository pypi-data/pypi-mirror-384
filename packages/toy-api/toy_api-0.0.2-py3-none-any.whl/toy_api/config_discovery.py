"""

Config Discovery for Toy API

Handles finding configuration files in project-local directories or package defaults.

License: BSD 3-Clause

"""

#
# IMPORTS
#
import os
import shutil
from pathlib import Path
from typing import Optional


#
# CONSTANTS
#
LOCAL_CONFIG_DIR: str = "toy_api_config"
PACKAGE_CONFIG_DIR: str = "config"
DEFAULT_CONFIG_NAME: str = "v1"


#
# PUBLIC
#
def find_config_path(config_name: Optional[str] = None) -> tuple[str, str]:
    """Find the full path to a configuration file.

    Config discovery priority:
    1. If no config_name provided, use default (toy_api_v1)
    2. Check local project directory: ./toy_api_config/apis/config_name[.yaml]
    3. Check package configs directory: config/apis/config_name[.yaml]
    4. Error if not found

    Supports versioned configs:
    - config_name can be "name/version" (e.g., "versioned_remote/1.2")
    - Looks for toy_api_config/apis/name/version.yaml

    Args:
        config_name: Name of config file (with or without .yaml extension).
                     Can include version like "name/version".

    Returns:
        Tuple of (config_path, status_message).
        config_path is empty string if not found.
        status_message explains where config was found or error.
    """
    # Use default if no config specified
    if config_name is None:
        config_name = DEFAULT_CONFIG_NAME

    # Check if config_name contains version (e.g., "versioned_remote/1.2")
    if '/' in config_name:
        parts = config_name.split('/', 1)
        base_name = parts[0]
        version = parts[1]

        # Check for versioned config in local directory
        versioned_path = _check_versioned_config(base_name, version, LOCAL_CONFIG_DIR)
        if versioned_path:
            return versioned_path, f"Using local versioned config: {versioned_path}"

        # Check for versioned config in package directory
        package_dir = _get_package_config_dir()
        if package_dir:
            versioned_path = _check_versioned_config(base_name, version, str(package_dir))
            if versioned_path:
                return versioned_path, f"Using package versioned config: {versioned_path}"

        return "", f"Versioned config '{config_name}' not found"

    # Normalize config name (ensure .yaml extension)
    config_name = _normalize_config_name(config_name)

    # Priority 1: Check local project directory
    local_path = _check_local_config(config_name)
    if local_path:
        return local_path, f"Using local config: {local_path}"

    # Priority 2: Check package configs directory
    package_path = _check_package_config(config_name)
    if package_path:
        return package_path, f"Using package config: {config_name}"

    # Not found anywhere
    return "", f"Config '{config_name}' not found in {LOCAL_CONFIG_DIR}/apis/ or package configs/apis/"


def get_available_configs() -> dict[str, list[str]]:
    """Get lists of available configuration files.

    Includes both single-file configs and versioned configs (directories).

    Returns:
        Dictionary with 'local' and 'package' keys containing lists of config names.
        Versioned configs are listed as "name/version".
    """
    configs = {"local": [], "package": []}

    # Check local configs
    local_dir = Path(LOCAL_CONFIG_DIR) / "apis"
    if local_dir.exists() and local_dir.is_dir():
        # Single-file configs
        for config_file in local_dir.glob("*.yaml"):
            configs["local"].append(config_file.stem)
        for config_file in local_dir.glob("*.yml"):
            configs["local"].append(config_file.stem)

        # Versioned configs (subdirectories)
        for subdir in local_dir.iterdir():
            if subdir.is_dir():
                for version_file in subdir.glob("*.yaml"):
                    configs["local"].append(f"{subdir.name}/{version_file.stem}")
                for version_file in subdir.glob("*.yml"):
                    configs["local"].append(f"{subdir.name}/{version_file.stem}")

    # Check package configs
    package_dir = _get_package_config_dir()
    if package_dir and package_dir.exists():
        apis_dir = package_dir / "apis"
        if apis_dir.exists() and apis_dir.is_dir():
            # Single-file configs
            for config_file in apis_dir.glob("*.yaml"):
                configs["package"].append(config_file.stem)
            for config_file in apis_dir.glob("*.yml"):
                configs["package"].append(config_file.stem)

            # Versioned configs (subdirectories)
            for subdir in apis_dir.iterdir():
                if subdir.is_dir():
                    for version_file in subdir.glob("*.yaml"):
                        configs["package"].append(f"{subdir.name}/{version_file.stem}")
                    for version_file in subdir.glob("*.yml"):
                        configs["package"].append(f"{subdir.name}/{version_file.stem}")

    return configs


def create_local_config_dir() -> bool:
    """Create local config directory if it doesn't exist.

    Returns:
        True if directory was created or already exists, False on error.
    """
    try:
        Path(LOCAL_CONFIG_DIR).mkdir(exist_ok=True)
        return True
    except Exception:
        return False


def init_config_with_example() -> bool:
    """Initialize local config directory and create example.yaml from v1.yaml.

    This function:
    1. Creates toy_api_config/ directory (exists_ok=True)
    2. Creates toy_api_config/databases/ subdirectory
    3. Creates toy_api_config/apis/ subdirectory
    4. Copies the package's v1.yaml to toy_api_config/apis/example.yaml

    Returns:
        True if successful, False on error.
    """
    try:
        # Step 1: Create the directory
        local_dir = Path(LOCAL_CONFIG_DIR)
        local_dir.mkdir(exist_ok=True)

        # Step 2: Create databases subdirectory
        databases_dir = local_dir / "databases"
        databases_dir.mkdir(exist_ok=True)

        # Step 3: Create apis subdirectory
        apis_dir = local_dir / "apis"
        apis_dir.mkdir(exist_ok=True)

        # Step 4: Copy v1.yaml to apis/example.yaml
        package_dir = _get_package_config_dir()
        if not package_dir:
            return False

        v1_source = package_dir / "apis" / "v1.yaml"
        example_target = apis_dir / "example.yaml"

        if not v1_source.exists():
            return False

        shutil.copy2(v1_source, example_target)
        return True

    except Exception:
        return False


#
# INTERNAL
#
def _check_versioned_config(base_name: str, version: str, base_dir: str) -> Optional[str]:
    """Check if a versioned config exists.

    Args:
        base_name: Base name of the config (e.g., "versioned_remote").
        version: Version string (e.g., "1.2").
        base_dir: Base directory to search in.

    Returns:
        Full path if found, None otherwise.
    """
    # Normalize version to include .yaml extension
    if not version.endswith(('.yaml', '.yml')):
        version = f"{version}.yaml"

    # Check for versioned config: base_dir/apis/base_name/version.yaml
    versioned_path = Path(base_dir) / "apis" / base_name / version
    if versioned_path.exists() and versioned_path.is_file():
        return str(versioned_path)

    # Also try .yml extension if .yaml was requested
    if version.endswith('.yaml'):
        yml_version = version.replace('.yaml', '.yml')
        yml_path = Path(base_dir) / "apis" / base_name / yml_version
        if yml_path.exists() and yml_path.is_file():
            return str(yml_path)

    return None


def _normalize_config_name(config_name: str) -> str:
    """Normalize config name to include .yaml extension.

    Args:
        config_name: Config name with or without extension.

    Returns:
        Config name with .yaml extension.
    """
    if not config_name.endswith(('.yaml', '.yml')):
        return f"{config_name}.yaml"
    return config_name


def _check_local_config(config_name: str) -> Optional[str]:
    """Check if config exists in local project directory.

    Args:
        config_name: Config filename with extension.

    Returns:
        Full path if found, None otherwise.
    """
    local_path = Path(LOCAL_CONFIG_DIR) / "apis" / config_name
    if local_path.exists() and local_path.is_file():
        return str(local_path)

    # Also try .yml extension if .yaml was requested
    if config_name.endswith('.yaml'):
        yml_path = Path(LOCAL_CONFIG_DIR) / "apis" / config_name.replace('.yaml', '.yml')
        if yml_path.exists() and yml_path.is_file():
            return str(yml_path)

    return None


def _check_package_config(config_name: str) -> Optional[str]:
    """Check if config exists in package configs directory.

    Args:
        config_name: Config filename with extension.

    Returns:
        Full path if found, None otherwise.
    """
    package_dir = _get_package_config_dir()
    if not package_dir:
        return None

    package_path = package_dir / "apis" / config_name
    if package_path.exists() and package_path.is_file():
        return str(package_path)

    # Also try .yml extension if .yaml was requested
    if config_name.endswith('.yaml'):
        yml_path = package_dir / "apis" / config_name.replace('.yaml', '.yml')
        if yml_path.exists() and yml_path.is_file():
            return str(yml_path)

    return None


def _get_package_config_dir() -> Optional[Path]:
    """Get path to package configs directory.

    Returns:
        Path to package configs directory, or None if not found.
    """
    try:
        # Get the directory where this module is located
        current_dir = Path(__file__).parent
        # Go up one level to the toy_api package root, then to configs
        package_root = current_dir.parent
        config_dir = package_root / PACKAGE_CONFIG_DIR

        if config_dir.exists() and config_dir.is_dir():
            return config_dir
    except Exception:
        pass

    return None