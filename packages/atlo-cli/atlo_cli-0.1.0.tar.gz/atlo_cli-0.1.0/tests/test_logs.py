"""Tests for log management and viewing."""

import json
import tempfile
from pathlib import Path

from atlo.logs import LogManager, LogViewer


class TestLogManager:
    """Tests for LogManager."""

    def test_create_run_dir(self):
        """Test creating a new run directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override LOG_BASE_DIR
            original_base_dir = LogManager.LOG_BASE_DIR
            LogManager.LOG_BASE_DIR = Path(tmpdir) / ".atlo/logs"

            try:
                run_dir = LogManager.create_run_dir()

                assert run_dir.exists()
                assert run_dir.is_dir()
                # Check format: YYYY-MM-DD_HH-MM-SS
                assert len(run_dir.name) == 19
                assert run_dir.name[4] == "-"
                assert run_dir.name[10] == "_"
            finally:
                LogManager.LOG_BASE_DIR = original_base_dir

    def test_create_run_dir_creates_parents(self):
        """Test that create_run_dir creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = LogManager.LOG_BASE_DIR
            LogManager.LOG_BASE_DIR = Path(tmpdir) / "deep/nested/.atlo/logs"

            try:
                run_dir = LogManager.create_run_dir()

                assert run_dir.exists()
                assert run_dir.parent.exists()  # .atlo/logs
                assert run_dir.parent.parent.exists()  # .atlo
            finally:
                LogManager.LOG_BASE_DIR = original_base_dir

    def test_get_latest_run_returns_newest(self):
        """Test that get_latest_run returns the newest directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = LogManager.LOG_BASE_DIR
            log_base = Path(tmpdir) / ".atlo/logs"
            LogManager.LOG_BASE_DIR = log_base

            try:
                # Create multiple run directories
                (log_base / "2025-10-17_14-30-45").mkdir(parents=True)
                (log_base / "2025-10-17_15-45-30").mkdir(parents=True)
                (log_base / "2025-10-17_13-00-00").mkdir(parents=True)

                latest = LogManager.get_latest_run()

                assert latest is not None
                assert latest.name == "2025-10-17_15-45-30"
            finally:
                LogManager.LOG_BASE_DIR = original_base_dir

    def test_get_latest_run_no_directory(self):
        """Test get_latest_run when log directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = LogManager.LOG_BASE_DIR
            LogManager.LOG_BASE_DIR = Path(tmpdir) / "nonexistent"

            try:
                latest = LogManager.get_latest_run()
                assert latest is None
            finally:
                LogManager.LOG_BASE_DIR = original_base_dir

    def test_get_latest_run_empty_directory(self):
        """Test get_latest_run when directory exists but is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = LogManager.LOG_BASE_DIR
            log_base = Path(tmpdir) / ".atlo/logs"
            log_base.mkdir(parents=True)
            LogManager.LOG_BASE_DIR = log_base

            try:
                latest = LogManager.get_latest_run()
                assert latest is None
            finally:
                LogManager.LOG_BASE_DIR = original_base_dir

    def test_list_runs_returns_sorted(self):
        """Test that list_runs returns directories sorted by date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = LogManager.LOG_BASE_DIR
            log_base = Path(tmpdir) / ".atlo/logs"
            LogManager.LOG_BASE_DIR = log_base

            try:
                # Create run directories (not in order)
                (log_base / "2025-10-17_13-00-00").mkdir(parents=True)
                (log_base / "2025-10-17_15-45-30").mkdir(parents=True)
                (log_base / "2025-10-17_14-30-45").mkdir(parents=True)

                runs = LogManager.list_runs()

                assert len(runs) == 3
                # Should be sorted newest first
                assert runs[0].name == "2025-10-17_15-45-30"
                assert runs[1].name == "2025-10-17_14-30-45"
                assert runs[2].name == "2025-10-17_13-00-00"
            finally:
                LogManager.LOG_BASE_DIR = original_base_dir

    def test_list_runs_no_directory(self):
        """Test list_runs when log directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = LogManager.LOG_BASE_DIR
            LogManager.LOG_BASE_DIR = Path(tmpdir) / "nonexistent"

            try:
                runs = LogManager.list_runs()
                assert runs == []
            finally:
                LogManager.LOG_BASE_DIR = original_base_dir

    def test_list_runs_ignores_files(self):
        """Test that list_runs only returns directories, not files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = LogManager.LOG_BASE_DIR
            log_base = Path(tmpdir) / ".atlo/logs"
            LogManager.LOG_BASE_DIR = log_base

            try:
                # Create directories and files
                (log_base / "2025-10-17_14-30-45").mkdir(parents=True)
                (log_base / "some_file.txt").touch()

                runs = LogManager.list_runs()

                assert len(runs) == 1
                assert runs[0].name == "2025-10-17_14-30-45"
            finally:
                LogManager.LOG_BASE_DIR = original_base_dir

    def test_load_manifest_success(self):
        """Test loading a valid manifest file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            manifest_data = {
                "timestamp": "2025-10-17T14:30:45",
                "results": [{"project": "test"}],
            }

            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            loaded = LogManager.load_manifest(run_dir)

            assert loaded is not None
            assert loaded["timestamp"] == "2025-10-17T14:30:45"
            assert len(loaded["results"]) == 1

    def test_load_manifest_missing_file(self):
        """Test loading manifest when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            loaded = LogManager.load_manifest(run_dir)
            assert loaded is None

    def test_load_manifest_malformed_json(self):
        """Test loading manifest with malformed JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            with open(run_dir / "manifest.json", "w") as f:
                f.write("invalid json{{{")

            loaded = LogManager.load_manifest(run_dir)
            assert loaded is None

    def test_save_manifest(self):
        """Test saving manifest data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            manifest_data = {
                "timestamp": "2025-10-17T14:30:45",
                "total_duration": 120.5,
                "results": [{"project": "test", "status": "success"}],
            }

            LogManager.save_manifest(run_dir, manifest_data)

            # Verify file was created
            manifest_path = run_dir / "manifest.json"
            assert manifest_path.exists()

            # Verify contents
            with open(manifest_path) as f:
                loaded = json.load(f)

            assert loaded["timestamp"] == "2025-10-17T14:30:45"
            assert loaded["total_duration"] == 120.5
            assert len(loaded["results"]) == 1

    def test_save_manifest_creates_formatted_json(self):
        """Test that saved manifest is formatted with indentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            manifest_data = {"key": "value"}

            LogManager.save_manifest(run_dir, manifest_data)

            # Read raw content
            with open(run_dir / "manifest.json") as f:
                content = f.read()

            # Should have indentation (not single line)
            assert "\n" in content
            assert "  " in content  # 2-space indent


class TestLogViewer:
    """Tests for LogViewer."""

    def test_initialization(self):
        """Test LogViewer initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            viewer = LogViewer(run_dir)

            assert viewer.run_dir == run_dir
            assert viewer.manifest is None  # No manifest file

    def test_initialization_with_manifest(self):
        """Test LogViewer initialization with manifest file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            manifest_data = {
                "timestamp": "2025-10-17T14:30:45",
                "results": [],
            }

            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            viewer = LogViewer(run_dir)

            assert viewer.run_dir == run_dir
            assert viewer.manifest is not None
            assert viewer.manifest["timestamp"] == "2025-10-17T14:30:45"

    def test_view_project_no_manifest(self, capsys):
        """Test viewing project when no manifest exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            viewer = LogViewer(run_dir)
            viewer.view_project("test-project")

            captured = capsys.readouterr()
            assert "No manifest found" in captured.out

    def test_view_project_not_found(self, capsys):
        """Test viewing project that doesn't exist in manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            manifest_data = {
                "timestamp": "2025-10-17T14:30:45",
                "results": [
                    {
                        "project_name": "api-prod",
                        "log_file": "api-prod.log",
                        "status": "success",
                    }
                ],
            }

            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            viewer = LogViewer(run_dir)
            viewer.view_project("nonexistent")

            captured = capsys.readouterr()
            assert "not found" in captured.out

    def test_view_all_no_manifest(self, capsys):
        """Test viewing all logs when no manifest exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            viewer = LogViewer(run_dir)
            viewer.view_all()

            captured = capsys.readouterr()
            assert "No manifest found" in captured.out

    def test_view_failures_no_failures(self, capsys):
        """Test viewing failures when there are none."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            manifest_data = {
                "timestamp": "2025-10-17T14:30:45",
                "results": [
                    {
                        "project_name": "api-prod",
                        "status": "success",
                        "log_file": "api-prod.log",
                    }
                ],
            }

            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            viewer = LogViewer(run_dir)
            viewer.view_failures()

            captured = capsys.readouterr()
            assert "No failures" in captured.out

    def test_view_failures_shows_failed_only(self, capsys):
        """Test that view_failures only shows failed projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            manifest_data = {
                "timestamp": "2025-10-17T14:30:45",
                "results": [
                    {
                        "project_name": "success-project",
                        "status": "success",
                        "log_file": "success.log",
                    },
                    {
                        "project_name": "failed-project",
                        "status": "failed",
                        "error_message": "Plan failed",
                        "log_file": "failed.log",
                    },
                ],
            }

            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            # Create log file
            (run_dir / "failed.log").write_text("Error details here")

            viewer = LogViewer(run_dir)
            viewer.view_failures()

            captured = capsys.readouterr()
            assert "failed-project" in captured.out
            assert "Failed Project" in captured.out
            # Should not show success project
            assert "success-project" not in captured.out

    def test_print_summary(self, capsys):
        """Test printing summary table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run1"
            run_dir.mkdir()

            manifest_data = {
                "timestamp": "2025-10-17T14:30:45",
                "total_duration": 125.5,
                "results": [
                    {
                        "project_name": "api-prod",
                        "status": "success",
                        "duration": 45.2,
                        "changes_summary": "3 to add",
                    },
                    {
                        "project_name": "api-staging",
                        "status": "failed",
                        "duration": 30.1,
                        "changes_summary": None,
                    },
                ],
            }

            with open(run_dir / "manifest.json", "w") as f:
                json.dump(manifest_data, f)

            viewer = LogViewer(run_dir)
            viewer.print_summary()

            captured = capsys.readouterr()
            assert "2025-10-17T14:30:45" in captured.out
            assert "api-prod" in captured.out
            assert "api-staging" in captured.out
            assert "1 successful, 1 failed" in captured.out

    def test_format_duration_seconds(self):
        """Test duration formatting for seconds."""
        assert LogViewer._format_duration(45.5) == "45.5s"
        assert LogViewer._format_duration(10.0) == "10.0s"

    def test_format_duration_minutes(self):
        """Test duration formatting for minutes."""
        assert LogViewer._format_duration(90.0) == "1m 30s"
        assert LogViewer._format_duration(125.5) == "2m 5s"
        assert LogViewer._format_duration(60.0) == "1m 0s"
