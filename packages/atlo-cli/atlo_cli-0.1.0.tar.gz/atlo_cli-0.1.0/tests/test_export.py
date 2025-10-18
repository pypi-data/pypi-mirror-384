"""Tests for result export formats."""

import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from atlo.export import ResultExporter


@pytest.fixture
def sample_manifest():
    """Sample manifest for testing exports."""
    return {
        "timestamp": "2025-10-17T14:30:45.123456",
        "total_duration": 125.5,
        "workflow": "default",
        "results": [
            {
                "project_name": "api-prod",
                "project_dir": "envs/prod/api",
                "status": "success",
                "duration": 45.2,
                "log_file": "envs-prod-api.log",
                "error_message": None,
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
                "log_file": "envs-staging-api.log",
                "error_message": None,
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
                "log_file": "envs-prod-core.log",
                "error_message": "Plan failed",
                "changes_summary": None,
                "adds": None,
                "changes": None,
                "destroys": None,
            },
        ],
    }


class TestExportJSON:
    """Tests for JSON export."""

    def test_export_json_creates_file(self, sample_manifest):
        """Test that JSON export creates a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_json(sample_manifest, output_path)
            assert output_path.exists()
        finally:
            output_path.unlink()

    def test_export_json_valid_json(self, sample_manifest):
        """Test that exported JSON is valid and parseable."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_json(sample_manifest, output_path)

            # Read and parse JSON
            with open(output_path) as f:
                data = json.load(f)

            assert data["timestamp"] == sample_manifest["timestamp"]
            assert data["total_duration"] == sample_manifest["total_duration"]
            assert len(data["results"]) == 3
        finally:
            output_path.unlink()

    def test_export_json_includes_changes(self, sample_manifest):
        """Test that JSON export includes change data."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_json(sample_manifest, output_path)

            with open(output_path) as f:
                data = json.load(f)

            result = data["results"][0]
            assert result["adds"] == 3
            assert result["changes"] == 2
            assert result["destroys"] == 0
        finally:
            output_path.unlink()


class TestExportJUnit:
    """Tests for JUnit XML export."""

    def test_export_junit_creates_file(self, sample_manifest):
        """Test that JUnit export creates a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".xml") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_junit(sample_manifest, output_path)
            assert output_path.exists()
        finally:
            output_path.unlink()

    def test_export_junit_valid_xml(self, sample_manifest):
        """Test that exported XML is valid and parseable."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".xml") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_junit(sample_manifest, output_path)

            # Parse XML
            tree = ET.parse(output_path)
            root = tree.getroot()

            assert root.tag == "testsuite"
            assert root.attrib["name"] == "atlo-terraform-plan"
            assert root.attrib["tests"] == "3"
            assert root.attrib["failures"] == "1"
        finally:
            output_path.unlink()

    def test_export_junit_test_cases(self, sample_manifest):
        """Test that JUnit includes correct test cases."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".xml") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_junit(sample_manifest, output_path)

            tree = ET.parse(output_path)
            root = tree.getroot()
            testcases = root.findall("testcase")

            assert len(testcases) == 3

            # Check first test case
            assert testcases[0].attrib["name"] == "api-prod"
            assert testcases[0].attrib["classname"] == "envs/prod/api"
        finally:
            output_path.unlink()

    def test_export_junit_failure_element(self, sample_manifest):
        """Test that failures are marked correctly."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".xml") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_junit(sample_manifest, output_path)

            tree = ET.parse(output_path)
            root = tree.getroot()

            # Third test case should have failure
            testcase = root.findall("testcase")[2]
            failure = testcase.find("failure")

            assert failure is not None
            assert failure.attrib["message"] == "Plan failed"
        finally:
            output_path.unlink()

    def test_export_junit_properties(self, sample_manifest):
        """Test that change properties are included."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".xml") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_junit(sample_manifest, output_path)

            tree = ET.parse(output_path)
            root = tree.getroot()

            # First test case should have properties
            testcase = root.findall("testcase")[0]
            properties = testcase.find("properties")

            assert properties is not None

            # Find property elements
            props = {p.attrib["name"]: p.text for p in properties.findall("property")}
            assert props["adds"] == "3"
            assert props["changes"] == "2"
            assert props["destroys"] == "0"
        finally:
            output_path.unlink()


