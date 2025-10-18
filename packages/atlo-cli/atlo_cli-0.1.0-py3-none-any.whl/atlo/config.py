"""Configuration management for .atlo.yaml overrides."""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class AtloConfig:
    """Represents Atlo-specific configuration overrides."""

    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize the Atlo config.

        Args:
            config_data: Dictionary containing the parsed .atlo.yaml data
        """
        self.raw_config = config_data or {}

        # Override settings
        self.terraform_binary = self.raw_config.get("terraform_binary", "terraform")
        self.project_prefix = self.raw_config.get("project_prefix", "")
        self.debug = self.raw_config.get("debug", False)
        self.custom_env = self.raw_config.get("env", {})

        # New configuration options
        self.extra_terraform_flags = self.raw_config.get("extra_terraform_flags", [])
        self.workspace_auto_create = self.raw_config.get("workspace_auto_create", True)
        self.continue_on_error = self.raw_config.get("continue_on_error", False)
        self.step_timeout = self.raw_config.get("step_timeout", None)  # None = no timeout

        # Local-run optimizations
        self.disable_state_lock = self.raw_config.get("disable_state_lock", True)
        self.skip_init_if_present = self.raw_config.get("skip_init_if_present", True)

        # Custom command options
        self.command_wrapper = self.raw_config.get("command_wrapper", None)
        self.default_var_file = self.raw_config.get("default_var_file", None)

        # Parallel execution settings
        max_parallel = self.raw_config.get("max_parallel_projects", 1)
        # Validate and cap at 10
        if max_parallel > 10:
            max_parallel = 10
        elif max_parallel < 1:
            max_parallel = 1
        self.max_parallel_projects = max_parallel

        # Project-specific overrides
        self.project_overrides = self.raw_config.get("projects", {})

    def get_terraform_binary(self) -> str:
        """Get the terraform binary path.

        Returns:
            Path to terraform binary
        """
        return self.terraform_binary

    def get_env_vars(self) -> Dict[str, str]:
        """Get custom environment variables.

        Returns:
            Dictionary of environment variables
        """
        return self.custom_env

    def get_project_config(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """Get project-specific configuration overrides.

        Args:
            project_name: Name of the project

        Returns:
            Project-specific config dict
        """
        if project_name and project_name in self.project_overrides:
            return self.project_overrides[project_name]
        return {}

    def get_extra_terraform_flags(self) -> list:
        """Get extra terraform flags to add to all commands.

        Returns:
            List of extra flags
        """
        return self.extra_terraform_flags


def load_atlo_config(file_path: Optional[Path] = None) -> AtloConfig:
    """Load .atlo.yaml configuration file.

    Args:
        file_path: Path to the .atlo.yaml file (default: search from current dir)

    Returns:
        AtloConfig object with overrides
    """
    if file_path is None:
        file_path = find_atlo_config()

    if file_path is None or not file_path.exists():
        # Return default config if no file found
        return AtloConfig()

    with open(file_path, "r") as f:
        config_data = yaml.safe_load(f) or {}

    return AtloConfig(config_data)


def find_atlo_config(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find .atlo.yaml by walking up the directory tree.

    Args:
        start_dir: Directory to start searching from (default: current directory)

    Returns:
        Path to .atlo.yaml if found, None otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        candidate = parent / ".atlo.yaml"
        if candidate.exists():
            return candidate

    return None


def merge_configs(atlantis_config: Dict[str, Any], atlo_config: AtloConfig) -> Dict[str, Any]:
    """Merge Atlantis and Atlo configurations.

    Args:
        atlantis_config: Base Atlantis configuration
        atlo_config: Atlo-specific overrides

    Returns:
        Merged configuration dictionary
    """
    import copy

    merged = copy.deepcopy(atlantis_config)

    # Note: Environment variables are injected directly by the workflow runner
    # rather than modifying the workflow configuration

    # Apply project-specific overrides
    for project in merged.get("projects", []):
        project_name = project.get("name")
        if project_name:
            project_config = atlo_config.get_project_config(project_name)
            if project_config:
                # Merge project overrides
                project.update(project_config)

    return merged
