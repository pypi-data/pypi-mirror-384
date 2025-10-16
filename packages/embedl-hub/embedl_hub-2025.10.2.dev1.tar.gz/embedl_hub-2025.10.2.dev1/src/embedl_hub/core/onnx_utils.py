# Copyright (C) 2025 Embedl AB

"""Module for ONNX related helper functions."""

from pathlib import Path
from typing import Union

import onnx

from embedl_hub.core.hub_logging import console


def load_onnx_model(model_path: Path) -> onnx.ModelProto:
    """Load an ONNX model from a file or directory.
    If a directory is provided, it expects exactly one ONNX file inside.
    Args:
        model_path: Path to the ONNX model file or directory.
    Returns:
        Loaded ONNX model.
    Raises:
        ValueError: If the model path is invalid or does not contain a valid ONNX file.
    """

    if model_path.is_file():
        if model_path.suffix.lower() != ".onnx":
            raise ValueError(f"Expected a .onnx file, got: {model_path.name}")
        return onnx.load(model_path)
    if not model_path.is_dir():
        raise ValueError(
            f"Model path must be a file or directory: {model_path}"
        )
    onnx_files = sorted([p for p in model_path.glob("*.onnx") if p.is_file()])
    if not len(onnx_files) == 1:
        raise ValueError(
            f"Expected exactly one ONNX file in directory, found: {len(onnx_files)}"
        )
    return onnx.load(onnx_files[0])


def maybe_package_onnx_folder_to_file(
    model_path: Path, dest_folder: Union[Path, str]
) -> Path:
    """If model_path is a directory, repackage the ONNX model into a single .onnx file.
    Returns the path to the .onnx file (either the original file or a new file inside dest_folder).
    """
    if model_path.is_dir():
        console.log("Directory model detected. Looking for ONNX file...")
        # Repackage directory onnx model into a single .onnx file
        onnx_model = load_onnx_model(model_path)
        new_onnx_path = (
            Path(dest_folder) / model_path.with_suffix(".onnx").name
        )
        onnx.save(onnx_model, new_onnx_path)
        console.log("ONNX model found and validated.")
        return new_onnx_path
    return model_path
