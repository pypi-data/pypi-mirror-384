"""Progress estimation using historical data."""

import json
from pathlib import Path
from typing import Dict, Optional


class ProgressEstimator:
    """Estimates progress based on historical run data."""

    def __init__(self, history_path: Path = Path(".atlo/logs")):
        """Initialize the progress estimator.

        Args:
            history_path: Path to logs directory
        """
        self.history_path = history_path
        self._historical_data: Dict[str, float] = {}
        self._load_history()

    def _load_history(self) -> None:
        """Load historical timing data from past runs."""
        if not self.history_path.exists():
            return

        # Load data from recent manifests (last 10 runs)
        manifest_files = sorted(
            self.history_path.glob("*/manifest.json"),
            key=lambda p: p.parent.name,
            reverse=True,
        )[:10]

        project_durations: Dict[str, list[float]] = {}

        for manifest_file in manifest_files:
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)

                for result in manifest.get("results", []):
                    project_name = result.get("project_name")
                    duration = result.get("duration")

                    if project_name and duration and result.get("status") == "success":
                        if project_name not in project_durations:
                            project_durations[project_name] = []
                        project_durations[project_name].append(duration)
            except Exception:
                # Skip malformed manifests
                continue

        # Calculate average duration for each project
        for project_name, durations in project_durations.items():
            if durations:
                self._historical_data[project_name] = sum(durations) / len(durations)

    def estimate_duration(self, project_name: str) -> Optional[float]:
        """Estimate duration for a specific project.

        Args:
            project_name: Name of the project

        Returns:
            Estimated duration in seconds, or None if no data
        """
        return self._historical_data.get(project_name)

    def estimate_total(self, project_names: list[str]) -> tuple[float, int]:
        """Estimate total duration for a list of projects.

        Args:
            project_names: List of project names

        Returns:
            Tuple of (estimated_total_seconds, projects_with_data_count)
        """
        total = 0.0
        count = 0

        for project_name in project_names:
            estimate = self.estimate_duration(project_name)
            if estimate is not None:
                total += estimate
                count += 1

        return total, count

    def get_default_estimate(self) -> float:
        """Get a default estimate based on average of all projects.

        Returns:
            Default estimate in seconds
        """
        if not self._historical_data:
            return 30.0  # Default fallback

        return sum(self._historical_data.values()) / len(self._historical_data)
