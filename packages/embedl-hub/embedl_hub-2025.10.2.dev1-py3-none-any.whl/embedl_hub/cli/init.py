# Copyright (C) 2025 Embedl AB
"""
Project and experiment context management for embedl-hub CLI.

This module provides CLI commands to initialize and display the current project
and experiment context. The selected context determines under which project and
experiment all data, results, and metadata are stored in the user's account on
https://hub.embedl.com.

Users can create new projects and experiments, switch between them, and view the
active context. Context information is stored locally in a YAML file.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.table import Table

init_cli = typer.Typer(help="Initialise / show project & experiment context")


@init_cli.command("init")
def init_command(
    project: Optional[str] = typer.Option(
        None, "-p", "--project", help="Project name or id", show_default=False
    ),
    experiment: Optional[str] = typer.Option(
        None,
        "-e",
        "--experiment",
        help="Experiment name or id",
        show_default=False,
    ),
):
    """
    Configure persistent CLI context.

    This command stores values used by other commands in a local context file
    in your home directory. The context file can contain:

    - Active project (created automatically if name does not exist)
    - Active experiment (created automatically if name does not exist)

    Examples
    --------
    Create a new project and experiment with random names:
        $ embedl-hub init

    Create or set named project:
        $ embedl-hub init -p "My Flower Detector App"

    Create or load named experiment inside current project:
        $ embedl-hub init -e "MobileNet Flower Detector"

    Set both project and experiment explicitly:
        $ embedl-hub init -p "My Flower Detector App" -e "MobileNet Flower Detector"
    """

    # pylint: disable=import-outside-toplevel
    from embedl_hub.cli.utils import assert_api_config
    from embedl_hub.core.context import (
        read_embedl_hub_context,
        write_ctx,
    )
    from embedl_hub.core.hub_logging import console
    from embedl_hub.core.tracking_utils import (
        set_new_experiment,
        set_new_project,
    )
    from embedl_hub.tracking.utils import (
        to_experiment_url,
    )
    # pylint: enable=import-outside-toplevel

    assert_api_config()

    ctx = read_embedl_hub_context()
    current_project = ctx.get("project_name")
    current_experiment = ctx.get("experiment_name")
    force_new_experiment = project is not None and project != current_project

    # Decide which project to use
    project_to_use: Optional[str]
    if project:
        console.print(f"Setting project to '{project}'")
        project_to_use = project
    elif not current_project:
        console.print("No active project, creating a new one")
        project_to_use = project
    else:
        console.print(f"Keeping current project '{current_project}'")
        project_to_use = current_project
    set_new_project(ctx, project_to_use)

    # Decide which experiment to use
    experiment_to_use: Optional[str]
    if experiment:
        console.print(f"Setting experiment to '{experiment}'")
        experiment_to_use = experiment
    elif not current_experiment or force_new_experiment:
        console.print("No active experiment, creating a new one")
        experiment_to_use = experiment
    else:
        console.print(f"Keeping current experiment '{current_experiment}'")
        experiment_to_use = current_experiment
    set_new_experiment(ctx, experiment_to_use)

    write_ctx(ctx)

    console.print(f"[green]✓ Project:[/] {ctx['project_name']}")
    console.print(f"[green]✓ Experiment:[/] {ctx['experiment_name']}")
    console.print(
        f"See your results: {to_experiment_url(ctx['project_id'], ctx['experiment_id'])}"
    )


@init_cli.command("show")
def show_command():
    """Print active project/experiment IDs and names."""

    # pylint: disable=import-outside-toplevel
    from embedl_hub.cli.utils import assert_api_config
    from embedl_hub.core.context import read_embedl_hub_context
    from embedl_hub.core.hub_logging import console
    # pylint: enable=import-outside-toplevel

    assert_api_config()
    ctx = read_embedl_hub_context()

    if not ctx:
        console.print("[red]✗[/] No project or experiment initialized.")
        console.print(
            "Run `embedl-hub init` to create a new project and experiment."
        )
        return

    table = Table(title=".embedl_hub_ctx", show_lines=True, show_header=False)
    for k in (
        "project_id",
        "project_name",
        "experiment_id",
        "experiment_name",
    ):
        table.add_row(k, ctx.get(k, "—"))
    console.print(table)
