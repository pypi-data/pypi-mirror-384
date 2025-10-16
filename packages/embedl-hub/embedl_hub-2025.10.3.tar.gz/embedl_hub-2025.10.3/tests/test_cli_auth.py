# Copyright (C) 2025 Embedl AB
"""
Test cases for the embedl-hub CLI init command.

"""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from embedl_hub.cli.auth import auth_cli

runner = CliRunner()


@patch("embedl_hub.core.context.write_ctx")
@patch("embedl_hub.core.context.read_embedl_hub_context")
@patch("embedl_hub.core.hub_logging.console")
def test_auth_command_success(mock_console, mock_read_ctx, mock_write_ctx):
    """Test that auth_command successfully stores a new API key."""
    # Arrange
    mock_read_ctx.return_value = {}
    api_key = "test-api-key-123"

    # Act
    result = runner.invoke(auth_cli, ["--api-key", api_key])

    # Assert
    assert result.exit_code == 0
    mock_read_ctx.assert_called_once()
    mock_write_ctx.assert_called_once_with({"api_key": api_key})
    mock_console.print.assert_called_once_with("[green]✓ Stored API key[/]")


@patch("embedl_hub.core.context.write_ctx")
@patch("embedl_hub.core.context.read_embedl_hub_context")
@patch("embedl_hub.core.hub_logging.console")
def test_auth_command_updates_existing_key(
    mock_console, mock_read_ctx, mock_write_ctx
):
    """Test that auth_command successfully updates an existing API key."""
    # Arrange
    mock_read_ctx.return_value = {
        "api_key": "old-key",
        "other_data": "persists",
    }
    new_api_key = "new-api-key-456"

    # Act
    result = runner.invoke(auth_cli, ["--api-key", new_api_key])

    # Assert
    assert result.exit_code == 0
    mock_read_ctx.assert_called_once()
    mock_write_ctx.assert_called_once_with(
        {"api_key": new_api_key, "other_data": "persists"}
    )
    mock_console.print.assert_called_once_with("[green]✓ Stored API key[/]")


def test_auth_command_missing_api_key():
    """Test that the command fails if the --api-key option is missing."""
    # Act
    result = runner.invoke(auth_cli, [])

    # Assert
    assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__])
