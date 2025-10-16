# Copyright (C) 2025 Embedl AB
"""
embedl-hub CLI

This is the main entry point for the Embedl-Hub command-line interface.
It provides commands for experiment tracking and on-device benchmarking
and verification.
"""

from importlib import metadata

import typer

from embedl_hub.cli.auth import auth_cli
from embedl_hub.cli.benchmark import benchmark_cli
from embedl_hub.cli.compile import compile_cli
from embedl_hub.cli.init import init_cli
from embedl_hub.cli.list_devices import list_devices_cli
from embedl_hub.cli.quantize import quantize_cli
from embedl_hub.core.hub_logging import console, setup_logging

app = typer.Typer(
    add_completion=True,
    rich_markup_mode="rich",
    help="[bold cyan]embedl-hub[/] end-to-end Edge-AI workflow CLI",
    no_args_is_help=True,
    # Disable local variables for security.
    # See https://typer.tiangolo.com/tutorial/exceptions/#disable-local-variables-for-security
    pretty_exceptions_show_locals=False,
)

# The order of these commands should be the expected order of calls,
# not alphabetical.
app.add_typer(auth_cli)
app.add_typer(init_cli)
app.add_typer(compile_cli)
app.add_typer(quantize_cli)
app.add_typer(benchmark_cli)
app.add_typer(list_devices_cli)


def _version_callback(value: bool):
    if value:
        console.print(f"embedl-hub {metadata.version('embedl-hub')}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Print embedl-hub version and exit.",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity (-v, -vv, -vvv).",
        show_default=False,
    ),
):
    """Main entry point for the embedl-hub CLI."""

    _ = version  # Mark as used to avoid unused argument warning
    setup_logging(verbose)
