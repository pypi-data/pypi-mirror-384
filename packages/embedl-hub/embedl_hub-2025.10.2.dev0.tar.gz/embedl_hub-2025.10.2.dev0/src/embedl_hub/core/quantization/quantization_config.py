# Copyright (C) 2025 Embedl AB

"""Configuration for quantizing models."""

from pathlib import Path
from typing import Optional

from embedl_hub.core.config import ExperimentConfig


class QuantizationConfig(ExperimentConfig):
    """Class for quantization configuration."""

    # User specific parameters
    model: Path
    data_path: Optional[Path]
    output_file: Path
    num_samples: int
