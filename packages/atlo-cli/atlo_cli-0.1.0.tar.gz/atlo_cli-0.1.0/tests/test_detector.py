"""Tests for git change detection and project matching."""

import pytest

from atlo.detector import ChangeDetector, ProjectMatch, ProjectMatcher
from atlo.parser import AtlantisConfig


@pytest.fixture
def sample_atlantis_config():
    """Sample atlantis.yaml with multiple projects."""
    config_data = {
        "version": 3,
        "projects": [
            {
                "name": "api-prod",
                "dir": "envs/prod/api",
                "workspace": "prod",
                "workflow": "default",
            },
            {
                "name": "api-staging",
                "dir": "envs/staging/api",
                "workspace": "staging",
                "workflow": "default",
            },
            {
                "name": "core-prod",
                "dir": "envs/prod/core",
                "workspace": "prod",
                "workflow": "default",
            },
            {
                "name": "test-api",
                "dir": "envs/test/api",
                "workspace": "test",
                "workflow": "default",
            },
        ],
        "workflows": {
            "default": {
                "plan": {"steps": ["init", "plan"]},
            }
        },
    }
    return AtlantisConfig(config_data)


class TestProjectMatch:
    """Tests for ProjectMatch dataclass."""

    def test_project_match_name(self):
        """Test extracting project name."""
        project = {"name": "test-project", "dir": "terraform/test"}
        match = ProjectMatch(project=project, matched_files=[], reason="test")
        assert match.name == "test-project"

    def test_project_match_name_fallback(self):
        """Test name fallback to dir when name missing."""
        project = {"dir": "terraform/test"}
        match = ProjectMatch(project=project, matched_files=[], reason="test")
        assert match.name == "terraform/test"

    def test_project_match_dir(self):
        """Test extracting project directory."""
        project = {"dir": "terraform/api"}
        match = ProjectMatch(project=project, matched_files=[], reason="test")
        assert match.dir == "terraform/api"

    def test_project_match_workspace(self):
        """Test extracting workspace."""
        project = {"workspace": "prod"}
        match = ProjectMatch(project=project, matched_files=[], reason="test")
        assert match.workspace == "prod"

    def test_project_match_workspace_none(self):
        """Test workspace when not specified."""
        project = {"dir": "terraform/api"}
        match = ProjectMatch(project=project, matched_files=[], reason="test")
        assert match.workspace is None

    def test_project_match_workflow(self):
        """Test extracting workflow name."""
        project = {"workflow": "custom"}
        match = ProjectMatch(project=project, matched_files=[], reason="test")
        assert match.workflow == "custom"

    def test_project_match_workflow_default(self):
        """Test workflow defaults to 'default'."""
        project = {"dir": "terraform/api"}
        match = ProjectMatch(project=project, matched_files=[], reason="test")
        assert match.workflow == "default"


class TestChangeDetector:
    """Tests for ChangeDetector."""

    def test_detect_base_branch(self):
        """Test base branch detection."""
        branch = ChangeDetector.detect_base_branch()
        assert branch in ["main", "master"]

    def test_get_changed_files_returns_list(self):
        """Test that get_changed_files returns a list."""
        files = ChangeDetector.get_changed_files()
        assert isinstance(files, list)


