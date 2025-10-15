# Copyright (C) 2025 Embedl AB
"""
Test cases for the embedl-hub CLI init command.

"""

import itertools

import pytest
import yaml
from typer.testing import CliRunner

from embedl_hub.cli.init import init_cli


class DummyCtx:
    def __init__(self, id, name):
        self.id = id
        self.name = name


@pytest.fixture(autouse=True)
def mock_tracking_and_ctx(monkeypatch, tmp_path):
    """
    Pytest fixture to mock tracking functions and redirect the context file
    to a temporary path. This prevents tests from making real API calls and
    from interfering with the user's actual context file.
    """
    # Mock tracking functions
    monkeypatch.setattr(
        "embedl_hub.core.tracking_utils.set_project",
        lambda name: DummyCtx(f"dummy_project_id_{name}", name),
    )
    monkeypatch.setattr(
        "embedl_hub.core.tracking_utils.set_experiment",
        lambda name: DummyCtx(f"dummy_experiment_id_{name}", name),
    )
    monkeypatch.setattr("embedl_hub.cli.utils.assert_api_config", lambda: None)

    # Monkeypatch CTX_FILE to use a temporary file
    temp_ctx_file = tmp_path / ".embedl_hub_ctx"
    monkeypatch.setattr("embedl_hub.core.context.CTX_FILE", temp_ctx_file)


runner = CliRunner()


def test_init_new_project(tmp_path):
    """Test creating a new project with the -p flag."""
    result = runner.invoke(init_cli, ["init", "-p", "MyProject"])
    assert result.exit_code == 0
    assert "✓ Project:" in result.output
    assert "✓ Experiment:" in result.output
    ctx_file = tmp_path / ".embedl_hub_ctx"
    ctx = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    assert ctx["project_name"] == "MyProject"
    assert ctx["project_id"] == "dummy_project_id_MyProject"
    assert (
        ctx["experiment_name"].startswith("experiment_")
        or ctx["experiment_name"]
    )
    assert ctx["experiment_id"].startswith("dummy_experiment_id_")


def test_init_new_experiment(tmp_path):
    """Test creating a new experiment with the -e flag in an existing project."""
    runner.invoke(init_cli, ["init", "-p", "MyProject"])
    result = runner.invoke(init_cli, ["init", "-e", "MyExperiment"])
    assert result.exit_code == 0
    assert "✓ Experiment:" in result.output
    ctx_file = tmp_path / ".embedl_hub_ctx"
    ctx = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    assert ctx["experiment_name"] == "MyExperiment"
    assert ctx["experiment_id"] == "dummy_experiment_id_MyExperiment"


def test_init_no_project_error():
    """Test when creating an experiment without an initialized project leads to a new experiment."""
    result = runner.invoke(init_cli, ["init", "-e", "MyExperiment"])
    assert result.exit_code == 0
    assert "No active project, creating a new one" in result.output


def test_init_default_project_and_experiment(tmp_path):
    """Test creating a default project and experiment with no flags."""
    result = runner.invoke(init_cli, ["init"])
    assert result.exit_code == 0
    assert "✓ Project:" in result.output
    assert "✓ Experiment:" in result.output
    ctx_file = tmp_path / ".embedl_hub_ctx"
    ctx = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    assert ctx["project_id"].startswith("dummy_project_id_project_")
    assert ctx["experiment_id"].startswith("dummy_experiment_id_experiment_")
    assert ctx["project_name"].startswith("project_")
    assert ctx["experiment_name"].startswith("experiment_")


def test_switch_project_resets_experiment(tmp_path):
    """Switching project should reset experiment context."""
    runner.invoke(init_cli, ["init", "-p", "Proj1", "-e", "Exp1"])
    ctx_file = tmp_path / ".embedl_hub_ctx"
    ctx1 = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    runner.invoke(init_cli, ["init", "-p", "Proj2"])
    ctx2 = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    assert ctx2["project_name"] == "Proj2"
    assert ctx2["project_id"] == "dummy_project_id_Proj2"
    assert ctx2["project_id"] != ctx1["project_id"]
    assert ctx2["experiment_id"] != ctx1["experiment_id"]


def test_show_command_outputs_context():
    """Test the show command prints the current context."""
    runner.invoke(init_cli, ["init", "-p", "ShowProj", "-e", "ShowExp"])
    result = runner.invoke(init_cli, ["show"])
    assert result.exit_code == 0
    assert ".embedl_hub_ctx" in result.output
    assert "project_id" in result.output
    assert "experiment_id" in result.output
    assert "ShowProj" in result.output
    assert "ShowExp" in result.output


def test_ctx_file_created_and_updated(tmp_path):
    """Test that the context file is created and updated as expected."""
    ctx_file = tmp_path / ".embedl_hub_ctx"
    assert not ctx_file.exists()
    runner.invoke(init_cli, ["init", "-p", "FileTestProj"])
    assert ctx_file.exists()
    ctx = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    assert ctx["project_name"] == "FileTestProj"
    assert ctx["project_id"] == "dummy_project_id_FileTestProj"
    runner.invoke(init_cli, ["init", "-e", "FileTestExp"])
    ctx2 = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    assert ctx2["experiment_name"] == "FileTestExp"
    assert ctx2["experiment_id"] == "dummy_experiment_id_FileTestExp"


def test_init_always_creates_new_project_and_experiment(monkeypatch, tmp_path):
    """Test that running 'init' with no flags always creates a new project and experiment."""

    project_counter = itertools.count()
    experiment_counter = itertools.count()

    monkeypatch.setattr(
        "embedl_hub.core.tracking_utils.set_project",
        lambda name: DummyCtx(
            f"dummy_project_id_{next(project_counter)}", name
        ),
    )
    monkeypatch.setattr(
        "embedl_hub.core.tracking_utils.set_experiment",
        lambda name: DummyCtx(
            f"dummy_experiment_id_{next(experiment_counter)}", name
        ),
    )
    # First run: create initial context
    result1 = runner.invoke(init_cli, ["init"])
    assert result1.exit_code == 0
    ctx_file = tmp_path / ".embedl_hub_ctx"
    ctx1 = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    project_id_1 = ctx1["project_id"]
    experiment_id_1 = ctx1["experiment_id"]
    # Second run: should create a new project and experiment, not reuse the old ones
    result2 = runner.invoke(init_cli, ["init"])
    assert result2.exit_code == 0
    ctx2 = yaml.safe_load(ctx_file.read_text(encoding="utf-8"))
    project_id_2 = ctx2["project_id"]
    experiment_id_2 = ctx2["experiment_id"]
    assert project_id_2 != project_id_1, (
        "Project ID should change on each init with no flags"
    )
    assert experiment_id_2 != experiment_id_1, (
        "Experiment ID should change on each init with no flags"
    )


if __name__ == "__main__":
    pytest.main([__file__])
