"""Multi-project runner with Rich output for Atlo."""

import concurrent.futures
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table

from atlo.detector import ProjectMatch
from atlo.progress import ProgressEstimator
from atlo.workflow import WorkflowRunner

console = Console()


@dataclass
class ProjectResult:
    """Result of running a project."""

    project_name: str
    project_dir: str
    status: str  # "success", "failed", "running", "pending"
    duration: float
    log_file: str
    error_message: Optional[str] = None
    changes_summary: Optional[str] = None
    # Structured change data
    adds: Optional[int] = None
    changes: Optional[int] = None
    destroys: Optional[int] = None


class MultiProjectRunner:
    """Runs multiple projects and displays progress."""

    def __init__(
        self,
        workflow_runner: WorkflowRunner,
        project_matches: List[ProjectMatch],
        log_dir: Path,
        workflow_name: str = "default",
        max_workers: int = 1,
    ):
        """Initialize the multi-project runner.

        Args:
            workflow_runner: Configured WorkflowRunner instance
            project_matches: List of projects to run
            log_dir: Directory to save logs
            workflow_name: Name of the workflow to run
            max_workers: Maximum number of parallel workers
        """
        self.workflow_runner = workflow_runner
        self.project_matches = project_matches
        self.log_dir = log_dir
        self.workflow_name = workflow_name
        self.max_workers = max_workers
        self.results: List[ProjectResult] = []
        self.table_lock = threading.Lock()  # For thread-safe table updates
        self.estimator = ProgressEstimator()
        self.start_time = 0.0

    def run_all(self, verbose: bool = False) -> dict:
        """Run all projects and display progress.

        Args:
            verbose: If True, show full output inline instead of table

        Returns:
            Manifest dict with all results
        """
        if verbose:
            return self._run_verbose()
        else:
            return self._run_with_table()

    def _run_verbose(self) -> dict:
        """Run all projects with full output displayed inline."""
        start_time = time.time()

        console.print(f"\n[bold cyan]Running {len(self.project_matches)} project(s)[/bold cyan]\n")

        for i, project_match in enumerate(self.project_matches, 1):
            console.print(
                f"[bold]Project {i}/{len(self.project_matches)}:[/bold] " f"{project_match.name}"
            )
            console.print(f"[dim]Directory: {project_match.dir}[/dim]")
            if project_match.workspace:
                console.print(f"[dim]Workspace: {project_match.workspace}[/dim]")
            console.print()

            result = self._run_project(project_match, show_output=True)
            self.results.append(result)

            if result.status == "failed":
                console.print(f"\n[red]✗ Failed: {result.error_message}[/red]\n")
            else:
                console.print("\n[green]✓ Success[/green]\n")

        total_duration = time.time() - start_time
        return self._build_manifest(total_duration)

    def _run_with_table(self) -> dict:
        """Run all projects with live progress table."""
        self.start_time = time.time()

        parallel_mode = self.max_workers > 1
        worker_info = f" ({self.max_workers} parallel)" if parallel_mode else ""
        console.print(
            f"\n[bold cyan]Running {len(self.project_matches)} project(s){worker_info}[/bold cyan]"
        )
        console.print(f"[dim]Logs: {self.log_dir}[/dim]")

        # Show initial ETA if we have historical data
        project_names = [pm.name for pm in self.project_matches]
        estimated_total, projects_with_data = self.estimator.estimate_total(project_names)
        if projects_with_data > 0:
            console.print(
                f"[dim]Estimated time: ~{self._format_duration(estimated_total)} "
                f"(based on {projects_with_data}/{len(project_names)} projects)[/dim]"
            )
        console.print()

        # Initialize results
        self.results = [
            ProjectResult(
                project_name=pm.name,
                project_dir=pm.dir,
                status="pending",
                duration=0.0,
                log_file=self._get_log_filename(pm),
            )
            for pm in self.project_matches
        ]

        if parallel_mode:
            # Run projects in parallel
            with Live(self._generate_table(), refresh_per_second=4) as live:
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=self.max_workers
                ) as executor:
                    # Submit all projects
                    future_to_idx = {
                        executor.submit(self._run_project_timed, idx, pm): idx
                        for idx, pm in enumerate(self.project_matches)
                    }

                    # Process as they complete
                    for future in concurrent.futures.as_completed(future_to_idx):
                        idx = future_to_idx[future]
                        try:
                            result = future.result()
                            with self.table_lock:
                                self.results[idx] = result
                                live.update(self._generate_table())
                        except Exception as e:
                            # Handle unexpected errors
                            with self.table_lock:
                                self.results[idx].status = "failed"
                                self.results[idx].error_message = str(e)
                                live.update(self._generate_table())
        else:
            # Sequential execution (original behavior)
            with Live(self._generate_table(), refresh_per_second=4) as live:
                for idx, project_match in enumerate(self.project_matches):
                    # Update status to running
                    self.results[idx].status = "running"
                    live.update(self._generate_table())

                    # Run the project
                    result = self._run_project_timed(idx, project_match)

                    # Update result
                    self.results[idx] = result
                    live.update(self._generate_table())

        total_duration = time.time() - self.start_time

        # Print final summary
        self._print_summary(total_duration)

        return self._build_manifest(total_duration)

    def _run_project_timed(self, idx: int, project_match: ProjectMatch) -> ProjectResult:
        """Run a project and track timing.

        Args:
            idx: Index in results list
            project_match: Project to run

        Returns:
            ProjectResult with outcome
        """
        # Mark as running
        with self.table_lock:
            self.results[idx].status = "running"

        project_start = time.time()
        result = self._run_project(project_match, show_output=False)
        result.duration = time.time() - project_start
        return result

    def _run_project(
        self,
        project_match: ProjectMatch,
        show_output: bool = False,
    ) -> ProjectResult:
        """Run a single project.

        Args:
            project_match: Project to run
            show_output: If True, display output to console

        Returns:
            ProjectResult with outcome
        """
        log_filename = self._get_log_filename(project_match)
        log_path = self.log_dir / log_filename

        try:
            # Run the workflow with log file
            success, output = self.workflow_runner.run_plan(
                directory=project_match.dir,
                workspace=project_match.workspace,
                workflow_name=project_match.workflow,
                log_file=log_path if not show_output else None,
            )

            # Determine status
            status = "success" if success else "failed"
            error_message = None if success else "Plan failed"

            # Parse changes from output
            changes_summary, adds, changes, destroys = self._parse_changes(output)

        except Exception as e:
            status = "failed"
            error_message = str(e)
            changes_summary = None
            adds = None
            changes = None
            destroys = None

        return ProjectResult(
            project_name=project_match.name,
            project_dir=project_match.dir,
            status=status,
            duration=0.0,  # Will be set by caller
            log_file=log_filename,
            error_message=error_message,
            changes_summary=changes_summary,
            adds=adds,
            changes=changes,
            destroys=destroys,
        )

    def _generate_table(self) -> Table:
        """Generate the progress table.

        Returns:
            Rich Table with current status
        """
        # Calculate ETA
        completed_count = sum(1 for r in self.results if r.status in ("success", "failed"))
        remaining_count = len(self.results) - completed_count

        eta_str = ""
        if remaining_count > 0 and completed_count > 0:
            elapsed = time.time() - self.start_time
            avg_per_project = elapsed / completed_count
            estimated_remaining = avg_per_project * remaining_count
            eta_str = f" • ETA: {self._format_duration(estimated_remaining)}"

        table = Table(
            show_header=True,
            header_style="bold cyan",
            title=f"Progress: {completed_count}/{len(self.results)}{eta_str}",
            title_style="dim",
        )
        table.add_column("Project", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Duration", justify="right")
        table.add_column("Changes", style="dim")

        for result in self.results:
            # Format status
            if result.status == "success":
                status_str = "[green]✓ Done[/green]"
            elif result.status == "failed":
                status_str = "[red]✗ Failed[/red]"
            elif result.status == "running":
                status_str = "[yellow]⠋ Running[/yellow]"
            else:
                status_str = "[dim]Pending[/dim]"

            # Format duration
            if result.duration > 0:
                duration_str = f"{result.duration:.1f}s"
            else:
                duration_str = "-"

            # Format changes
            changes_str = result.changes_summary or "-"

            table.add_row(
                result.project_name,
                status_str,
                duration_str,
                changes_str,
            )

        return table

    def _print_summary(self, total_duration: float):
        """Print final summary.

        Args:
            total_duration: Total time taken
        """
        success_count = sum(1 for r in self.results if r.status == "success")
        failed_count = sum(1 for r in self.results if r.status == "failed")

        console.print("\n[bold]Planning Complete[/bold]\n")
        console.print(
            f"Summary: [green]{success_count} successful[/green], "
            f"[red]{failed_count} failed[/red] "
            f"in {self._format_duration(total_duration)}\n"
        )

        # Calculate total changes across all successful projects
        total_adds = sum(r.adds for r in self.results if r.adds is not None)
        total_changes = sum(r.changes for r in self.results if r.changes is not None)
        total_destroys = sum(r.destroys for r in self.results if r.destroys is not None)

        if total_adds or total_changes or total_destroys:
            console.print("[bold]Total Changes:[/bold]")
            parts = []
            if total_adds:
                parts.append(f"[green]{total_adds} to add[/green]")
            if total_changes:
                parts.append(f"[yellow]{total_changes} to change[/yellow]")
            if total_destroys:
                parts.append(f"[red]{total_destroys} to destroy[/red]")
            console.print(f"  {', '.join(parts)}\n")

        if failed_count > 0:
            console.print("[bold]Failed projects:[/bold]")
            for result in self.results:
                if result.status == "failed":
                    console.print(f"  • {result.project_name} - {result.error_message}")
            console.print()

        console.print(f"Logs saved to: [cyan]{self.log_dir}[/cyan]")
        console.print("View logs: [cyan]atlo logs[/cyan]")
        if failed_count > 0:
            console.print("View failures: [cyan]atlo logs --failures[/cyan]")
        console.print()

    def _build_manifest(self, total_duration: float) -> dict:
        """Build manifest dict for saving.

        Args:
            total_duration: Total time taken

        Returns:
            Manifest dict
        """
        from datetime import datetime

        return {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "workflow": self.workflow_name,
            "results": [
                {
                    "project_name": r.project_name,
                    "project_dir": r.project_dir,
                    "status": r.status,
                    "duration": r.duration,
                    "log_file": r.log_file,
                    "error_message": r.error_message,
                    "changes_summary": r.changes_summary,
                    "adds": r.adds,
                    "changes": r.changes,
                    "destroys": r.destroys,
                }
                for r in self.results
            ],
        }

    @staticmethod
    def _get_log_filename(project_match: ProjectMatch) -> str:
        """Generate log filename for a project.

        Args:
            project_match: Project to generate filename for

        Returns:
            Log filename
        """
        # Replace slashes with dashes for filename
        safe_name = project_match.dir.replace("/", "-").replace("\\", "-")
        return f"{safe_name}.log"

    @staticmethod
    def _parse_changes(
        output: str,
    ) -> tuple[Optional[str], Optional[int], Optional[int], Optional[int]]:
        """Parse terraform output to extract changes summary.

        Args:
            output: Terraform output

        Returns:
            Tuple of (summary_string, adds, changes, destroys)
        """
        adds = None
        changes = None
        destroys = None

        # Look for terraform plan output summary
        # Example: "Plan: 3 to add, 2 to change, 1 to destroy"
        pattern = r"Plan: (\d+) to add(?:, (\d+) to change)?(?:, (\d+) to destroy)?"
        match = re.search(pattern, output)
        if match:
            adds = int(match.group(1))
            if match.group(2):
                changes = int(match.group(2))
            if match.group(3):
                destroys = int(match.group(3))

            # Build summary string
            parts = [f"{adds} to add"]
            if changes:
                parts.append(f"{changes} to change")
            if destroys:
                parts.append(f"{destroys} to destroy")
            summary = ", ".join(parts)

            return summary, adds, changes, destroys

        # Check for no changes
        if "No changes" in output or "Your infrastructure matches the configuration" in output:
            return "No changes", 0, 0, 0

        return None, None, None, None

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
