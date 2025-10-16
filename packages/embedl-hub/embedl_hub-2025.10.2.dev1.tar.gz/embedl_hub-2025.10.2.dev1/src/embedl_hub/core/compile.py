# Copyright (C) 2025 Embedl AB
"""
Core compile logic for the embedl-hub CLI.

Handles submitting models to Qualcomm AI Hub for compilation and saving the resulting artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Tuple, Union

import qai_hub as hub

from embedl_hub.core.hardware.qualcomm_ai_hub import create_device
from embedl_hub.core.onnx_utils import maybe_package_onnx_folder_to_file
from embedl_hub.core.qai_hub_utils import (
    get_global_qai_hub_client,
    get_job_result,
    parse_runtime_info,
)
from embedl_hub.core.tracking_utils import experiment_context
from embedl_hub.tracking import RunType, log_param


class CompileError(RuntimeError):
    """Raised when Qualcomm AI Hub compile job fails or times out."""


@dataclass
class CompileResult:
    """Result of a successful compile job."""

    model_path: Path  # local .tflite, .bin, or .onnx after compile
    job_id: str
    device: str


def compile_model(
    project_name: str,
    experiment_name: str,
    model_path: Path | str,
    device: str,
    runtime: str,
    quantize_io: bool = False,
    output_file: Optional[Union[Path, str]] = None,
    input_size: Tuple[int, ...] | None = None,
) -> CompileResult:
    """
    Submit an ONNX model to Qualcomm AI Hub and retrieve the compiled artifact.

    Args:
        model_path: Path to TorchScript/ONNX (INT8 or FP32).
        device: Device nickname, e.g. 'Samsung Galaxy S24'.
        runtime: 'tflite' | 'qnn' | 'onnx'
        quantize_io: Add --quantize_io to options.
        output_file: Compiled model filename. File ending added automatically if not specified.
        input_size: Input size as (dim0, dim1, ...) tuple, e.g. (1, 3, 224, 224).

    Returns:
        CompileResult with local path to compiled model.
    """

    model_path = Path(model_path)
    if not model_path.exists():
        raise ValueError(f"Model not found: {model_path}")

    with experiment_context(project_name, experiment_name, RunType.COMPILE):
        with TemporaryDirectory() as tmpdir:
            model_path = maybe_package_onnx_folder_to_file(model_path, tmpdir)
            return _compile_model(
                model_file=model_path,
                device=device,
                runtime=runtime,
                quantize_io=quantize_io,
                output_file=output_file,
                input_size=input_size,
            )


def _compile_model(
    model_file: Path,
    device: str,
    runtime: str = "tflite",
    quantize_io: bool = False,
    output_file: Optional[Union[Path, str]] = None,
    input_size: Tuple[int, ...] | None = None,
) -> CompileResult:
    """
    Submit a model to Qualcomm AI Hub and retrieve the compiled artifact.

    Args:
        model_file: Path to the model.
        device: Device nickname, e.g. 'Samsung Galaxy S24'.
        runtime: 'tflite' | 'qnn' | 'onnx'
        quantize_io: Add --quantize_io to options.
        output_file: Compiled model filename. File ending added automatically if not specified.
        input_size: Input size as tuple, e.g. (1, 3, 224, 224).

    Returns:
        CompileResult with local path to compiled model.

    """
    hub_device = create_device(device)

    log_param("$device", device)

    opts = f"--target_runtime {runtime}"
    if quantize_io:
        opts += " --quantize_io"

    input_specs = {"image": input_size} if input_size else None

    try:
        job = hub.submit_compile_job(
            model=model_file.as_posix(),
            device=hub_device,
            options=opts,
            input_specs=input_specs,
        )
    except Exception as error:
        raise CompileError("Failed to submit compile job.") from error

    log_param("$qai_hub_job_id", job.job_id)

    try:
        compiled_model = job.get_target_model()
    except Exception as error:
        raise CompileError(
            "Failed to download compiled model from Qualcomm AI Hub."
        ) from error
    local_path = _save_compiled_model(compiled_model, output_file)

    if "qnn" in runtime:
        # Compile jobs with --target-runtime qnn_dlc, qnn_lib_aarch64_android or
        # qnn_context_binary don't expose runtime info in the job result
        logged_runtime = "QNN"
    else:
        try:
            job_result = get_job_result(
                job.job_id, get_global_qai_hub_client().config
            )
            logged_runtime = parse_runtime_info(job_result)
        except RuntimeError as error:
            raise CompileError("Failed to parse runtime info.") from error
    log_param("$runtime", logged_runtime)

    return CompileResult(
        model_path=local_path,
        job_id=job.job_id,
        device=device,
    )


def _save_compiled_model(
    compiled: "hub.Model", output_file: Optional[Union[Path, str]] = None
) -> Path:
    """
    Save the compiled artifact to a user-specified location or to the root
    directory with the name provided by Qualcomm AI Hub.

    Returns:
        Path to the saved model file.
    """
    model_filename = Path(compiled.name)
    if output_file is None:
        dst = Path.cwd() / model_filename
    else:
        output_path = Path(output_file)
        if output_path.is_dir() or str(output_file).endswith(("/", "\\")):
            dst = output_path / model_filename
        else:
            dst = output_path

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst = dst.with_suffix("")
    dst = compiled.download(str(dst))
    return dst
