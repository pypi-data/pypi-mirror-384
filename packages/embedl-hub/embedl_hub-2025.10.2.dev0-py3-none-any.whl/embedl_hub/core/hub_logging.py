# Copyright (C) 2025 Embedl AB

"""Shared Rich console and logging setup helpers for embedl-hub CLI.

Import ``console`` whenever you need to print user-facing output:

    from embedl_hub.cli.logging import console
    console.print("[green]✓ done[/]")

Call ``setup_logging(verbose)`` once at Typer app entry-point, passing the
``-v/--verbose`` count so that log levels map to WARNING/INFO/DEBUG/NOTSET.

"""

import logging
from typing import Sequence

from rich.console import Console
from rich.logging import RichHandler

__all__: Sequence[str] = ("console", "setup_logging")

# This is the single Console instance reused across the entire CLI
console: Console = Console()


def setup_logging(verbose: int = 0, *, force: bool = False) -> None:
    """Configure Rich-formatted logging.

    Parameters
    ----------
    verbose : int, default 0
        Verbosity count from ``-v/--verbose`` flag.
        0 → WARNING, 1 → INFO, 2 → DEBUG, ≥3 → NOTSET.
    force : bool, default False
        If True, re-configures logging even if already configured.
        Handy for unit tests that run the Typer app multiple times.
    """

    levels = [logging.WARNING, logging.INFO, logging.DEBUG, logging.NOTSET]
    level = levels[min(verbose, len(levels) - 1)]

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=console, markup=True, rich_tracebacks=True)
        ],
        force=force,
    )

    # Here we can silence 3rd party libraries if needed by adding them to the list of names below.
    if verbose == 0:
        name: str
        for name in ():
            logging.getLogger(name).setLevel(logging.WARNING)
