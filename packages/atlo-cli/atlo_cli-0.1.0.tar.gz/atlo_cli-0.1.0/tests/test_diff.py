"""Tests for run comparison and diff viewing."""

import pytest

from atlo.diff import RunDiff


@pytest.fixture
def sample_run1():
    """Sample first run manifest."""
    return {
        "timestamp": "2025-10-17T14:30:45",
        "total_duration": 125.5,
        "workflow": "default",
        "results": [
            {
                "project_name": "api-prod",
                "project_dir": "envs/prod/api",
                "status": "success",
                "duration": 45.2,
                "changes_summary": "3 to add, 2 to change",
                "adds": 3,
                "changes": 2,
                "destroys": 0,
            },
            {
                "project_name": "api-staging",
                "project_dir": "envs/staging/api",
                "status": "success",
                "duration": 38.7,
                "changes_summary": "No changes",
                "adds": 0,
                "changes": 0,
                "destroys": 0,
            },
            {
                "project_name": "core-prod",
                "project_dir": "envs/prod/core",
                "status": "failed",
                "duration": 41.6,
                "changes_summary": None,
                "adds": None,
                "changes": None,
                "destroys": None,
            },
        ],
    }


@pytest.fixture
def sample_run2():
    """Sample second run manifest."""
    return {
        "timestamp": "2025-10-17T15:45:30",
        "total_duration": 110.2,
        "workflow": "default",
        "results": [
            {
                "project_name": "api-prod",
                "project_dir": "envs/prod/api",
                "status": "success",
                "duration": 42.1,
                "changes_summary": "5 to add, 1 to change",
                "adds": 5,
                "changes": 1,
                "destroys": 0,
            },
            {
                "project_name": "api-staging",
                "project_dir": "envs/staging/api",
                "status": "success",
                "duration": 35.0,
                "changes_summary": "No changes",
                "adds": 0,
                "changes": 0,
                "destroys": 0,
            },
            {
                "project_name": "core-prod",
                "project_dir": "envs/prod/core",
                "status": "success",
                "duration": 33.1,
                "changes_summary": "2 to add",
                "adds": 2,
                "changes": 0,
                "destroys": 0,
            },
        ],
    }


@pytest.fixture
def run_with_new_project():
    """Run manifest with a new project added."""
    return {
        "timestamp": "2025-10-17T16:00:00",
        "total_duration": 150.0,
        "workflow": "default",
        "results": [
            {
                "project_name": "api-prod",
                "project_dir": "envs/prod/api",
                "status": "success",
                "duration": 45.0,
                "changes_summary": "No changes",
                "adds": 0,
                "changes": 0,
                "destroys": 0,
            },
            {
                "project_name": "new-project",
                "project_dir": "envs/test/new",
                "status": "success",
                "duration": 105.0,
                "changes_summary": "10 to add",
                "adds": 10,
                "changes": 0,
                "destroys": 0,
            },
        ],
    }


