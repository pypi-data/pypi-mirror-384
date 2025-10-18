"""Diff viewing for comparing atlo runs."""

from typing import Any, Dict

from rich.console import Console
from rich.table import Table

console = Console()


class RunDiff:
    """Compares two atlo runs."""

    def __init__(self, run1_manifest: Dict[str, Any], run2_manifest: Dict[str, Any]):
        """Initialize the diff viewer.

        Args:
            run1_manifest: First run manifest
            run2_manifest: Second run manifest
        """
        self.run1 = run1_manifest
        self.run2 = run2_manifest

    def print_diff(self) -> None:
        """Print comprehensive diff between two runs."""
        console.print("\n[bold cyan]Comparing Runs[/bold cyan]\n")

        # Header info
        console.print(f"[dim]Run 1:[/dim] {self.run1['timestamp']}")
        console.print(f"[dim]Run 2:[/dim] {self.run2['timestamp']}")
        console.print()

        # Compare overall stats
        self._print_stats_comparison()

        # Compare individual projects
        self._print_project_comparison()

        # Show new/removed projects
        self._print_project_changes()

    def _print_stats_comparison(self) -> None:
        """Print comparison of overall statistics."""
        console.print("[bold]Overall Statistics[/bold]\n")

        # Calculate stats for both runs
        run1_stats = self._calculate_stats(self.run1)
        run2_stats = self._calculate_stats(self.run2)

        # Create comparison table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Metric", style="cyan")
        table.add_column("Run 1", justify="right")
        table.add_column("Run 2", justify="right")
        table.add_column("Change", justify="right")

        # Success count
        success_diff = run2_stats["success"] - run1_stats["success"]
        success_color = "green" if success_diff > 0 else "red" if success_diff < 0 else "dim"
        success_change = f"[{success_color}]{success_diff:+d}[/{success_color}]"
        table.add_row(
            "Successful",
            str(run1_stats["success"]),
            str(run2_stats["success"]),
            success_change,
        )

        # Failed count
        failed_diff = run2_stats["failed"] - run1_stats["failed"]
        failed_color = "red" if failed_diff > 0 else "green" if failed_diff < 0 else "dim"
        failed_change = f"[{failed_color}]{failed_diff:+d}[/{failed_color}]"
        table.add_row(
            "Failed",
            str(run1_stats["failed"]),
            str(run2_stats["failed"]),
            failed_change,
        )

        # Total changes
        adds_diff = run2_stats["adds"] - run1_stats["adds"]
        adds_color = "yellow" if adds_diff != 0 else "dim"
        table.add_row(
            "Resources to Add",
            str(run1_stats["adds"]),
            str(run2_stats["adds"]),
            f"[{adds_color}]{adds_diff:+d}[/{adds_color}]",
        )

        changes_diff = run2_stats["changes"] - run1_stats["changes"]
        changes_color = "yellow" if changes_diff != 0 else "dim"
        table.add_row(
            "Resources to Change",
            str(run1_stats["changes"]),
            str(run2_stats["changes"]),
            f"[{changes_color}]{changes_diff:+d}[/{changes_color}]",
        )

        destroys_diff = run2_stats["destroys"] - run1_stats["destroys"]
        destroys_color = "red" if destroys_diff > 0 else "green" if destroys_diff < 0 else "dim"
        table.add_row(
            "Resources to Destroy",
            str(run1_stats["destroys"]),
            str(run2_stats["destroys"]),
            f"[{destroys_color}]{destroys_diff:+d}[/{destroys_color}]",
        )

        # Duration
        duration_diff = run2_stats["duration"] - run1_stats["duration"]
        duration_color = "green" if duration_diff < 0 else "red" if duration_diff > 0 else "dim"
        table.add_row(
            "Duration (s)",
            f"{run1_stats['duration']:.1f}",
            f"{run2_stats['duration']:.1f}",
            f"[{duration_color}]{duration_diff:+.1f}[/{duration_color}]",
        )

        console.print(table)
        console.print()

    def _print_project_comparison(self) -> None:
        """Print comparison of individual projects."""
        console.print("[bold]Project-by-Project Comparison[/bold]\n")

        # Build lookup dicts
        run1_projects = {r["project_name"]: r for r in self.run1["results"]}
        run2_projects = {r["project_name"]: r for r in self.run2["results"]}

        # Find common projects
        common_projects = set(run1_projects.keys()) & set(run2_projects.keys())

        if not common_projects:
            console.print("[yellow]No common projects between runs[/yellow]\n")
            return

        # Create comparison table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Project", style="cyan")
        table.add_column("Status Change")
        table.add_column("Changes (Run 1)", justify="right")
        table.add_column("Changes (Run 2)", justify="right")
        table.add_column("Duration Δ", justify="right")

        for project_name in sorted(common_projects):
            r1 = run1_projects[project_name]
            r2 = run2_projects[project_name]

            # Status change
            status1 = r1["status"]
            status2 = r2["status"]
            if status1 == status2:
                status_str = "→" if status1 == "success" else "[red]→[/red]"
            elif status2 == "success":
                status_str = "[green]Fixed[/green]"
            else:
                status_str = "[red]Broke[/red]"

            # Changes
            changes1 = r1.get("changes_summary") or "-"
            changes2 = r2.get("changes_summary") or "-"

            # Duration diff
            duration_diff = r2["duration"] - r1["duration"]
            duration_color = (
                "green" if duration_diff < -0.5 else "red" if duration_diff > 0.5 else "dim"
            )
            duration_str = f"[{duration_color}]{duration_diff:+.1f}s[/{duration_color}]"

            table.add_row(project_name, status_str, changes1, changes2, duration_str)

        console.print(table)
        console.print()

    def _print_project_changes(self) -> None:
        """Print projects that were added or removed."""
        run1_projects = {r["project_name"] for r in self.run1["results"]}
        run2_projects = {r["project_name"] for r in self.run2["results"]}

        new_projects = run2_projects - run1_projects
        removed_projects = run1_projects - run2_projects

        if new_projects or removed_projects:
            console.print("[bold]Project Set Changes[/bold]\n")

            if new_projects:
                console.print(f"[green]+ New projects ({len(new_projects)}):[/green]")
                for project in sorted(new_projects):
                    console.print(f"  [dim]• {project}[/dim]")
                console.print()

            if removed_projects:
                console.print(f"[red]- Removed projects ({len(removed_projects)}):[/red]")
                for project in sorted(removed_projects):
                    console.print(f"  [dim]• {project}[/dim]")
                console.print()

    @staticmethod
    def _calculate_stats(manifest: Dict[str, Any]) -> Dict[str, int]:
        """Calculate statistics for a manifest.

        Args:
            manifest: Run manifest

        Returns:
            Dict with calculated stats
        """
        results = manifest["results"]

        return {
            "success": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "adds": sum(r.get("adds", 0) or 0 for r in results),
            "changes": sum(r.get("changes", 0) or 0 for r in results),
            "destroys": sum(r.get("destroys", 0) or 0 for r in results),
            "duration": manifest["total_duration"],
        }
