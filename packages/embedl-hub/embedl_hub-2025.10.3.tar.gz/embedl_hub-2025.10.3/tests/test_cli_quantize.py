# Copyright (C) 2025 Embedl AB

"""Test the CLI for quantizing models using the Embedl Hub SDK."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from embedl_hub.cli.quantize import quantize_cli


def test_quantize_cli_uses_default_config():
    """
    Test the CLI with default configuration.

    The test should fail due to lacking config settings.
    """

    runner = CliRunner()
    result = runner.invoke(quantize_cli)
    assert result.exit_code == 2
    assert isinstance(result.exception, SystemExit)


def test_quantize_cli_overrides_with_flags(monkeypatch):
    """Test the CLI with command-line flags to override default configuration."""

    captured = {}

    # pylint: disable-next=unused-argument
    def fake_quantize_model(config, project_name, experiment_name):
        """Fake quantize_model function to capture the config."""
        captured["cfg"] = config

    monkeypatch.setattr(
        "embedl_hub.core.quantization.quantize.quantize_model",
        fake_quantize_model,
    )
    monkeypatch.setattr('embedl_hub.cli.utils.assert_api_config', lambda: None)
    monkeypatch.setattr(
        "embedl_hub.core.context.read_embedl_hub_context",
        lambda: {
            "project_name": "test_project",
            "experiment_name": "test_experiment",
        },
    )

    runner = CliRunner()
    args = [
        "--model",
        "my-model",
        "--data",
        "/other/data",
    ]
    result = runner.invoke(quantize_cli, args)
    assert result.exit_code == 0

    cfg = captured["cfg"]
    assert cfg.model == Path("my-model")
    assert cfg.data_path == Path("/other/data")
    assert cfg.num_samples == 500  # default


def test_quantize_cli_with_custom_config_file(tmp_path, monkeypatch):
    """Test the CLI with a custom YAML configuration file."""

    # Create a custom YAML and pass via --config
    custom = {
        "data_path": "/mnt/x",
        "num_samples": 128,
    }
    custom_path = tmp_path / "custom.yaml"
    custom_path.write_text(yaml.dump(custom))

    captured = {}

    # pylint: disable-next=unused-argument
    def fake_quantize_model(config, project_name, experiment_name):
        """Fake quantize_model function to capture the config."""
        captured["cfg"] = config

    monkeypatch.setattr(
        "embedl_hub.core.quantization.quantize.quantize_model",
        fake_quantize_model,
    )
    monkeypatch.setattr('embedl_hub.cli.utils.assert_api_config', lambda: None)
    monkeypatch.setattr(
        "embedl_hub.core.context.read_embedl_hub_context",
        lambda: {
            "project_name": "test_project",
            "experiment_name": "test_experiment",
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        quantize_cli, ["--model", "from-cli", "--config", str(custom_path)]
    )
    assert result.exit_code == 0

    cfg = captured["cfg"]
    assert cfg.model == Path("from-cli")
    assert cfg.data_path == Path("/mnt/x")
    assert cfg.num_samples == 128


if __name__ == "__main__":
    pytest.main([__file__])
