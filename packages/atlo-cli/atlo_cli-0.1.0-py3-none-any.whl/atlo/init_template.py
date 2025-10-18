"""Configuration template and interactive initialization for Atlo."""

import typer

DEFAULT_CONFIG_TEMPLATE = """# Atlo Configuration
# Created by: atlo init

# Disable Terraform state locking for local runs (default: true)
# Recommended for local sanity checks to avoid lock conflicts
disable_state_lock: true

# Skip init if .terraform/ directory exists (default: true)
# Speeds up repeated runs
skip_init_if_present: true

# Custom terraform binary path (default: terraform)
# Uncomment and modify if you use a different binary (e.g., 'tofu' for OpenTofu)
# terraform_binary: terraform

# Command wrapper - prepends a command before terraform
# Useful for environment injection tools
# Example: command_wrapper: your-env-tool
# command_wrapper:

# Default var file to use for plan/apply
# Uncomment and set if you have a standard var file across projects
# default_var_file: env.auto.tfvars

# Auto-create workspaces if they don't exist (default: true)
workspace_auto_create: true

# Continue workflow even if a step fails (default: false)
continue_on_error: false

# Maximum number of projects to plan in parallel (default: 1)
# Recommended: 4-6 for best performance on modern machines
# Set to 1 for sequential execution (safest)
# Maximum allowed: 10
max_parallel_projects: 1

# Max execution time per step in seconds (optional)
# Uncomment to set a timeout for long-running operations
# step_timeout: 300

# Custom environment variables
# Uncomment and add environment variables to be set during terraform execution
# env:
#   TF_LOG: INFO
#   AWS_PROFILE: dev

# Project-specific overrides
# Uncomment and customize for specific projects
# projects:
#   my-project-dir:
#     var_file: custom.tfvars
#     disable_state_lock: false
"""


def create_interactive_config() -> str:
    """Create configuration through interactive prompts.

    Returns:
        Configuration string with user's choices
    """
    from rich.console import Console

    console = Console()

    console.print("\n[bold cyan]Atlo Configuration Setup[/bold cyan]\n")

    # Disable state lock
    disable_lock = typer.confirm(
        "Disable state locking for local runs? (recommended)",
        default=True,
    )

    # Skip init if present
    skip_init = typer.confirm(
        "Skip init if already initialized?",
        default=True,
    )

    # Terraform binary
    tf_binary = typer.prompt(
        "Terraform binary path",
        default="terraform",
    )

    # Var file
    var_file = typer.prompt(
        "Default var file (leave empty to skip)",
        default="",
    )

    # Auto-create workspaces
    auto_create_ws = typer.confirm(
        "Auto-create workspaces if they don't exist?",
        default=True,
    )

    # Parallel projects
    parallel = typer.prompt(
        "Max parallel projects (1-10, recommended: 4)",
        default="1",
        type=int,
    )
    # Validate
    if parallel > 10:
        parallel = 10
    elif parallel < 1:
        parallel = 1

    # Build config
    config_lines = [
        "# Atlo Configuration",
        "# Created by: atlo init",
        "",
        "# Disable Terraform state locking for local runs",
        f"disable_state_lock: {str(disable_lock).lower()}",
        "",
        "# Skip init if .terraform/ directory exists",
        f"skip_init_if_present: {str(skip_init).lower()}",
        "",
    ]

    if tf_binary != "terraform":
        config_lines.extend(
            [
                "# Custom terraform binary",
                f"terraform_binary: {tf_binary}",
                "",
            ]
        )

    if var_file:
        config_lines.extend(
            [
                "# Default var file to use for plan/apply",
                f"default_var_file: {var_file}",
                "",
            ]
        )

    config_lines.extend(
        [
            "# Auto-create workspaces if they don't exist",
            f"workspace_auto_create: {str(auto_create_ws).lower()}",
            "",
            "# Continue workflow even if a step fails",
            "continue_on_error: false",
            "",
            "# Maximum number of projects to plan in parallel",
            f"max_parallel_projects: {parallel}",
            "",
            "# For additional options, see: https://github.com/jonwsavage/atlo",
        ]
    )

    return "\n".join(config_lines) + "\n"
