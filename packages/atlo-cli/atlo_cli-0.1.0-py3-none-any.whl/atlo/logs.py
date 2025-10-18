"""Log management and viewing for Atlo."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

console = Console()


class LogManager:
    """Manages atlo log directories and files."""

    LOG_BASE_DIR = Path(".atlo/logs")

    @classmethod
    def create_run_dir(cls) -> Path:
        """Create a new log directory for this run.

        Returns:
            Path to the created log directory
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_dir = cls.LOG_BASE_DIR / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    @classmethod
    def get_latest_run(cls) -> Optional[Path]:
        """Get the most recent log directory.

        Returns:
            Path to the latest log directory, or None if none exist
        """
        if not cls.LOG_BASE_DIR.exists():
            return None

        run_dirs = sorted(
            [d for d in cls.LOG_BASE_DIR.iterdir() if d.is_dir()],
            reverse=True,
        )
        return run_dirs[0] if run_dirs else None

    @classmethod
    def list_runs(cls) -> List[Path]:
        """List all available log directories.

        Returns:
            List of log directory paths, sorted by date (newest first)
        """
        if not cls.LOG_BASE_DIR.exists():
            return []

        return sorted(
            [d for d in cls.LOG_BASE_DIR.iterdir() if d.is_dir()],
            reverse=True,
        )

    @classmethod
    def load_manifest(cls, run_dir: Path) -> Optional[dict]:
        """Load the manifest.json from a run directory.

        Args:
            run_dir: Path to the run directory

        Returns:
            Manifest dict, or None if not found
        """
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path) as f:
                return json.load(f)
        except Exception:
            return None

    @classmethod
    def save_manifest(cls, run_dir: Path, manifest_data: dict):
        """Save manifest data to a run directory.

        Args:
            run_dir: Path to the run directory
            manifest_data: Manifest data to save
        """
        manifest_path = run_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest_data, f, indent=2)


class LogViewer:
    """Views and displays log files."""

    def __init__(self, run_dir: Path):
        """Initialize the log viewer.

        Args:
            run_dir: Path to the run directory
        """
        self.run_dir = run_dir
        self.manifest = LogManager.load_manifest(run_dir)

    def view_project(self, project_name: str):
        """Display log for a specific project.

        Args:
            project_name: Name or directory of the project
        """
        if not self.manifest:
            console.print("[red]No manifest found for this run[/red]")
            return

        # Find the project in the manifest
        project_result = None
        for result in self.manifest.get("results", []):
            if (
                result.get("project_name") == project_name
                or result.get("project_dir") == project_name
            ):
                project_result = result
                break

        if not project_result:
            console.print(f"[red]Project '{project_name}' not found in this run[/red]")
            return

        log_path = self.run_dir / project_result.get("log_file", "")
        if not log_path.exists():
            console.print(f"[red]Log file not found: {log_path}[/red]")
            return

        # Read and display the log file
        console.print(f"\n[bold cyan]Project:[/bold cyan] {project_name}")
        console.print(f"[dim]Log: {log_path}[/dim]\n")

        with open(log_path) as f:
            content = f.read()

        # Display with syntax highlighting
        syntax = Syntax(content, "terraform", theme="monokai", line_numbers=True)
        console.print(syntax)

    def view_all(self):
        """Display all logs from the run."""
        if not self.manifest:
            console.print("[red]No manifest found for this run[/red]")
            return

        for result in self.manifest.get("results", []):
            project_name = result.get("project_name", "unknown")
            console.print(f"\n{'=' * 80}")
            console.print(f"[bold cyan]Project:[/bold cyan] {project_name}")
            console.print(f"{'=' * 80}\n")

            log_path = self.run_dir / result.get("log_file", "")
            if log_path.exists():
                with open(log_path) as f:
                    console.print(f.read())
            else:
                console.print("[red]Log file not found[/red]")

    def view_failures(self):
        """Display only logs from failed projects."""
        if not self.manifest:
            console.print("[red]No manifest found for this run[/red]")
            return

        failed_results = [
            r for r in self.manifest.get("results", []) if r.get("status") == "failed"
        ]

        if not failed_results:
            console.print("[green]No failures in this run![/green]")
            return

        for result in failed_results:
            project_name = result.get("project_name", "unknown")
            console.print(f"\n{'=' * 80}")
            console.print(f"[bold red]Failed Project:[/bold red] {project_name}")
            console.print(f"[red]Error:[/red] {result.get('error_message', 'Unknown')}")
            console.print(f"{'=' * 80}\n")

            log_path = self.run_dir / result.get("log_file", "")
            if log_path.exists():
                with open(log_path) as f:
                    console.print(f.read())
            else:
                console.print("[red]Log file not found[/red]")

    def print_summary(self):
        """Print summary table of the run."""
        if not self.manifest:
            console.print("[red]No manifest found for this run[/red]")
            return

        timestamp = self.manifest.get("timestamp", "unknown")
        total_duration = self.manifest.get("total_duration", 0)

        console.print(f"\n[bold]Run:[/bold] {timestamp}")
        console.print(f"[bold]Duration:[/bold] {self._format_duration(total_duration)}\n")

        # Create summary table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Project", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Changes", style="dim")

        for result in self.manifest.get("results", []):
            project_name = result.get("project_name", "unknown")
            status = result.get("status", "unknown")
            duration = self._format_duration(result.get("duration", 0))
            changes = result.get("changes_summary", "-")

            # Format status with emoji
            if status == "success":
                status_str = "[green]✓[/green]"
            elif status == "failed":
                status_str = "[red]✗[/red]"
            else:
                status_str = "[yellow]?[/yellow]"

            table.add_row(project_name, status_str, duration, changes)

        console.print(table)

        # Print summary counts
        results = self.manifest.get("results", [])
        success_count = sum(1 for r in results if r.get("status") == "success")
        failed_count = sum(1 for r in results if r.get("status") == "failed")

        console.print(f"\n[bold]Summary:[/bold] {success_count} successful, {failed_count} failed")

        if failed_count > 0:
            console.print("\nView failures: [cyan]atlo logs --failures[/cyan]")
        console.print("View specific: [cyan]atlo logs <project-name>[/cyan]\n")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "1m 23s")
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
