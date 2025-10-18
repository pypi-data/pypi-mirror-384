"""Tests for configuration management."""

import tempfile
from pathlib import Path

import yaml

from atlo.config import AtloConfig, find_atlo_config, load_atlo_config, merge_configs


def test_atlo_config_defaults():
    """Test that AtloConfig has correct defaults."""
    config = AtloConfig()

    assert config.terraform_binary == "terraform"
    assert config.debug is False
    assert config.disable_state_lock is True  # Default for local runs
    assert config.skip_init_if_present is True
    assert config.workspace_auto_create is True
    assert config.continue_on_error is False
    assert config.command_wrapper is None
    assert config.default_var_file is None
    assert config.extra_terraform_flags == []


def test_atlo_config_custom_values():
    """Test AtloConfig with custom values."""
    config_data = {
        "terraform_binary": "tofu",
        "debug": True,
        "disable_state_lock": False,
        "skip_init_if_present": False,
        "command_wrapper": "my-wrapper",
        "default_var_file": "custom.tfvars",
        "extra_terraform_flags": ["-out=tfplan"],
        "env": {"TF_LOG": "DEBUG"},
    }

    config = AtloConfig(config_data)

    assert config.terraform_binary == "tofu"
    assert config.debug is True
    assert config.disable_state_lock is False
    assert config.skip_init_if_present is False
    assert config.command_wrapper == "my-wrapper"
    assert config.default_var_file == "custom.tfvars"
    assert config.extra_terraform_flags == ["-out=tfplan"]
    assert config.get_env_vars() == {"TF_LOG": "DEBUG"}


def test_atlo_config_project_overrides():
    """Test project-specific overrides."""
    config_data = {
        "projects": {"api-stage": {"terraform_binary": "tofu", "var_file": "stage.tfvars"}}
    }

    config = AtloConfig(config_data)

    project_config = config.get_project_config("api-stage")
    assert project_config["terraform_binary"] == "tofu"
    assert project_config["var_file"] == "stage.tfvars"

    # Non-existent project returns empty dict
    empty_config = config.get_project_config("non-existent")
    assert empty_config == {}


def test_load_atlo_config_missing_file():
    """Test loading config when file doesn't exist returns defaults."""
    config = load_atlo_config(Path("/nonexistent/.atlo.yaml"))

    assert config.terraform_binary == "terraform"
    assert config.disable_state_lock is True


def test_extra_terraform_flags_default():
    """Test that extra_terraform_flags returns empty list by default."""
    config = AtloConfig()
    assert config.get_extra_terraform_flags() == []


def test_extra_terraform_flags_configured():
    """Test configured extra_terraform_flags."""
    config = AtloConfig({"extra_terraform_flags": ["-compact-warnings", "-no-color"]})
    flags = config.get_extra_terraform_flags()
    assert flags == ["-compact-warnings", "-no-color"]


def test_environment_variables():
    """Test custom environment variables."""
    config = AtloConfig({"env": {"TF_LOG": "DEBUG", "AWS_REGION": "us-west-2"}})
    env_vars = config.get_env_vars()
    assert env_vars["TF_LOG"] == "DEBUG"
    assert env_vars["AWS_REGION"] == "us-west-2"


def test_environment_variables_default_empty():
    """Test that env vars default to empty dict."""
    config = AtloConfig()
    assert config.get_env_vars() == {}


def test_max_parallel_projects_validation():
    """Test max_parallel_projects is validated and capped."""
    # Test upper bound
    config_high = AtloConfig({"max_parallel_projects": 20})
    assert config_high.max_parallel_projects == 10

    # Test lower bound
    config_low = AtloConfig({"max_parallel_projects": 0})
    assert config_low.max_parallel_projects == 1

    # Test negative
    config_neg = AtloConfig({"max_parallel_projects": -5})
    assert config_neg.max_parallel_projects == 1

    # Test valid value
    config_valid = AtloConfig({"max_parallel_projects": 5})
    assert config_valid.max_parallel_projects == 5


def test_workspace_auto_create_default():
    """Test workspace_auto_create defaults to True."""
    config = AtloConfig()
    assert config.workspace_auto_create is True


def test_workspace_auto_create_configured():
    """Test workspace_auto_create can be configured."""
    config = AtloConfig({"workspace_auto_create": False})
    assert config.workspace_auto_create is False


