"""Workflow execution engine."""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from atlo.config import AtloConfig
from atlo.parser import AtlantisConfig, WorkflowStep
from atlo.utils import console, print_error, print_info, print_step, print_success


class WorkflowRunner:
    """Runs Atlantis workflows locally."""

    def __init__(
        self,
        atlantis_config: AtlantisConfig,
        atlo_config: AtloConfig,
        debug: bool = False,
        dry_run: bool = False,
        force_init: bool = False,
    ):
        """Initialize the workflow runner.

        Args:
            atlantis_config: Atlantis configuration
            atlo_config: Atlo configuration with overrides
            debug: Enable debug mode
            dry_run: Don't execute commands, just print them
            force_init: Force terraform init even if already initialized
        """
        self.atlantis_config = atlantis_config
        self.atlo_config = atlo_config
        self.debug = debug
        self.dry_run = dry_run
        self.force_init = force_init
        self.terraform_binary = atlo_config.get_terraform_binary()

    def run_plan(
        self,
        directory: Optional[str] = None,
        workspace: Optional[str] = None,
        workflow_name: str = "default",
        log_file: Optional[Path] = None,
    ) -> tuple[bool, str]:
        """Run the plan workflow.

        Args:
            directory: Project directory
            workspace: Terraform workspace
            workflow_name: Name of the workflow to run

        Returns:
            True if successful, False otherwise
        """
        # Parse workflow steps using the new parser
        workflow_steps = self.atlantis_config.parse_workflow_steps(workflow_name, "plan")

        if not workflow_steps:
            print_error(f"Workflow '{workflow_name}' not found or has no steps")
            return False, ""

        # Dry run mode - just show what would be executed
        if self.dry_run:
            console.print(
                "\n[bold cyan]Dry run mode - showing commands that would be executed:"
                "[/bold cyan]\n"
            )

            for step in workflow_steps:
                if step.is_run():
                    # Custom run command
                    cmd = self._substitute_env_vars(step.run_command, directory, workspace)
                    print_step(cmd)
                else:
                    # Built-in terraform command
                    cmd = self._build_command(step.command, directory, workspace, step.extra_args)
                    print_step(cmd)

            console.print()
            return True, ""

        # Real execution mode
        console.print()

        # Handle workspace if specified
        if workspace and directory:
            if not self._setup_workspace(directory, workspace):
                return False, ""

        # Execute each step
        all_output = []
        for i, step in enumerate(workflow_steps, 1):
            step_name = step.get_command_name()
            console.print(f"[bold cyan]Step {i}/{len(workflow_steps)}:[/bold cyan] {step_name}")

            success, output = self._execute_step(step, directory, workspace, log_file)
            all_output.append(output)

            if not success:
                print_error(f"Step '{step_name}' failed")
                if not self.atlo_config.continue_on_error:
                    return False, "\n".join(all_output)
                console.print(
                    "[yellow]Continuing despite error (continue_on_error=true)[/yellow]\n"
                )

            console.print()

        print_success("Workflow completed successfully")
        return True, "\n".join(all_output)

    def _build_command(
        self,
        step: str,
        directory: Optional[str] = None,
        workspace: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
    ) -> str:
        """Build a terraform command string.

        Args:
            step: Step name (e.g., "init", "plan")
            directory: Project directory
            workspace: Terraform workspace
            extra_args: Additional arguments to pass

        Returns:
            Command string
        """
        if step == "init":
            cmd = f"{self.terraform_binary} init"
        elif step == "plan":
            cmd = f"{self.terraform_binary} plan"
        elif step == "apply":
            cmd = f"{self.terraform_binary} apply"
        else:
            cmd = f"{self.terraform_binary} {step}"

        # Add directory if specified
        if directory:
            cmd += f" -chdir={directory}"

        # Add -lock=false if configured (for init and plan)
        if self.atlo_config.disable_state_lock and step in ["init", "plan"]:
            cmd += " -lock=false"

        # Add var-file if configured (for plan and apply)
        if self.atlo_config.default_var_file and step in ["plan", "apply"]:
            cmd += f" -var-file={self.atlo_config.default_var_file}"

        # Add extra terraform flags from config
        for flag in self.atlo_config.get_extra_terraform_flags():
            cmd += f" {flag}"

        # Add extra args from step definition
        if extra_args:
            for arg in extra_args:
                cmd += f" {arg}"

        return cmd

    def _execute_command(
        self,
        command: str,
        cwd: Optional[Path] = None,
        capture_output: bool = False,
        log_file: Optional[Path] = None,
    ) -> tuple[bool, str]:
        """Execute a shell command with real-time output streaming.

        Args:
            command: Command to execute
            cwd: Working directory
            capture_output: If True, capture output to string
            log_file: If provided, write output to this file

        Returns:
            Tuple of (success: bool, output: str)
        """
        if self.debug:
            console.print(f"[dim]Executing: {command}[/dim]")

        output_lines = []
        log_handle = None

        try:
            # Open log file if provided
            if log_file:
                log_handle = open(log_file, "a")

            # Run command with real-time output
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=self._get_env(),
                bufsize=1,
            )

            # Stream output in real-time
            if process.stdout:
                for line in process.stdout:
                    # Capture for return
                    if capture_output:
                        output_lines.append(line)

                    # Write to log file
                    if log_handle:
                        log_handle.write(line)
                        log_handle.flush()

                    # Print to console (unless we're in quiet mode)
                    if not log_file:  # Only print if not logging to file
                        console.print(line, end="")

            # Wait for process to complete
            return_code = process.wait(timeout=self.atlo_config.step_timeout)

            output = "".join(output_lines) if capture_output else ""

            if return_code == 0:
                return True, output
            else:
                if not log_file:  # Only print error if not already logged
                    print_error(f"Command exited with code {return_code}")
                return False, output

        except subprocess.TimeoutExpired:
            output = "".join(output_lines) if capture_output else ""
            if not log_file:
                print_error(f"Command timed out after {self.atlo_config.step_timeout} seconds")
            process.kill()
            return False, output
        except Exception as e:
            output = "".join(output_lines) if capture_output else ""
            if not log_file:
                print_error(f"Command failed: {str(e)}")
            return False, output
        finally:
            if log_handle:
                log_handle.close()

    def _get_env(self) -> Dict[str, str]:
        """Get environment variables for command execution.

        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()
        env.update(self.atlo_config.get_env_vars())
        return env

    def _substitute_env_vars(
        self,
        command: str,
        directory: Optional[str] = None,
        workspace: Optional[str] = None,
    ) -> str:
        """Substitute Atlantis environment variables in a command.

        Args:
            command: Command string with potential env vars
            directory: Project directory
            workspace: Terraform workspace

        Returns:
            Command with substituted variables
        """
        # Atlantis environment variables
        substitutions = {
            "$WORKSPACE": workspace or "default",
            "$DIR": directory or ".",
            "$PROJECT_NAME": directory or "unknown",
            "$ATLANTIS_TERRAFORM_VERSION": self.terraform_binary,
        }

        result = command
        for var, value in substitutions.items():
            result = result.replace(var, value)

        return result

    def _setup_workspace(self, directory: str, workspace: str) -> bool:
        """Setup terraform workspace (select or create).

        Args:
            directory: Project directory
            workspace: Workspace name

        Returns:
            True if successful, False otherwise
        """
        if not self.atlo_config.workspace_auto_create:
            # Just try to select the workspace
            select_cmd = f"{self.terraform_binary} workspace select {workspace}"
            if directory:
                select_cmd += f" -chdir={directory}"

            if self.debug:
                print_info(f"Selecting workspace: {workspace}")

            return self._execute_command(select_cmd)

        # Try to select first, create if it doesn't exist
        select_cmd = f"{self.terraform_binary} workspace select {workspace}"
        if directory:
            select_cmd += f" -chdir={directory}"

        if self.debug:
            print_info(f"Selecting or creating workspace: {workspace}")

        # Try selecting
        result = subprocess.run(
            select_cmd,
            shell=True,
            capture_output=True,
            text=True,
            env=self._get_env(),
        )

        if result.returncode == 0:
            return True

        # If select failed, try creating
        print_info(f"Workspace '{workspace}' doesn't exist, creating it...")
        create_cmd = f"{self.terraform_binary} workspace new {workspace}"
        if directory:
            create_cmd += f" -chdir={directory}"

        return self._execute_command(create_cmd)

    def _should_skip_init(self, directory: Optional[str]) -> bool:
        """Check if init should be skipped (already initialized).

        Args:
            directory: Project directory

        Returns:
            True if init should be skipped, False otherwise
        """
        # Don't skip if force_init flag is set
        if self.force_init:
            return False

        # Don't skip if config says not to
        if not self.atlo_config.skip_init_if_present:
            return False

        # Check if directory is specified
        if not directory:
            terraform_dir = Path(".terraform")
        else:
            terraform_dir = Path(directory) / ".terraform"

        return terraform_dir.exists()

    def _wrap_command(self, command: str) -> str:
        """Wrap command with custom wrapper if configured.

        Args:
            command: The command to wrap

        Returns:
            Wrapped command if wrapper configured, otherwise original command
        """
        wrapper = self.atlo_config.command_wrapper
        if wrapper:
            return f"{wrapper} {command}"
        return command

    def _execute_step(
        self,
        step: WorkflowStep,
        directory: Optional[str] = None,
        workspace: Optional[str] = None,
        log_file: Optional[Path] = None,
    ) -> tuple[bool, str]:
        """Execute a single workflow step.

        Args:
            step: The workflow step to execute
            directory: Project directory
            workspace: Terraform workspace
            log_file: Optional log file to write output to

        Returns:
            Tuple of (success: bool, output: str)
        """
        if step.is_run():
            # Custom run command
            command = self._substitute_env_vars(step.run_command, directory, workspace)
            command = self._wrap_command(command)
            print_step(command)
            return self._execute_command(command, log_file=log_file, capture_output=True)
        else:
            # Check if we should skip init
            if step.command == "init" and self._should_skip_init(directory):
                print_info(
                    "Terraform already initialized, skipping init " "(use --force-init to override)"
                )
                return True, ""

            # Built-in terraform command
            command = self._build_command(step.command, directory, workspace, step.extra_args)
            command = self._wrap_command(command)
            print_step(command)
            return self._execute_command(command, log_file=log_file, capture_output=True)


def get_workflow_steps(workflow_config: Dict[str, Any], stage: str = "plan") -> List[str]:
    """Extract step names from a workflow configuration.

    Args:
        workflow_config: Workflow configuration dictionary
        stage: Workflow stage (e.g., "plan", "apply")

    Returns:
        List of step names
    """
    stage_config = workflow_config.get(stage, {})
    steps = stage_config.get("steps", [])

    step_names = []
    for step in steps:
        if isinstance(step, str):
            step_names.append(step)
        elif isinstance(step, dict):
            step_names.append(step.get("name", "custom"))

    return step_names