class TestProjectMatcher:
    """Tests for ProjectMatcher."""

    def test_match_all_projects(self, sample_atlantis_config):
        """Test matching all projects with --all flag."""
        matcher = ProjectMatcher(sample_atlantis_config)
        matches = matcher.match_projects(changed_files=[], all_projects=True)

        assert len(matches) == 4
        assert all(m.reason == "Included via --all flag" for m in matches)

    def test_match_changed_files(self, sample_atlantis_config):
        """Test matching projects by changed files."""
        matcher = ProjectMatcher(sample_atlantis_config)
        changed_files = ["envs/prod/api/main.tf", "envs/staging/api/variables.tf"]

        matches = matcher.match_projects(changed_files=changed_files)

        # Should match api-prod and api-staging
        assert len(matches) == 2
        matched_names = {m.name for m in matches}
        assert "api-prod" in matched_names
        assert "api-staging" in matched_names

    def test_filter_by_pattern(self, sample_atlantis_config):
        """Test filtering projects by glob pattern."""
        matcher = ProjectMatcher(sample_atlantis_config)

        # Filter to only prod projects
        matches = matcher.match_projects(
            changed_files=[],
            all_projects=True,
            filter_patterns=["envs/prod/*"],
        )

        assert len(matches) == 2
        matched_names = {m.name for m in matches}
        assert "api-prod" in matched_names
        assert "core-prod" in matched_names

    def test_filter_multiple_patterns(self, sample_atlantis_config):
        """Test filtering with multiple patterns."""
        matcher = ProjectMatcher(sample_atlantis_config)

        # Filter to prod and staging
        matches = matcher.match_projects(
            changed_files=[],
            all_projects=True,
            filter_patterns=["envs/prod/*", "envs/staging/*"],
        )

        assert len(matches) == 3
        matched_names = {m.name for m in matches}
        assert "api-prod" in matched_names
        assert "api-staging" in matched_names
        assert "core-prod" in matched_names

    def test_exclude_pattern(self, sample_atlantis_config):
        """Test excluding projects by pattern."""
        matcher = ProjectMatcher(sample_atlantis_config)

        # Get all except test
        matches = matcher.match_projects(
            changed_files=[],
            all_projects=True,
            exclude_patterns=["envs/test/*"],
        )

        assert len(matches) == 3
        matched_names = {m.name for m in matches}
        assert "test-api" not in matched_names

    def test_filter_and_exclude(self, sample_atlantis_config):
        """Test combining filter and exclude patterns."""
        matcher = ProjectMatcher(sample_atlantis_config)

        # Get all *api* projects except test
        matches = matcher.match_projects(
            changed_files=[],
            all_projects=True,
            filter_patterns=["*/api"],
            exclude_patterns=["envs/test/*"],
        )

        assert len(matches) == 2
        matched_names = {m.name for m in matches}
        assert "api-prod" in matched_names
        assert "api-staging" in matched_names
        assert "test-api" not in matched_names

    def test_filter_by_name_pattern(self, sample_atlantis_config):
        """Test filtering by project name pattern."""
        matcher = ProjectMatcher(sample_atlantis_config)

        # Filter by name containing "core"
        matches = matcher.match_projects(
            changed_files=[],
            all_projects=True,
            filter_patterns=["*core*"],
        )

        assert len(matches) == 1
        assert matches[0].name == "core-prod"

    def test_no_matches(self, sample_atlantis_config):
        """Test when no projects match filters."""
        matcher = ProjectMatcher(sample_atlantis_config)

        matches = matcher.match_projects(
            changed_files=[],
            all_projects=True,
            filter_patterns=["nonexistent/*"],
        )

        assert len(matches) == 0

    def test_file_matches_project_simple(self, sample_atlantis_config):
        """Test file matching for simple terraform files."""
        matcher = ProjectMatcher(sample_atlantis_config)

        # Test that .tf files match
        assert matcher._file_matches_project(
            "envs/prod/api/main.tf",
            "envs/prod/api",
            ["*.tf"],
        )

    def test_file_matches_project_subdirectory(self, sample_atlantis_config):
        """Test file matching in subdirectories."""
        matcher = ProjectMatcher(sample_atlantis_config)

        # Test nested files
        assert matcher._file_matches_project(
            "envs/prod/api/modules/vpc/main.tf",
            "envs/prod/api",
            ["**/*.tf"],
        )

    def test_matches_any_pattern_simple(self):
        """Test pattern matching against directory."""
        assert ProjectMatcher._matches_any_pattern(
            "envs/prod/api",
            "api-prod",
            ["envs/prod/*"],
        )

    def test_matches_any_pattern_wildcard(self):
        """Test pattern with wildcard in middle."""
        assert ProjectMatcher._matches_any_pattern(
            "envs/prod/api",
            "api-prod",
            ["envs/*/api"],
        )

    def test_matches_any_pattern_name(self):
        """Test pattern matching against project name."""
        assert ProjectMatcher._matches_any_pattern(
            "envs/prod/api",
            "api-prod",
            ["*prod*"],
        )

    def test_matches_any_pattern_no_match(self):
        """Test pattern that doesn't match."""
        assert not ProjectMatcher._matches_any_pattern(
            "envs/prod/api",
            "api-prod",
            ["envs/staging/*"],
        )