def test_continue_on_error_default():
    """Test continue_on_error defaults to False."""
    config = AtloConfig()
    assert config.continue_on_error is False


def test_continue_on_error_configured():
    """Test continue_on_error can be configured."""
    config = AtloConfig({"continue_on_error": True})
    assert config.continue_on_error is True


def test_step_timeout_default():
    """Test step_timeout defaults to None."""
    config = AtloConfig()
    assert config.step_timeout is None


def test_step_timeout_configured():
    """Test step_timeout can be configured."""
    config = AtloConfig({"step_timeout": 300})
    assert config.step_timeout == 300


def test_disable_state_lock_default():
    """Test disable_state_lock defaults to True for local runs."""
    config = AtloConfig()
    assert config.disable_state_lock is True


def test_disable_state_lock_configured():
    """Test disable_state_lock can be configured."""
    config = AtloConfig({"disable_state_lock": False})
    assert config.disable_state_lock is False


def test_skip_init_if_present_default():
    """Test skip_init_if_present defaults to True."""
    config = AtloConfig()
    assert config.skip_init_if_present is True


def test_skip_init_if_present_configured():
    """Test skip_init_if_present can be configured."""
    config = AtloConfig({"skip_init_if_present": False})
    assert config.skip_init_if_present is False


def test_command_wrapper_default():
    """Test command_wrapper defaults to None."""
    config = AtloConfig()
    assert config.command_wrapper is None


def test_command_wrapper_configured():
    """Test command_wrapper can be configured."""
    config = AtloConfig({"command_wrapper": "docker run terraform"})
    assert config.command_wrapper == "docker run terraform"


def test_default_var_file_default():
    """Test default_var_file defaults to None."""
    config = AtloConfig()
    assert config.default_var_file is None


def test_default_var_file_configured():
    """Test default_var_file can be configured."""
    config = AtloConfig({"default_var_file": "vars/prod.tfvars"})
    assert config.default_var_file == "vars/prod.tfvars"


def test_project_prefix_default():
    """Test project_prefix defaults to empty string."""
    config = AtloConfig()
    assert config.project_prefix == ""


def test_project_prefix_configured():
    """Test project_prefix can be configured."""
    config = AtloConfig({"project_prefix": "tf-"})
    assert config.project_prefix == "tf-"


def test_get_terraform_binary():
    """Test get_terraform_binary method."""
    config = AtloConfig({"terraform_binary": "/usr/local/bin/tofu"})
    assert config.get_terraform_binary() == "/usr/local/bin/tofu"


def test_project_config_with_none_project_name():
    """Test get_project_config with None project name."""
    config = AtloConfig({"projects": {"test": {"workspace": "prod"}}})
    result = config.get_project_config(None)
    assert result == {}


def test_all_fields_configured():
    """Test config with all fields configured."""
    config_data = {
        "terraform_binary": "/usr/local/bin/terraform",
        "project_prefix": "tf-",
        "debug": True,
        "env": {"TF_LOG": "DEBUG"},
        "extra_terraform_flags": ["-no-color"],
        "workspace_auto_create": False,
        "continue_on_error": True,
        "step_timeout": 600,
        "disable_state_lock": False,
        "skip_init_if_present": False,
        "command_wrapper": "docker run",
        "default_var_file": "vars/prod.tfvars",
        "max_parallel_projects": 8,
        "projects": {"test": {"workspace": "prod"}},
    }

    config = AtloConfig(config_data)

    assert config.terraform_binary == "/usr/local/bin/terraform"
    assert config.project_prefix == "tf-"
    assert config.debug is True
    assert config.custom_env == {"TF_LOG": "DEBUG"}
    assert config.extra_terraform_flags == ["-no-color"]
    assert config.workspace_auto_create is False
    assert config.continue_on_error is True
    assert config.step_timeout == 600
    assert config.disable_state_lock is False
    assert config.skip_init_if_present is False
    assert config.command_wrapper == "docker run"
    assert config.default_var_file == "vars/prod.tfvars"
    assert config.max_parallel_projects == 8
    assert config.project_overrides == {"test": {"workspace": "prod"}}


