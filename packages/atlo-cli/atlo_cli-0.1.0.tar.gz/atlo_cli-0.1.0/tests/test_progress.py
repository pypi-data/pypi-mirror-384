"""Tests for progress estimation."""

import json
import tempfile
from pathlib import Path

import pytest

from atlo.progress import ProgressEstimator


@pytest.fixture
def temp_log_dir():
    """Create a temporary log directory with sample manifests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_dir = Path(tmpdir)

        # Create sample run 1
        run1_dir = log_dir / "2025-10-17_14-30-45"
        run1_dir.mkdir()
        manifest1 = {
            "timestamp": "2025-10-17T14:30:45",
            "total_duration": 150.0,
            "workflow": "default",
            "results": [
                {
                    "project_name": "api-prod",
                    "status": "success",
                    "duration": 45.5,
                },
                {
                    "project_name": "api-staging",
                    "status": "success",
                    "duration": 38.2,
                },
                {
                    "project_name": "core-prod",
                    "status": "failed",
                    "duration": 15.0,
                },
            ],
        }
        with open(run1_dir / "manifest.json", "w") as f:
            json.dump(manifest1, f)

        # Create sample run 2
        run2_dir = log_dir / "2025-10-17_15-45-30"
        run2_dir.mkdir()
        manifest2 = {
            "timestamp": "2025-10-17T15:45:30",
            "total_duration": 145.0,
            "workflow": "default",
            "results": [
                {
                    "project_name": "api-prod",
                    "status": "success",
                    "duration": 42.8,
                },
                {
                    "project_name": "api-staging",
                    "status": "success",
                    "duration": 40.1,
                },
                {
                    "project_name": "core-prod",
                    "status": "success",
                    "duration": 50.0,
                },
            ],
        }
        with open(run2_dir / "manifest.json", "w") as f:
            json.dump(manifest2, f)

        yield log_dir


class TestProgressEstimator:
    """Tests for ProgressEstimator."""

    def test_empty_history(self):
        """Test estimator with no historical data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            estimator = ProgressEstimator(Path(tmpdir) / "nonexistent")
            assert estimator._historical_data == {}

    def test_load_history(self, temp_log_dir):
        """Test loading historical data from manifests."""
        estimator = ProgressEstimator(temp_log_dir)

        # Should have data for projects that succeeded in at least one run
        assert "api-prod" in estimator._historical_data
        assert "api-staging" in estimator._historical_data
        assert "core-prod" in estimator._historical_data

    def test_estimate_duration_known_project(self, temp_log_dir):
        """Test estimating duration for a known project."""
        estimator = ProgressEstimator(temp_log_dir)

        # api-prod ran twice: 45.5s and 42.8s, average = 44.15s
        estimate = estimator.estimate_duration("api-prod")
        assert estimate is not None
        assert 44.0 < estimate < 44.5

    def test_estimate_duration_unknown_project(self, temp_log_dir):
        """Test estimating duration for an unknown project."""
        estimator = ProgressEstimator(temp_log_dir)

        estimate = estimator.estimate_duration("unknown-project")
        assert estimate is None

    def test_estimate_total_all_known(self, temp_log_dir):
        """Test total estimation when all projects are known."""
        estimator = ProgressEstimator(temp_log_dir)

        total, count = estimator.estimate_total(["api-prod", "api-staging"])

        assert count == 2
        assert total > 80  # Both should be around 40-45s each

    def test_estimate_total_some_unknown(self, temp_log_dir):
        """Test total estimation with some unknown projects."""
        estimator = ProgressEstimator(temp_log_dir)

        total, count = estimator.estimate_total(["api-prod", "unknown-project", "api-staging"])

        # Only 2 projects should be estimated
        assert count == 2
        # Total should only include known projects
        assert total > 80

    def test_estimate_total_all_unknown(self, temp_log_dir):
        """Test total estimation when all projects are unknown."""
        estimator = ProgressEstimator(temp_log_dir)

        total, count = estimator.estimate_total(["unknown1", "unknown2"])

        assert count == 0
        assert total == 0.0

    def test_get_default_estimate_with_data(self, temp_log_dir):
        """Test default estimate when we have historical data."""
        estimator = ProgressEstimator(temp_log_dir)

        default = estimator.get_default_estimate()

        # Should be average of all project durations
        assert default > 0
        assert default < 100  # Reasonable default

    def test_get_default_estimate_no_data(self):
        """Test default estimate with no historical data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            estimator = ProgressEstimator(Path(tmpdir) / "nonexistent")

            default = estimator.get_default_estimate()

            # Should return fallback value
            assert default == 30.0

    def test_averages_multiple_runs(self, temp_log_dir):
        """Test that estimates are averaged across multiple runs."""
        estimator = ProgressEstimator(temp_log_dir)

        # api-staging ran twice: 38.2s and 40.1s
        estimate = estimator.estimate_duration("api-staging")
        assert estimate is not None

        # Average should be around 39.15s
        expected = (38.2 + 40.1) / 2
        assert abs(estimate - expected) < 0.1

    def test_ignores_failed_runs(self, temp_log_dir):
        """Test that failed runs are not included in estimates."""
        estimator = ProgressEstimator(temp_log_dir)

        # core-prod failed in run 1 (15.0s), succeeded in run 2 (50.0s)
        # Should only use the successful run
        estimate = estimator.estimate_duration("core-prod")
        assert estimate is not None
        assert estimate == 50.0

    def test_handles_malformed_manifests(self, temp_log_dir):
        """Test that estimator handles malformed manifest files gracefully."""
        # Create a malformed manifest
        bad_run_dir = temp_log_dir / "2025-10-17_16-00-00"
        bad_run_dir.mkdir()
        with open(bad_run_dir / "manifest.json", "w") as f:
            f.write("invalid json{{{")

        # Should not crash
        estimator = ProgressEstimator(temp_log_dir)
        assert len(estimator._historical_data) > 0

    def test_limits_to_recent_runs(self):
        """Test that estimator only uses recent runs (last 10)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)

            # Create 15 runs
            for i in range(15):
                run_dir = log_dir / f"2025-10-17_10-{i:02d}-00"
                run_dir.mkdir()
                manifest = {
                    "timestamp": f"2025-10-17T10:{i:02d}:00",
                    "results": [
                        {
                            "project_name": "test-project",
                            "status": "success",
                            "duration": float(i + 20),
                        }
                    ],
                }
                with open(run_dir / "manifest.json", "w") as f:
                    json.dump(manifest, f)

            estimator = ProgressEstimator(log_dir)

            # Should only use last 10 runs (runs 5-14)
            # Average should be around (25+26+27+28+29+30+31+32+33+34)/10 = 29.5
            estimate = estimator.estimate_duration("test-project")
            assert estimate is not None
            assert 29.0 < estimate < 30.0

    def test_no_crash_on_missing_fields(self, temp_log_dir):
        """Test that estimator handles missing fields in manifest."""
        # Create manifest with missing fields
        run_dir = temp_log_dir / "2025-10-17_17-00-00"
        run_dir.mkdir()
        manifest = {
            "timestamp": "2025-10-17T17:00:00",
            "results": [
                {
                    # Missing project_name
                    "status": "success",
                    "duration": 30.0,
                },
                {
                    "project_name": "test",
                    # Missing status
                    "duration": 40.0,
                },
                {
                    "project_name": "test2",
                    "status": "success",
                    # Missing duration
                },
            ],
        }
        with open(run_dir / "manifest.json", "w") as f:
            json.dump(manifest, f)

        # Should not crash
        estimator = ProgressEstimator(temp_log_dir)
        assert len(estimator._historical_data) > 0
