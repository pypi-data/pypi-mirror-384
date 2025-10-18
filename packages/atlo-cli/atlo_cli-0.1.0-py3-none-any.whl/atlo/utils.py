"""Utilities for Rich formatting and output."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def print_banner():
    """Print the Atlo banner."""
    banner_text = Text("Atlo — Run Atlantis workflows locally", style="bold cyan")
    console.print(Panel(banner_text, border_style="cyan"))


def print_step(message: str, style: str = "green"):
    """Print a step message with an arrow prefix."""
    console.print(f"→ {message}", style=style)


def print_error(message: str):
    """Print an error message."""
    console.print(f"✗ {message}", style="bold red")


def print_success(message: str):
    """Print a success message."""
    console.print(f"✓ {message}", style="bold green")


def print_info(message: str):
    """Print an info message."""
    console.print(f"i {message}", style="cyan")


def create_workflow_table(workflows: dict) -> Table:
    """Create a Rich table for displaying workflows."""
    table = Table(title="Atlantis Workflows", border_style="cyan")

    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Steps", style="green")

    for name, steps in workflows.items():
        steps_str = " → ".join(steps)
        table.add_row(name, steps_str)

    return table


def create_projects_table(projects: list) -> Table:
    """Create a Rich table for displaying projects."""
    table = Table(title="Atlantis Projects", border_style="cyan")

    table.add_column("Project", style="cyan", no_wrap=True)
    table.add_column("Directory", style="green")
    table.add_column("Workspace", style="yellow")

    for project in projects:
        table.add_row(
            project.get("name", "N/A"),
            project.get("dir", "N/A"),
            project.get("workspace", "default"),
        )

    return table


def print_command_menu(atlantis_yaml_found: bool = False):
    """Print the command menu with available commands.

    Args:
        atlantis_yaml_found: Whether atlantis.yaml was found in the current directory
    """
    # Context indicator
    if atlantis_yaml_found:
        console.print("\n[green]✓[/green] Found atlantis.yaml in current directory\n")
    else:
        console.print("\n[yellow]⚠[/yellow] No atlantis.yaml found in current directory\n")

    # Create commands table
    table = Table(title="Available Commands", border_style="cyan", show_header=True)
    table.add_column("Command", style="cyan bold", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row("atlo init", "Initialize .atlo.yaml configuration")
    table.add_row("atlo plan", "Run Terraform plan workflow (auto-detect or manual)")
    table.add_row("atlo logs", "View logs from previous runs")
    table.add_row("atlo diff", "Compare results between two runs")
    table.add_row("atlo export", "Export results to JSON, JUnit, Markdown, or GitHub")
    table.add_row("atlo list-projects", "List all projects in atlantis.yaml")
    table.add_row("atlo show-workflow", "Display workflow configuration")
    table.add_row("atlo completion", "Show or install shell completion")
    table.add_row("atlo version", "Show version information")

    console.print(table)

    # Quick examples
    console.print("\n[bold cyan]Quick Examples:[/bold cyan]")
    console.print("  [dim]→[/dim] atlo init")
    console.print("  [dim]→[/dim] atlo plan [dim]# Auto-detect changed projects[/dim]")
    console.print(
        "  [dim]→[/dim] atlo plan [green]--dir[/green] terraform/api "
        "[green]--workspace[/green] stage"
    )
    console.print("  [dim]→[/dim] atlo logs [dim]# View last run[/dim]")

    console.print(
        "\n[dim]Run [cyan]atlo --help[/cyan] or [cyan]atlo [command] --help[/cyan] "
        "for more details[/dim]\n"
    )


def check_atlantis_yaml_exists(start_dir: Optional[Path] = None) -> bool:
    """Check if atlantis.yaml exists in current directory or parents.

    Args:
        start_dir: Directory to start searching from (default: current directory)

    Returns:
        True if atlantis.yaml found, False otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        if (parent / "atlantis.yaml").exists():
            return True

    return False
