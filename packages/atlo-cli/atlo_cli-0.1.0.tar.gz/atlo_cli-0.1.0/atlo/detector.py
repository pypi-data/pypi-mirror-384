"""Git change detection and project matching for Atlo."""

import fnmatch
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from atlo.parser import AtlantisConfig


@dataclass
class ProjectMatch:
    """Represents a project matched to changed files."""

    project: Dict
    matched_files: List[str]
    reason: str

    @property
    def name(self) -> str:
        """Get project name."""
        return self.project.get("name", self.project.get("dir", "unknown"))

    @property
    def dir(self) -> str:
        """Get project directory."""
        return self.project.get("dir", "")

    @property
    def workspace(self) -> Optional[str]:
        """Get project workspace."""
        return self.project.get("workspace")

    @property
    def workflow(self) -> str:
        """Get project workflow name."""
        return self.project.get("workflow", "default")


class ChangeDetector:
    """Detects changed files in git repository."""

    @staticmethod
    def detect_base_branch() -> str:
        """Auto-detect the main/master branch.

        Returns:
            Branch name (main or master)
        """
        try:
            # Check if main exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "main"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return "main"

            # Fall back to master
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "master"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return "master"

            # Default to main if neither exists
            return "main"
        except Exception:
            return "main"

    @staticmethod
    def get_changed_files(base_branch: Optional[str] = None) -> List[str]:
        """Get list of changed files compared to base branch.

        Args:
            base_branch: Branch to compare against (default: auto-detect)

        Returns:
            List of changed file paths
        """
        if base_branch is None:
            base_branch = ChangeDetector.detect_base_branch()

        changed_files = []

        try:
            # Get staged and unstaged changes
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                changed_files.extend(result.stdout.strip().split("\n"))

            # Get committed changes compared to base branch
            result = subprocess.run(
                ["git", "diff", "--name-only", base_branch + "...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                changed_files.extend(result.stdout.strip().split("\n"))

            # Remove duplicates and empty strings
            changed_files = list(set(f for f in changed_files if f))

        except subprocess.CalledProcessError:
            # If git diff fails, try getting all modified files
            try:
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                for line in result.stdout.split("\n"):
                    if line:
                        # Extract filename from status line
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            changed_files.append(parts[-1])
            except Exception:
                pass

        return changed_files


class ProjectMatcher:
    """Matches changed files to projects in atlantis.yaml."""

    def __init__(self, atlantis_config: AtlantisConfig):
        """Initialize the project matcher.

        Args:
            atlantis_config: Atlantis configuration
        """
        self.atlantis_config = atlantis_config

    def match_projects(
        self,
        changed_files: List[str],
        all_projects: bool = False,
        filter_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[ProjectMatch]:
        """Match changed files to projects.

        Args:
            changed_files: List of changed file paths
            all_projects: If True, return all projects regardless of changes
            filter_patterns: Only include projects matching these glob patterns
            exclude_patterns: Exclude projects matching these glob patterns

        Returns:
            List of matched projects with reasons
        """
        matches = []

        for project in self.atlantis_config.projects:
            project_dir = project.get("dir", "")
            project_name = project.get("name", project_dir)

            # Apply filters first
            if filter_patterns and not self._matches_any_pattern(
                project_dir, project_name, filter_patterns
            ):
                continue

            # Apply excludes
            if exclude_patterns and self._matches_any_pattern(
                project_dir, project_name, exclude_patterns
            ):
                continue

            if all_projects:
                # Include all projects when --all flag is used
                matches.append(
                    ProjectMatch(
                        project=project,
                        matched_files=[],
                        reason="Included via --all flag",
                    )
                )
                continue

            # Get when_modified patterns from project
            autoplan = project.get("autoplan", {})
            patterns = autoplan.get("when_modified", [])

            # If no patterns defined, use defaults
            if not patterns:
                patterns = ["*.tf", "*.tfvars", "*.tfvars.json", ".terraform.lock.hcl"]

            # Check if any changed files match this project
            matched_files = []
            for changed_file in changed_files:
                if self._file_matches_project(
                    changed_file,
                    project_dir,
                    patterns,
                ):
                    matched_files.append(changed_file)

            if matched_files:
                # Build reason string
                reason = f"Matched {len(matched_files)} file(s)"
                matches.append(
                    ProjectMatch(
                        project=project,
                        matched_files=matched_files,
                        reason=reason,
                    )
                )

        return matches

    def _file_matches_project(
        self,
        file_path: str,
        project_dir: str,
        patterns: List[str],
    ) -> bool:
        """Check if a file matches a project's patterns.

        Args:
            file_path: Path to the changed file
            project_dir: Project directory
            patterns: List of glob patterns from when_modified

        Returns:
            True if file matches any pattern
        """
        file_path_obj = Path(file_path)
        project_dir_obj = Path(project_dir)

        # Check each pattern
        for pattern in patterns:
            # Pattern can be relative to project dir or absolute
            if pattern.startswith("../"):
                # Pattern references parent directories (e.g., ../../../modules/common/*.tf)
                # Resolve relative to project directory
                full_pattern = str(project_dir_obj / pattern)
            elif "/" in pattern:
                # Pattern contains directory separator
                # Check relative to project dir
                full_pattern = str(project_dir_obj / pattern)
            else:
                # Simple glob pattern (e.g., *.tf)
                # Check within project directory
                full_pattern = str(project_dir_obj / pattern)

            # Check if file matches the pattern
            if fnmatch.fnmatch(file_path, full_pattern):
                return True

            # Also check if file is in project dir and matches simple pattern
            if str(file_path_obj).startswith(str(project_dir_obj)):
                # File is in project directory
                relative_path = str(file_path_obj.relative_to(project_dir_obj))
                if fnmatch.fnmatch(relative_path, pattern):
                    return True

        return False

    @staticmethod
    def _matches_any_pattern(project_dir: str, project_name: str, patterns: List[str]) -> bool:
        """Check if project matches any of the given patterns.

        Args:
            project_dir: Project directory path
            project_name: Project name
            patterns: List of glob patterns to match against

        Returns:
            True if project matches any pattern
        """
        for pattern in patterns:
            # Try matching against directory
            if fnmatch.fnmatch(project_dir, pattern):
                return True
            # Try matching against name
            if fnmatch.fnmatch(project_name, pattern):
                return True
            # Try partial directory matches (e.g., "envs/prod/*")
            if "/" in pattern:
                # Split pattern and check if directory starts with it
                pattern_parts = pattern.rstrip("/*").split("/")
                dir_parts = project_dir.split("/")
                if len(dir_parts) >= len(pattern_parts):
                    match = True
                    for i, pattern_part in enumerate(pattern_parts):
                        if pattern_part == "*":
                            continue
                        if i >= len(dir_parts) or not fnmatch.fnmatch(dir_parts[i], pattern_part):
                            match = False
                            break
                    if match:
                        return True
        return False
