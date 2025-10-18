"""Tests for workflow execution."""

import pytest

from atlo.config import AtloConfig
from atlo.parser import AtlantisConfig
from atlo.workflow import WorkflowRunner, get_workflow_steps


@pytest.fixture
def sample_atlantis_config():
    """Sample Atlantis config for testing."""
    config_data = {
        "version": 3,
        "projects": [],
        "workflows": {
            "default": {
                "plan": {"steps": ["init", "plan"]},
                "apply": {"steps": ["apply"]},
            }
        },
    }
    return AtlantisConfig(config_data)


@pytest.fixture
def sample_atlo_config():
    """Sample Atlo config for testing."""
    return AtloConfig({"terraform_binary": "terraform"})


def test_workflow_runner_initialization(sample_atlantis_config, sample_atlo_config):
    """Test WorkflowRunner initialization."""
    runner = WorkflowRunner(
        atlantis_config=sample_atlantis_config,
        atlo_config=sample_atlo_config,
        debug=False,
        dry_run=True,
    )

    assert runner.terraform_binary == "terraform"
    assert runner.dry_run is True
    assert runner.debug is False


def test_workflow_runner_dry_run(sample_atlantis_config, sample_atlo_config):
    """Test workflow runner in dry-run mode."""
    runner = WorkflowRunner(
        atlantis_config=sample_atlantis_config,
        atlo_config=sample_atlo_config,
        dry_run=True,
    )

    # Should succeed in dry-run mode
    success, output = runner.run_plan()
    assert success is True
    assert isinstance(output, str)


def test_get_workflow_steps():
    """Test extracting workflow steps."""
    workflow_config = {"plan": {"steps": ["init", "plan", {"run": "echo test"}]}}

    steps = get_workflow_steps(workflow_config, "plan")
    assert len(steps) == 3
    assert steps[0] == "init"
    assert steps[1] == "plan"


def test_build_command(sample_atlantis_config):
    """Test building terraform commands."""
    # Test with disable_state_lock=False
    config_no_lock = AtloConfig({"disable_state_lock": False})
    runner = WorkflowRunner(
        atlantis_config=sample_atlantis_config,
        atlo_config=config_no_lock,
    )

    # Test init command (no -lock=false when disabled)
    cmd = runner._build_command("init")
    assert cmd == "terraform init"
    assert "-lock=false" not in cmd

    # Test plan command with directory
    cmd = runner._build_command("plan", directory="terraform/api")
    assert "terraform plan" in cmd
    assert "-chdir=terraform/api" in cmd

    # Test command with extra args
    cmd = runner._build_command("plan", directory="terraform/api", extra_args=["-out=tfplan"])
    assert "terraform plan" in cmd
    assert "-chdir=terraform/api" in cmd
    assert "-out=tfplan" in cmd


def test_substitute_env_vars(sample_atlantis_config, sample_atlo_config):
    """Test environment variable substitution."""
    runner = WorkflowRunner(
        atlantis_config=sample_atlantis_config,
        atlo_config=sample_atlo_config,
    )

    # Test basic substitution
    cmd = runner._substitute_env_vars("echo $WORKSPACE", workspace="prod")
    assert cmd == "echo prod"

    # Test multiple substitutions
    cmd = runner._substitute_env_vars(
        "cd $DIR && echo $WORKSPACE", directory="terraform/api", workspace="stage"
    )
    assert cmd == "cd terraform/api && echo stage"


def test_disable_state_lock(sample_atlantis_config):
    """Test that -lock=false is added when configured."""
    config_with_lock = AtloConfig({"disable_state_lock": True})
    runner = WorkflowRunner(atlantis_config=sample_atlantis_config, atlo_config=config_with_lock)

    # Init should have -lock=false
    cmd = runner._build_command("init", directory="terraform/api")
    assert "-lock=false" in cmd

    # Plan should have -lock=false
    cmd = runner._build_command("plan", directory="terraform/api")
    assert "-lock=false" in cmd

    # Apply should NOT have -lock=false
    cmd = runner._build_command("apply", directory="terraform/api")
    assert "-lock=false" not in cmd


