# Copyright (C) 2025 Embedl AB

"""Utility functions for the Embedl Hub CLI."""

from typing import Any, Dict, Optional, Tuple

import typer

from embedl_hub.core.hub_logging import console
from embedl_hub.tracking import global_client


def remove_none_values(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys with None values from a dictionary."""
    return {key: val for key, val in input_dict.items() if val is not None}


def assert_api_config():
    """Assert that the API configuration can be accessed without error."""
    try:
        _ = global_client.api_config
    except RuntimeError as e:
        console.print(f"[red]✗[/] API configuration error: {e}")
        raise typer.Exit(1)


def prepare_input_size(size: Optional[str]) -> Optional[Tuple[int, ...]]:
    """Prepare the input size from a string in comma separated format."""
    if not size:
        return None
    try:
        sizes = tuple(map(int, size.split(",")))
    except ValueError as error:
        raise ValueError(
            "Invalid size format. Use dim0, dim1,..., e.g. 1,3,224,224"
        ) from error
    console.print(f"[yellow]Using input size: {size}[/]")
    return sizes
