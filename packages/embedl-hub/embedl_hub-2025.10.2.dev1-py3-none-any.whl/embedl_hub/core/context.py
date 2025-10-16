# Copyright (C) 2025 Embedl AB

"""Context manager for managing the current experiment context."""

from pathlib import Path
from typing import Dict

import typer
import yaml

from embedl_hub.core.hub_logging import console

CTX_FILE = Path.home() / ".embedl_hub_ctx"


def write_ctx(ctx: Dict[str, str]) -> None:
    """Write the current embedl-hub context to the local YAML file."""
    CTX_FILE.write_text(yaml.safe_dump(ctx, sort_keys=False), encoding="utf-8")


def read_embedl_hub_context() -> Dict[str, str]:
    """Read the current embedl-hub context from the local YAML file."""
    return (
        yaml.safe_load(CTX_FILE.read_text(encoding="utf-8"))
        if CTX_FILE.exists()
        else {}
    )


def require_embedl_hub_context() -> Dict[str, str]:
    """
    Load the current embedl-hub context and ensure `project_name` and `experiment_name` are present.
    """
    ctx = read_embedl_hub_context()
    if not ctx.get("project_name") or not ctx.get("experiment_name"):
        console.print(
            "[red]Failed to find context: No project or experiment is initialized.[/]\n",
            "[red]Run 'embedl-hub init' to set up a project and experiment.[/]\n",
            "[red]Run 'embedl-hub auth' to set up an api key.[/]",
        )
        raise typer.Exit(1)
    return ctx
