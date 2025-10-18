"""Tests for multi-project runner."""

import tempfile
from pathlib import Path

import pytest

from atlo.config import AtloConfig
from atlo.detector import ProjectMatch
from atlo.multi_runner import MultiProjectRunner, ProjectResult
from atlo.parser import AtlantisConfig
from atlo.workflow import WorkflowRunner


@pytest.fixture
def sample_atlantis_config():
    """Sample Atlantis config for testing."""
    config_data = {
        "version": 3,
        "projects": [
            {
                "name": "api-prod",
                "dir": "terraform/api",
                "workspace": "prod",
            },
            {
                "name": "core-stage",
                "dir": "terraform/core",
                "workspace": "stage",
            },
        ],
        "workflows": {
            "default": {
                "plan": {"steps": ["init", "plan"]},
            }
        },
    }
    return AtlantisConfig(config_data)


@pytest.fixture
def sample_workflow_runner(sample_atlantis_config):
    """Create a workflow runner for testing."""
    atlo_config = AtloConfig({"terraform_binary": "terraform"})
    return WorkflowRunner(
        atlantis_config=sample_atlantis_config,
        atlo_config=atlo_config,
        dry_run=True,  # Always dry run in tests
    )


@pytest.fixture
def sample_project_matches():
    """Sample project matches for testing."""
    return [
        ProjectMatch(
            project={
                "name": "api-prod",
                "dir": "terraform/api",
                "workspace": "prod",
                "workflow": "default",
            },
            matched_files=[],
            reason="test",
        ),
        ProjectMatch(
            project={
                "name": "core-stage",
                "dir": "terraform/core",
                "workspace": "stage",
                "workflow": "default",
            },
            matched_files=[],
            reason="test",
        ),
    ]


