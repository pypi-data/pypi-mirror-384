"""Tests for utility functions."""

import tempfile
from pathlib import Path

from atlo.utils import (
    check_atlantis_yaml_exists,
    create_projects_table,
    create_workflow_table,
    print_banner,
    print_command_menu,
    print_error,
    print_info,
    print_step,
    print_success,
)


class TestPrintFunctions:
    """Tests for print utility functions."""

    def test_print_banner(self, capsys):
        """Test printing banner."""
        print_banner()

        captured = capsys.readouterr()
        assert "Atlo" in captured.out
        assert "Run Atlantis workflows locally" in captured.out

    def test_print_step(self, capsys):
        """Test printing step message."""
        print_step("Running terraform init")

        captured = capsys.readouterr()
        assert "→" in captured.out
        assert "Running terraform init" in captured.out

    def test_print_step_with_style(self, capsys):
        """Test printing step message with custom style."""
        print_step("Warning message", style="yellow")

        captured = capsys.readouterr()
        assert "→" in captured.out
        assert "Warning message" in captured.out

    def test_print_error(self, capsys):
        """Test printing error message."""
        print_error("Something went wrong")

        captured = capsys.readouterr()
        assert "✗" in captured.out
        assert "Something went wrong" in captured.out

    def test_print_success(self, capsys):
        """Test printing success message."""
        print_success("Operation completed")

        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "Operation completed" in captured.out

    def test_print_info(self, capsys):
        """Test printing info message."""
        print_info("Useful information")

        captured = capsys.readouterr()
        assert "i" in captured.out
        assert "Useful information" in captured.out


class TestTableCreation:
    """Tests for table creation functions."""

    def test_create_workflow_table_empty(self):
        """Test creating workflow table with no workflows."""
        table = create_workflow_table({})

        assert table.title == "Atlantis Workflows"
        # Table should still be created even if empty
        assert table is not None

    def test_create_workflow_table_with_workflows(self):
        """Test creating workflow table with workflows."""
        workflows = {
            "default": ["init", "plan"],
            "custom": ["init", "plan", "validate"],
        }

        table = create_workflow_table(workflows)

        assert table.title == "Atlantis Workflows"
        assert table is not None
        # Should have 2 columns
        assert len(table.columns) == 2

    def test_create_projects_table_empty(self):
        """Test creating projects table with no projects."""
        table = create_projects_table([])

        assert table.title == "Atlantis Projects"
        assert table is not None

    def test_create_projects_table_with_projects(self):
        """Test creating projects table with projects."""
        projects = [
            {
                "name": "api-prod",
                "dir": "terraform/api",
                "workspace": "prod",
            },
            {
                "name": "api-staging",
                "dir": "terraform/api",
                "workspace": "staging",
            },
        ]

        table = create_projects_table(projects)

        assert table.title == "Atlantis Projects"
        assert table is not None
        # Should have 3 columns
        assert len(table.columns) == 3

    def test_create_projects_table_with_missing_fields(self):
        """Test creating projects table with missing fields."""
        projects = [
            {
                "dir": "terraform/api",
                # Missing name and workspace
            }
        ]

        table = create_projects_table(projects)

        assert table is not None
        # Should handle missing fields gracefully


class TestCommandMenu:
    """Tests for command menu function."""

    def test_print_command_menu_without_atlantis_yaml(self, capsys):
        """Test printing command menu when atlantis.yaml not found."""
        print_command_menu(atlantis_yaml_found=False)

        captured = capsys.readouterr()
        assert "⚠" in captured.out or "warning" in captured.out.lower()
        assert "No atlantis.yaml found" in captured.out
        assert "atlo init" in captured.out
        assert "atlo plan" in captured.out

    def test_print_command_menu_with_atlantis_yaml(self, capsys):
        """Test printing command menu when atlantis.yaml is found."""
        print_command_menu(atlantis_yaml_found=True)

        captured = capsys.readouterr()
        assert "✓" in captured.out or "found" in captured.out.lower()
        assert "Found atlantis.yaml" in captured.out
        assert "atlo init" in captured.out
        assert "atlo plan" in captured.out
        assert "atlo diff" in captured.out
        assert "atlo export" in captured.out

    def test_print_command_menu_includes_examples(self, capsys):
        """Test that command menu includes quick examples."""
        print_command_menu(atlantis_yaml_found=True)

        captured = capsys.readouterr()
        assert "Quick Examples" in captured.out or "Examples" in captured.out
        assert "--dir" in captured.out
        assert "--workspace" in captured.out


class TestAtlantisYamlCheck:
    """Tests for atlantis.yaml existence check."""

    def test_check_atlantis_yaml_exists_in_current_dir(self):
        """Test checking for atlantis.yaml in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            (temp_path / "atlantis.yaml").touch()

            result = check_atlantis_yaml_exists(temp_path)
            assert result is True

    def test_check_atlantis_yaml_exists_in_parent_dir(self):
        """Test checking for atlantis.yaml in parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            (temp_path / "atlantis.yaml").touch()

            # Create subdirectory
            subdir = temp_path / "subdir"
            subdir.mkdir()

            result = check_atlantis_yaml_exists(subdir)
            assert result is True

    def test_check_atlantis_yaml_exists_nested_parents(self):
        """Test checking for atlantis.yaml in nested parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)
            (temp_path / "atlantis.yaml").touch()

            # Create nested subdirectories
            nested = temp_path / "level1" / "level2" / "level3"
            nested.mkdir(parents=True)

            result = check_atlantis_yaml_exists(nested)
            assert result is True

    def test_check_atlantis_yaml_not_found(self):
        """Test checking for atlantis.yaml when it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir)

            result = check_atlantis_yaml_exists(temp_path)
            assert result is False

    def test_check_atlantis_yaml_default_current_dir(self):
        """Test checking for atlantis.yaml with default (current directory)."""
        # This test uses the actual current directory
        # Just verify it doesn't crash
        result = check_atlantis_yaml_exists()
        assert isinstance(result, bool)