def test_var_file_support(sample_atlantis_config):
    """Test that -var-file is added when configured."""
    config_with_varfile = AtloConfig({"default_var_file": "env.auto.tfvars"})
    runner = WorkflowRunner(atlantis_config=sample_atlantis_config, atlo_config=config_with_varfile)

    # Plan should have -var-file
    cmd = runner._build_command("plan", directory="terraform/api")
    assert "-var-file=env.auto.tfvars" in cmd

    # Apply should have -var-file
    cmd = runner._build_command("apply", directory="terraform/api")
    assert "-var-file=env.auto.tfvars" in cmd

    # Init should NOT have -var-file
    cmd = runner._build_command("init", directory="terraform/api")
    assert "-var-file" not in cmd


def test_command_wrapper(sample_atlantis_config):
    """Test command wrapper functionality."""
    config_with_wrapper = AtloConfig({"command_wrapper": "my-wrapper"})
    runner = WorkflowRunner(atlantis_config=sample_atlantis_config, atlo_config=config_with_wrapper)

    # Test wrapping a command
    cmd = "terraform plan -chdir=terraform/api"
    wrapped = runner._wrap_command(cmd)
    assert wrapped == "my-wrapper terraform plan -chdir=terraform/api"

    # Without wrapper
    config_no_wrapper = AtloConfig({})
    runner_no_wrapper = WorkflowRunner(
        atlantis_config=sample_atlantis_config, atlo_config=config_no_wrapper
    )
    wrapped = runner_no_wrapper._wrap_command(cmd)
    assert wrapped == cmd


def test_extra_terraform_flags(sample_atlantis_config):
    """Test that extra terraform flags are added to commands."""
    config_with_flags = AtloConfig({"extra_terraform_flags": ["-compact-warnings", "-no-color"]})
    runner = WorkflowRunner(atlantis_config=sample_atlantis_config, atlo_config=config_with_flags)

    # Plan should have extra flags
    cmd = runner._build_command("plan", directory="terraform/api")
    assert "-compact-warnings" in cmd
    assert "-no-color" in cmd


def test_run_plan_with_workspace(sample_atlantis_config, sample_atlo_config):
    """Test running plan with workspace specified."""
    runner = WorkflowRunner(
        atlantis_config=sample_atlantis_config,
        atlo_config=sample_atlo_config,
        dry_run=True,
    )

    # Should succeed in dry-run mode with workspace
    success, output = runner.run_plan(workspace="prod")
    assert success is True


def test_run_plan_with_directory(sample_atlantis_config, sample_atlo_config):
    """Test running plan with directory specified."""
    runner = WorkflowRunner(
        atlantis_config=sample_atlantis_config,
        atlo_config=sample_atlo_config,
        dry_run=True,
    )

    # Should succeed in dry-run mode with directory
    success, output = runner.run_plan(directory="terraform/api")
    assert success is True


def test_debug_mode(sample_atlantis_config):
    """Test runner with debug mode enabled."""
    config = AtloConfig({"debug": True})
    runner = WorkflowRunner(
        atlantis_config=sample_atlantis_config,
        atlo_config=config,
        dry_run=True,
        debug=True,
    )

    # Should initialize with debug enabled
    assert runner.debug is True


def test_get_workflow_steps_empty():
    """Test extracting workflow steps from empty config."""
    workflow_config = {}
    steps = get_workflow_steps(workflow_config, "plan")
    assert steps == []


def test_get_workflow_steps_with_run_commands():
    """Test extracting steps with run commands."""
    workflow_config = {
        "plan": {
            "steps": [
                "init",
                {"run": "echo test"},
                "plan",
                {"run": "custom-script.sh"},
            ]
        }
    }

    steps = get_workflow_steps(workflow_config, "plan")
    assert len(steps) == 4
