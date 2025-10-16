# Copyright (C) 2025 Embedl AB

"""Utility functions for tracking experiments and runs."""

from contextlib import contextmanager

from embedl_hub.core.context import read_embedl_hub_context
from embedl_hub.core.hub_logging import console
from embedl_hub.tracking import (
    RunType,
    set_experiment,
    set_project,
    start_run,
)
from embedl_hub.tracking.utils import (
    timestamp_id,
    to_run_url,
)


def set_new_project(ctx: dict, project: str | None = None) -> None:
    """Set a new project in the context dict, using the given name or a generated one."""
    project_name = project or timestamp_id("project")
    project_ctx = set_project(project_name)
    ctx["project_id"] = project_ctx.id
    ctx["project_name"] = project_ctx.name


def set_new_experiment(ctx: dict, experiment: str | None = None) -> None:
    """Set a new experiment in the context dict, using the given name or a generated one."""
    experiment_name = experiment or timestamp_id("experiment")
    experiment_ctx = set_experiment(experiment_name)
    ctx["experiment_id"] = experiment_ctx.id
    ctx["experiment_name"] = experiment_ctx.name


def _embed_run_hyperlink(run_url: str, text: str) -> str:
    """Return a hyperlink string if the terminal supports it."""
    return (
        f"[blue][link={run_url}]{text}[/link][/]"
        if console.is_terminal
        else run_url
    )


@contextmanager
def experiment_context(
    project_name: str, experiment_name: str, run_type: RunType
):
    """
    Context manager for managing the current experiment context.
    """
    try:
        project = set_project(project_name)
        experiment = set_experiment(experiment_name)

        console.log(f"Running command with project name: {project_name}")
        console.log(f"Running command with experiment name: {experiment_name}")
        with start_run(type=run_type) as run:
            run_url = to_run_url(
                project_id=project.id,
                experiment_id=experiment.id,
                run_id=run.id,
            )
            console.log(
                f"Track your progress {_embed_run_hyperlink(run_url, 'here')}."
            )
            yield
            console.log(
                f"View results {_embed_run_hyperlink(run_url, 'here')}"
            )
    finally:
        pass
