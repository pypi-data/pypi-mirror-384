"""Tests for the Atlantis YAML parser."""

from pathlib import Path

import pytest

from atlo.parser import AtlantisConfig, WorkflowStep, parse_atlantis_yaml


@pytest.fixture
def sample_config():
    """Sample atlantis.yaml config for testing."""
    config_data = {
        "version": 3,
        "projects": [
            {
                "name": "api-stage",
                "dir": "terraform/api",
                "workspace": "stage",
                "workflow": "default",
            }
        ],
        "workflows": {
            "default": {
                "plan": {"steps": ["init", "plan"]},
                "apply": {"steps": ["apply"]},
            }
        },
    }
    return AtlantisConfig(config_data)


def test_atlantis_config_initialization(sample_config):
    """Test that AtlantisConfig initializes correctly."""
    assert sample_config.version == 3
    assert len(sample_config.projects) == 1
    assert "default" in sample_config.workflows


def test_get_workflow_default(sample_config):
    """Test retrieving the default workflow."""
    workflow = sample_config.get_workflow("default")
    assert workflow is not None
    assert "plan" in workflow
    assert workflow["plan"]["steps"] == ["init", "plan"]


def test_get_workflow_missing(sample_config):
    """Test retrieving a non-existent workflow returns default."""
    workflow = sample_config.get_workflow("nonexistent")
    assert workflow is not None  # Should return default workflow


def test_list_projects(sample_config):
    """Test listing all projects."""
    projects = sample_config.list_projects()
    assert len(projects) == 1
    assert projects[0]["name"] == "api-stage"


def test_parse_atlantis_yaml():
    """Test parsing a real atlantis.yaml file."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    config_path = fixtures_dir / "atlantis.yaml"

    config = parse_atlantis_yaml(config_path)

    assert config.version == 3
    assert len(config.projects) == 3
    assert "default" in config.workflows
    assert "custom" in config.workflows


def test_parse_missing_file():
    """Test that parsing a missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        parse_atlantis_yaml(Path("/nonexistent/atlantis.yaml"))


def test_workflow_step_simple_string():
    """Test parsing a simple string step."""
    step = WorkflowStep("init")
    assert step.is_builtin()
    assert not step.is_run()
    assert step.command == "init"
    assert step.extra_args == []


def test_workflow_step_run_command():
    """Test parsing a run command step."""
    step = WorkflowStep({"run": "echo test"})
    assert step.is_run()
    assert not step.is_builtin()
    assert step.run_command == "echo test"


def test_workflow_step_with_extra_args():
    """Test parsing a step with extra_args."""
    step = WorkflowStep({"plan": {"extra_args": ["-lock=false", "-out=plan.tfplan"]}})
    assert step.is_builtin()
    assert step.command == "plan"
    assert step.extra_args == ["-lock=false", "-out=plan.tfplan"]


def test_parse_workflow_steps():
    """Test parsing workflow steps with the fixture."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    config_path = fixtures_dir / "atlantis.yaml"
    config = parse_atlantis_yaml(config_path)

    # Test default workflow
    steps = config.parse_workflow_steps("default", "plan")
    assert len(steps) == 2
    assert steps[0].command == "init"
    assert steps[1].command == "plan"

    # Test custom workflow with run step
    custom_steps = config.parse_workflow_steps("custom", "plan")
    assert len(custom_steps) == 3
    assert custom_steps[0].command == "init"
    assert custom_steps[1].is_run()
    assert custom_steps[1].run_command == "terraform fmt -check"
    assert custom_steps[2].command == "plan"


def test_get_project_workflow():
    """Test getting project-specific workflow."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    config_path = fixtures_dir / "atlantis.yaml"
    config = parse_atlantis_yaml(config_path)

    # Test project with custom workflow
    workflow_name = config.get_project_workflow(
        directory="terraform/infrastructure", workspace="default"
    )
    assert workflow_name == "custom"

    # Test project with default workflow
    workflow_name = config.get_project_workflow(directory="terraform/api", workspace="stage")
    assert workflow_name == "default"


def test_workflow_without_projects():
    """Test that workflows can be used without project definitions."""
    config_data = {
        "version": 3,
        "workflows": {
            "default": {
                "plan": {"steps": ["init", "plan"]},
                "apply": {"steps": ["apply"]},
            }
        },
    }
    config = AtlantisConfig(config_data)

    # Should have no projects
    assert len(config.projects) == 0

    # But should still have workflows
    workflow = config.get_workflow("default")
    assert workflow is not None
    assert "plan" in workflow

    # Should be able to parse workflow steps
    steps = config.parse_workflow_steps("default", "plan")
    assert len(steps) == 2
    assert steps[0].command == "init"
    assert steps[1].command == "plan"