@pytest.fixture
def temp_log_dir():
    """Create a temporary log directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestProjectResult:
    """Tests for ProjectResult dataclass."""

    def test_project_result_creation(self):
        """Test creating a ProjectResult."""
        result = ProjectResult(
            project_name="test-project",
            project_dir="terraform/test",
            status="success",
            duration=45.5,
            log_file="test.log",
        )

        assert result.project_name == "test-project"
        assert result.project_dir == "terraform/test"
        assert result.status == "success"
        assert result.duration == 45.5
        assert result.log_file == "test.log"
        assert result.error_message is None
        assert result.changes_summary is None

    def test_project_result_with_error(self):
        """Test creating a ProjectResult with error."""
        result = ProjectResult(
            project_name="test-project",
            project_dir="terraform/test",
            status="failed",
            duration=10.0,
            log_file="test.log",
            error_message="Plan failed",
        )

        assert result.status == "failed"
        assert result.error_message == "Plan failed"

    def test_project_result_with_changes(self):
        """Test creating a ProjectResult with change data."""
        result = ProjectResult(
            project_name="test-project",
            project_dir="terraform/test",
            status="success",
            duration=45.5,
            log_file="test.log",
            changes_summary="3 to add, 2 to change",
            adds=3,
            changes=2,
            destroys=0,
        )

        assert result.changes_summary == "3 to add, 2 to change"
        assert result.adds == 3
        assert result.changes == 2
        assert result.destroys == 0


class TestMultiProjectRunner:
    """Tests for MultiProjectRunner."""

    def test_initialization(self, sample_workflow_runner, sample_project_matches, temp_log_dir):
        """Test MultiProjectRunner initialization."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
            workflow_name="default",
            max_workers=2,
        )

        assert runner.workflow_name == "default"
        assert runner.max_workers == 2
        assert len(runner.project_matches) == 2
        assert runner.log_dir == temp_log_dir
        assert len(runner.results) == 0

    def test_initialization_single_worker(
        self, sample_workflow_runner, sample_project_matches, temp_log_dir
    ):
        """Test initialization with single worker (serial mode)."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
            max_workers=1,
        )

        assert runner.max_workers == 1

    def test_initialization_default_workflow(
        self, sample_workflow_runner, sample_project_matches, temp_log_dir
    ):
        """Test that default workflow is used when not specified."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
        )

        assert runner.workflow_name == "default"

    def test_run_all_verbose_single_project(self, sample_workflow_runner, temp_log_dir):
        """Test running a single project in verbose mode."""
        projects = [
            ProjectMatch(
                project={
                    "name": "test-project",
                    "dir": "terraform/test",
                    "workspace": "default",
                    "workflow": "default",
                },
                matched_files=[],
                reason="test",
            ),
        ]

        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=projects,
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=True)

        assert manifest is not None
        assert "timestamp" in manifest
        assert "total_duration" in manifest
        assert "results" in manifest
        assert len(manifest["results"]) == 1
        assert manifest["results"][0]["project_name"] == "test-project"

    def test_run_all_table_mode_single_project(self, sample_workflow_runner, temp_log_dir):
        """Test running a single project in table mode."""
        projects = [
            ProjectMatch(
                project={
                    "name": "test-project",
                    "dir": "terraform/test",
                    "workspace": "default",
                    "workflow": "default",
                },
                matched_files=[],
                reason="test",
            ),
        ]

        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=projects,
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=False)

        assert manifest is not None
        assert len(manifest["results"]) == 1

    def test_run_all_multiple_projects_verbose(
        self, sample_workflow_runner, sample_project_matches, temp_log_dir
    ):
        """Test running multiple projects in verbose mode."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=True)

        assert len(manifest["results"]) == 2
        assert manifest["results"][0]["project_name"] == "api-prod"
        assert manifest["results"][1]["project_name"] == "core-stage"

    def test_run_all_multiple_projects_table(
        self, sample_workflow_runner, sample_project_matches, temp_log_dir
    ):
        """Test running multiple projects in table mode."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=False)

        assert len(manifest["results"]) == 2

    def test_run_all_parallel_mode(
        self, sample_workflow_runner, sample_project_matches, temp_log_dir
    ):
        """Test running projects in parallel mode."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
            max_workers=2,
        )

        manifest = runner.run_all(verbose=False)

        # All projects should complete
        assert len(manifest["results"]) == 2
        assert all(r["status"] == "success" for r in manifest["results"])

    def test_log_files_referenced(self, sample_workflow_runner, temp_log_dir):
        """Test that log files are referenced in results."""
        projects = [
            ProjectMatch(
                project={
                    "name": "test-project",
                    "dir": "terraform/test",
                    "workspace": "default",
                    "workflow": "default",
                },
                matched_files=[],
                reason="test",
            ),
        ]

        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=projects,
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=True)

        # Check that log file is referenced (it won't exist in dry-run mode)
        assert manifest["results"][0]["log_file"] is not None
        assert isinstance(manifest["results"][0]["log_file"], str)
        assert manifest["results"][0]["log_file"].endswith(".log")

    def test_manifest_structure(self, sample_workflow_runner, sample_project_matches, temp_log_dir):
        """Test that manifest has correct structure."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=True)

        # Check top-level fields
        assert "timestamp" in manifest
        assert "total_duration" in manifest
        assert "workflow" in manifest
        assert "results" in manifest

        # Check result structure
        result = manifest["results"][0]
        assert "project_name" in result
        assert "project_dir" in result
        assert "status" in result
        assert "duration" in result
        assert "log_file" in result

    def test_empty_project_list(self, sample_workflow_runner, temp_log_dir):
        """Test running with empty project list."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=[],
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=True)

        assert len(manifest["results"]) == 0
        assert manifest["total_duration"] >= 0

    def test_results_contain_status(
        self, sample_workflow_runner, sample_project_matches, temp_log_dir
    ):
        """Test that results contain status field."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=True)

        for result in manifest["results"]:
            assert result["status"] in ["success", "failed"]

    def test_duration_tracking(self, sample_workflow_runner, sample_project_matches, temp_log_dir):
        """Test that durations are tracked correctly."""
        runner = MultiProjectRunner(
            workflow_runner=sample_workflow_runner,
            project_matches=sample_project_matches,
            log_dir=temp_log_dir,
        )

        manifest = runner.run_all(verbose=True)

        # Each result should have a duration
        for result in manifest["results"]:
            assert result["duration"] >= 0

        # Total duration should be sum of all durations (in serial mode)
        total = manifest["total_duration"]
        assert total >= 0
