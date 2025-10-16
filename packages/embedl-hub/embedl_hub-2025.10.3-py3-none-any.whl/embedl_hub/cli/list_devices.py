# Copyright (C) 2025 Embedl AB
"""
embedl-hub list-devices - List all available target devices for the commands
`compile`, `quantize` and `benchmark`.
"""

import typer

list_devices_cli = typer.Typer()


@list_devices_cli.command("list-devices")
def list_devices_command():
    """
    List all available target devices.

    A device name is used as input to the `--device` option
    in the commands `compile`, `quantize` and `benchmark`.
    """

    # pylint: disable=import-outside-toplevel
    from embedl_hub.core.hardware.qualcomm_ai_hub import print_device_table
    # pylint: enable=import-outside-toplevel

    print_device_table()