class TestExportMarkdown:
    """Tests for Markdown export."""

    def test_export_markdown_creates_file(self, sample_manifest):
        """Test that Markdown export creates a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_markdown(sample_manifest, output_path)
            assert output_path.exists()
        finally:
            output_path.unlink()

    def test_export_markdown_has_header(self, sample_manifest):
        """Test that Markdown has proper header."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_markdown(sample_manifest, output_path)

            content = output_path.read_text()
            assert "# Atlo Terraform Plan Results" in content
            assert "## Summary" in content
        finally:
            output_path.unlink()

    def test_export_markdown_has_table(self, sample_manifest):
        """Test that Markdown includes results table."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_markdown(sample_manifest, output_path)

            content = output_path.read_text()
            assert "| Project | Status | Duration | Changes |" in content
            assert "api-prod" in content
            assert "api-staging" in content
            assert "core-prod" in content
        finally:
            output_path.unlink()

    def test_export_markdown_has_stats(self, sample_manifest):
        """Test that Markdown includes statistics."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_markdown(sample_manifest, output_path)

            content = output_path.read_text()
            assert "**Successful:** 2" in content
            assert "**Failed:** 1" in content
        finally:
            output_path.unlink()

    def test_export_markdown_has_changes(self, sample_manifest):
        """Test that Markdown includes total changes."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_markdown(sample_manifest, output_path)

            content = output_path.read_text()
            assert "### Total Changes" in content
            assert "**To Add:** 3" in content
            assert "**To Change:** 2" in content
        finally:
            output_path.unlink()

    def test_export_markdown_has_failures(self, sample_manifest):
        """Test that Markdown includes failed projects section."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_markdown(sample_manifest, output_path)

            content = output_path.read_text()
            assert "## Failed Projects" in content
            assert "### core-prod" in content
            assert "Plan failed" in content
        finally:
            output_path.unlink()


class TestExportGitHub:
    """Tests for GitHub Actions export."""

    def test_export_github_creates_file(self, sample_manifest):
        """Test that GitHub export creates a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_github_actions(sample_manifest, output_path)
            assert output_path.exists()
        finally:
            output_path.unlink()

    def test_export_github_has_emojis(self, sample_manifest):
        """Test that GitHub format includes emojis."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_github_actions(sample_manifest, output_path)

            content = output_path.read_text()
            assert "🚀" in content  # Header emoji
            assert "📊" in content  # Summary emoji
            assert "✅" in content  # Success emoji
            assert "❌" in content  # Failure emoji
        finally:
            output_path.unlink()

    def test_export_github_has_summary(self, sample_manifest):
        """Test that GitHub format includes summary section."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_github_actions(sample_manifest, output_path)

            content = output_path.read_text()
            assert "## 📊 Summary" in content
            assert "2 successful, ❌ 1 failed" in content
        finally:
            output_path.unlink()

    def test_export_github_has_changes_block(self, sample_manifest):
        """Test that GitHub format includes changes in code block."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_github_actions(sample_manifest, output_path)

            content = output_path.read_text()
            assert "## 📝 Total Infrastructure Changes" in content
            assert "```" in content
            assert "+ 3 resources to add" in content
            assert "~ 2 resources to change" in content
        finally:
            output_path.unlink()

    def test_export_github_has_table(self, sample_manifest):
        """Test that GitHub format includes results table."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as f:
            output_path = Path(f.name)

        try:
            ResultExporter.export_github_actions(sample_manifest, output_path)

            content = output_path.read_text()
            assert "## 📋 Project Details" in content
            assert "| Status | Project | Changes | Duration |" in content
        finally:
            output_path.unlink()