def test_find_atlo_config_in_current_dir():
    """Test finding .atlo.yaml in current directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir).resolve()
        config_file = temp_path / ".atlo.yaml"
        config_file.write_text("terraform_binary: tofu\n")

        result = find_atlo_config(temp_path)
        assert result == config_file


def test_find_atlo_config_in_parent_dir():
    """Test finding .atlo.yaml in parent directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir).resolve()
        config_file = temp_path / ".atlo.yaml"
        config_file.write_text("terraform_binary: tofu\n")

        # Create subdirectory
        subdir = temp_path / "subdir"
        subdir.mkdir()

        result = find_atlo_config(subdir)
        assert result == config_file


def test_find_atlo_config_nested_parents():
    """Test finding .atlo.yaml in nested parent directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir).resolve()
        config_file = temp_path / ".atlo.yaml"
        config_file.write_text("terraform_binary: tofu\n")

        # Create nested subdirectories
        nested_dir = temp_path / "a" / "b" / "c"
        nested_dir.mkdir(parents=True)

        result = find_atlo_config(nested_dir)
        assert result == config_file


def test_find_atlo_config_not_found():
    """Test when .atlo.yaml is not found anywhere."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)
        result = find_atlo_config(temp_path)
        assert result is None


def test_find_atlo_config_default_cwd():
    """Test finding .atlo.yaml from current working directory."""
    # Just verify it doesn't crash when called without arguments
    result = find_atlo_config()
    # Result could be None or a Path, just check it's one of those
    assert result is None or isinstance(result, Path)


def test_load_atlo_config_with_valid_file():
    """Test loading a valid .atlo.yaml file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".atlo.yaml"
        config_data = {
            "terraform_binary": "tofu",
            "debug": True,
            "max_parallel_projects": 5,
        }
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        config = load_atlo_config(config_file)
        assert config.terraform_binary == "tofu"
        assert config.debug is True
        assert config.max_parallel_projects == 5


def test_load_atlo_config_with_empty_file():
    """Test loading an empty .atlo.yaml file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / ".atlo.yaml"
        config_file.write_text("")

        config = load_atlo_config(config_file)
        # Should return defaults
        assert config.terraform_binary == "terraform"


def test_merge_configs_basic():
    """Test merging Atlantis and Atlo configs."""
    atlantis_config = {
        "version": 3,
        "projects": [{"name": "api-prod", "dir": "envs/prod/api", "workspace": "default"}],
    }

    atlo_config = AtloConfig({"terraform_binary": "tofu"})

    merged = merge_configs(atlantis_config, atlo_config)

    # Should preserve atlantis config
    assert merged["version"] == 3
    assert len(merged["projects"]) == 1
    assert merged["projects"][0]["name"] == "api-prod"


def test_merge_configs_with_project_overrides():
    """Test merging configs with project-specific overrides."""
    atlantis_config = {
        "version": 3,
        "projects": [
            {"name": "api-prod", "dir": "envs/prod/api", "workspace": "default"},
            {"name": "api-staging", "dir": "envs/staging/api", "workspace": "default"},
        ],
    }

    atlo_config = AtloConfig(
        {"projects": {"api-prod": {"workspace": "prod", "extra_field": "value"}}}
    )

    merged = merge_configs(atlantis_config, atlo_config)

    # api-prod should have overrides applied
    api_prod = merged["projects"][0]
    assert api_prod["workspace"] == "prod"
    assert api_prod["extra_field"] == "value"

    # api-staging should be unchanged
    api_staging = merged["projects"][1]
    assert api_staging["workspace"] == "default"


def test_merge_configs_no_project_overrides():
    """Test merging configs without project overrides."""
    atlantis_config = {
        "version": 3,
        "projects": [{"name": "test", "dir": "test"}],
    }

    atlo_config = AtloConfig({})

    merged = merge_configs(atlantis_config, atlo_config)

    # Should return unmodified atlantis config
    assert merged["projects"][0]["name"] == "test"
    assert merged["projects"][0]["dir"] == "test"


def test_merge_configs_preserves_original():
    """Test that merge_configs doesn't modify original config."""
    atlantis_config = {
        "version": 3,
        "projects": [{"name": "test", "dir": "test", "workspace": "default"}],
    }

    atlo_config = AtloConfig({"projects": {"test": {"workspace": "prod"}}})

    merged = merge_configs(atlantis_config, atlo_config)

    # Original should be unchanged
    assert atlantis_config["projects"][0]["workspace"] == "default"

    # Merged should have override
    assert merged["projects"][0]["workspace"] == "prod"
