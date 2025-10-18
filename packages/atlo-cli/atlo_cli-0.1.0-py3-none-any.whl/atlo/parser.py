"""Parser for atlantis.yaml configuration files."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


class WorkflowStep:
    """Represents a parsed workflow step."""

    def __init__(self, step_data: Union[str, Dict[str, Any]]):
        """Initialize a workflow step.

        Args:
            step_data: Either a string (simple step) or dict (complex step)
        """
        self.raw_data = step_data

        if isinstance(step_data, str):
            # Simple step: "init", "plan", "apply"
            self.step_type = "builtin"
            self.command = step_data
            self.extra_args = []
            self.run_command = None
        elif isinstance(step_data, dict):
            if "run" in step_data:
                # Custom run step: {run: "echo test"}
                self.step_type = "run"
                self.command = None
                self.extra_args = []
                self.run_command = step_data["run"]
            else:
                # Step with extra_args: {plan: {extra_args: ["-lock=false"]}}
                self.step_type = "builtin"
                # The key is the command name
                self.command = list(step_data.keys())[0]
                step_config = step_data[self.command]
                if isinstance(step_config, dict):
                    self.extra_args = step_config.get("extra_args", [])
                else:
                    self.extra_args = []
                self.run_command = None
        else:
            raise ValueError(f"Invalid step format: {step_data}")

    def is_builtin(self) -> bool:
        """Check if this is a built-in terraform command."""
        return self.step_type == "builtin"

    def is_run(self) -> bool:
        """Check if this is a custom run command."""
        return self.step_type == "run"

    def get_command_name(self) -> str:
        """Get the command name for display purposes."""
        if self.is_run():
            return "run"
        return self.command or "unknown"

    def __repr__(self) -> str:
        """String representation of the step."""
        if self.is_run():
            return f"WorkflowStep(run='{self.run_command}')"
        return f"WorkflowStep(command='{self.command}', extra_args={self.extra_args})"


class AtlantisConfig:
    """Represents an Atlantis configuration."""

    def __init__(self, config_data: Dict[str, Any]):
        """Initialize the Atlantis config.

        Args:
            config_data: Dictionary containing the parsed atlantis.yaml data
        """
        self.raw_config = config_data
        self.version = config_data.get("version", 3)
        self.projects = config_data.get("projects", [])
        self.workflows = config_data.get("workflows", {})

    def get_workflow(self, name: str = "default") -> Optional[Dict[str, Any]]:
        """Get a workflow by name.

        Args:
            name: The workflow name (default: "default")

        Returns:
            The workflow configuration or None if not found
        """
        if name in self.workflows:
            return self.workflows[name]

        # Return a default workflow if none found
        return {"plan": {"steps": ["init", "plan"]}}

    def get_project(
        self, directory: Optional[str] = None, workspace: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Find a project by directory and/or workspace.

        Args:
            directory: Project directory
            workspace: Terraform workspace

        Returns:
            The matching project or None
        """
        for project in self.projects:
            if directory and project.get("dir") != directory:
                continue
            if workspace and project.get("workspace") != workspace:
                continue
            return project
        return None

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects in the configuration.

        Returns:
            List of project configurations
        """
        return self.projects

    def list_workflows(self) -> Dict[str, Any]:
        """List all workflows in the configuration.

        Returns:
            Dictionary of workflow configurations
        """
        return self.workflows

    def get_project_workflow(
        self, directory: Optional[str] = None, workspace: Optional[str] = None
    ) -> str:
        """Get the workflow name for a specific project.

        Args:
            directory: Project directory
            workspace: Terraform workspace

        Returns:
            The workflow name (default: "default")
        """
        project = self.get_project(directory=directory, workspace=workspace)
        if project and "workflow" in project:
            return project["workflow"]
        return "default"

    def parse_workflow_steps(self, workflow_name: str, stage: str = "plan") -> List[WorkflowStep]:
        """Parse workflow steps into WorkflowStep objects.

        Args:
            workflow_name: Name of the workflow
            stage: Stage to get steps for (e.g., "plan", "apply")

        Returns:
            List of WorkflowStep objects
        """
        workflow = self.get_workflow(workflow_name)
        if workflow is None:
            return []

        stage_config = workflow.get(stage, {})
        raw_steps = stage_config.get("steps", [])

        return [WorkflowStep(step_data) for step_data in raw_steps]


def parse_atlantis_yaml(file_path: Path) -> AtlantisConfig:
    """Parse an atlantis.yaml file.

    Args:
        file_path: Path to the atlantis.yaml file

    Returns:
        AtlantisConfig object

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is invalid YAML
    """
    if not file_path.exists():
        raise FileNotFoundError(f"atlantis.yaml not found at {file_path}")

    with open(file_path, "r") as f:
        config_data = yaml.safe_load(f)

    return AtlantisConfig(config_data)


def find_atlantis_yaml(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find atlantis.yaml by walking up the directory tree.

    Args:
        start_dir: Directory to start searching from (default: current directory)

    Returns:
        Path to atlantis.yaml if found, None otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        candidate = parent / "atlantis.yaml"
        if candidate.exists():
            return candidate

    return None
