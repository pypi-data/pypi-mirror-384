# Copyright (C) 2025 Embedl AB

"""
Functionality for handling the Qualcomm AI Hub communication and device management.
"""

import qai_hub as hub
from rich.table import Table

from embedl_hub.core.hub_logging import console


def print_device_table():
    """Print a table of available devices on the Qualcomm AI Hub."""
    table = Table(title="Embedl Hub devices")
    table.add_column("Name", style="cyan")
    table.add_column("Cloud")
    table.add_column("OS")
    table.add_column("Chipset / Attrs", overflow="fold")
    devices = [
        (
            d.name,
            "qai_hub",
            d.os or "—",
            ", ".join(a for a in d.attributes if "chipset" in a) or "—"
        )
        for d in hub.get_devices()
    ]
    for row in devices:
        table.add_row(*row)
    console.print(table)


def create_device(device_name: str) -> hub.Device:
    """
    Create a device object from the given device name.

    Args:
        device (str): The name of the device.

    Returns:
        hub.Device: The created device object.
    """
    all_device_names = [d.name for d in hub.get_devices()]
    if device_name not in all_device_names:
        raise ValueError(
            f"Device name '{device_name}' not recognized. "
            "Use `embedl-hub list-devices` to see available devices."
        )
    return hub.Device(device_name)