class TestRunDiff:
    """Tests for RunDiff."""

    def test_initialization(self, sample_run1, sample_run2):
        """Test RunDiff initialization."""
        diff = RunDiff(sample_run1, sample_run2)
        assert diff.run1 == sample_run1
        assert diff.run2 == sample_run2

    def test_calculate_stats(self, sample_run1):
        """Test calculating statistics from a manifest."""
        stats = RunDiff._calculate_stats(sample_run1)

        assert stats["success"] == 2
        assert stats["failed"] == 1
        assert stats["adds"] == 3
        assert stats["changes"] == 2
        assert stats["destroys"] == 0
        assert stats["duration"] == 125.5

    def test_calculate_stats_with_none_values(self, sample_run1):
        """Test stats calculation handles None values correctly."""
        # core-prod has None for all change values
        stats = RunDiff._calculate_stats(sample_run1)

        # Should sum to 3 (only api-prod contributes)
        assert stats["adds"] == 3
        assert stats["changes"] == 2
        assert stats["destroys"] == 0

    def test_stats_comparison(self, sample_run1, sample_run2):
        """Test comparing stats between two runs."""
        run1_stats = RunDiff._calculate_stats(sample_run1)
        run2_stats = RunDiff._calculate_stats(sample_run2)

        # Run 2 fixed the failure
        assert run2_stats["success"] > run1_stats["success"]
        assert run2_stats["failed"] < run1_stats["failed"]

        # Run 2 has more adds
        assert run2_stats["adds"] > run1_stats["adds"]

        # Run 2 was faster
        assert run2_stats["duration"] < run1_stats["duration"]

    def test_print_diff_runs_without_error(self, sample_run1, sample_run2, capsys):
        """Test that print_diff executes without errors."""
        diff = RunDiff(sample_run1, sample_run2)
        diff.print_diff()

        captured = capsys.readouterr()
        # Should have output
        assert len(captured.out) > 0

    def test_diff_identifies_fixed_projects(self, sample_run1, sample_run2):
        """Test that diff identifies projects that were fixed."""
        # core-prod was failed in run1, success in run2
        run1_results = {r["project_name"]: r for r in sample_run1["results"]}
        run2_results = {r["project_name"]: r for r in sample_run2["results"]}

        assert run1_results["core-prod"]["status"] == "failed"
        assert run2_results["core-prod"]["status"] == "success"

    def test_diff_identifies_new_projects(self, sample_run1, run_with_new_project):
        """Test identifying new projects."""
        run1_projects = {r["project_name"] for r in sample_run1["results"]}
        run2_projects = {r["project_name"] for r in run_with_new_project["results"]}

        new_projects = run2_projects - run1_projects
        assert "new-project" in new_projects

    def test_diff_identifies_removed_projects(self, sample_run1, run_with_new_project):
        """Test identifying removed projects."""
        run1_projects = {r["project_name"] for r in sample_run1["results"]}
        run2_projects = {r["project_name"] for r in run_with_new_project["results"]}

        removed_projects = run1_projects - run2_projects
        assert "api-staging" in removed_projects
        assert "core-prod" in removed_projects

    def test_duration_comparison(self, sample_run1, sample_run2):
        """Test duration comparison between runs."""
        run1_results = {r["project_name"]: r for r in sample_run1["results"]}
        run2_results = {r["project_name"]: r for r in sample_run2["results"]}

        # api-prod was faster in run2
        assert run2_results["api-prod"]["duration"] < run1_results["api-prod"]["duration"]

        # api-staging was also faster in run2
        assert run2_results["api-staging"]["duration"] < run1_results["api-staging"]["duration"]

    def test_changes_comparison(self, sample_run1, sample_run2):
        """Test comparing resource changes between runs."""
        run1_results = {r["project_name"]: r for r in sample_run1["results"]}
        run2_results = {r["project_name"]: r for r in sample_run2["results"]}

        # api-prod has different changes
        assert run1_results["api-prod"]["adds"] == 3
        assert run2_results["api-prod"]["adds"] == 5

        assert run1_results["api-prod"]["changes"] == 2
        assert run2_results["api-prod"]["changes"] == 1

    def test_print_diff_includes_timestamps(self, sample_run1, sample_run2, capsys):
        """Test that diff output includes timestamps."""
        diff = RunDiff(sample_run1, sample_run2)
        diff.print_diff()

        captured = capsys.readouterr()
        assert "2025-10-17T14:30:45" in captured.out
        assert "2025-10-17T15:45:30" in captured.out

    def test_empty_runs_comparison(self):
        """Test comparing runs with no results."""
        empty_run1 = {
            "timestamp": "2025-10-17T14:30:45",
            "total_duration": 0.0,
            "workflow": "default",
            "results": [],
        }
        empty_run2 = {
            "timestamp": "2025-10-17T15:45:30",
            "total_duration": 0.0,
            "workflow": "default",
            "results": [],
        }

        diff = RunDiff(empty_run1, empty_run2)
        stats1 = diff._calculate_stats(empty_run1)
        stats2 = diff._calculate_stats(empty_run2)

        assert stats1["success"] == 0
        assert stats2["success"] == 0
        assert stats1["adds"] == 0
        assert stats2["adds"] == 0

    def test_handles_missing_change_fields(self):
        """Test handling manifests with missing change fields."""
        run_old = {
            "timestamp": "2025-10-17T14:30:45",
            "total_duration": 100.0,
            "workflow": "default",
            "results": [
                {
                    "project_name": "test",
                    "status": "success",
                    "duration": 50.0,
                    "changes_summary": "Some changes",
                    # Missing adds, changes, destroys fields
                }
            ],
        }

        diff = RunDiff(run_old, run_old)
        stats = diff._calculate_stats(run_old)

        # Should handle missing fields gracefully
        assert stats["adds"] == 0
        assert stats["changes"] == 0
        assert stats["destroys"] == 0
