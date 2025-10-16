# Copyright (C) 2025 Embedl AB

"""
Module containing a unified set of helper texts for CLI commands.
"""

# To avoid slowing down the CLI, avoid imports in this file.

CONFIG_HELPER = (
    "Path to an optional YAML configuration file for advanced settings."
)
DEVICE_HELPER = (
    "Target device name for deployment. "
    "Use command `list-devices` to view all available options."
)
OUTPUT_FILE_HELPER = "Path to the output file or directory where the resulting model will be saved."
SIZE_HELPER = "Input image size in format HEIGHT,WIDTH (e.g., 224,224)."
