# Copyright (C) 2025 Embedl AB

"""
embedl-hub compile - send an model to Qualcomm AI Hub, retrieve a
device-specific binary (.tflite for tflite, .bin for qnn, or .onnx for onnxruntime).
"""

from pathlib import Path

import typer

# All other embedl_hub imports should be done inside the function.
from embedl_hub.cli.helper import (
    DEVICE_HELPER,
    OUTPUT_FILE_HELPER,
    SIZE_HELPER,
)

compile_cli = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
)


@compile_cli.command("compile")
def compile_command(
    model: Path = typer.Option(
        ...,
        "-m",
        "--model",
        help="Path to the TorchScript model file, ONNX model file, or to a directory "
        "containing the ONNX model and any associated data files, to be compiled.",
        show_default=False,
    ),
    device: str = typer.Option(
        ...,
        "-d",
        "--device",
        help=DEVICE_HELPER,
        show_default=False,
    ),
    size: str = typer.Option(
        ...,
        "--size",
        "-s",
        help=SIZE_HELPER,
        show_default=False,
    ),
    runtime: str = typer.Option(
        ...,
        "-r",
        "--runtime",
        help="Runtime backend for compilation: tflite, qnn, or onnx.",
    ),
    quantize_io: bool = typer.Option(
        False,
        "--quantize-io",
        help="Quantize input and output tensors. "
        "Improves performance on platforms that support quantized I/O.",
        show_default=True,
    ),
    output_file: str = typer.Option(
        None,
        "-o",
        "--output-file",
        help=OUTPUT_FILE_HELPER,
        show_default=False,
    ),
):
    """
    Compile a model into a device ready binary using Qualcomm AI Hub.
    Qualcomm AI Hub may return a zip file containing multiple files.

    Required arguments:
        --model
        --size
        --device
        --runtime

    Examples
    --------

    Compile the ONNX model `fp32_model.onnx` with input size 1x3x224x224 for the Samsung Galaxy S24 using the tflite runtime:

        $ embedl-hub compile -m fp32_model.onnx  --size 1,3,224,224 -d "Samsung Galaxy S24" -r tflite

    Compile the TorchScript model `model.pt` with input size 1x3x224x224
    for the Samsung Galaxy S24, and save it to `./my_outputs/model.onnx`:

        $ embedl-hub compile -m model.pt  -r onnx --size 1,3,224,224 --device "Samsung Galaxy S24" -o ./my_outputs/model.onnx

    """

    # pylint: disable=import-outside-toplevel
    from embedl_hub.cli.utils import assert_api_config, prepare_input_size
    from embedl_hub.core.compile import (
        CompileError,
        CompileResult,
        compile_model,
    )
    from embedl_hub.core.context import require_embedl_hub_context
    from embedl_hub.core.hub_logging import console
    # pylint: enable=import-outside-toplevel

    assert_api_config()
    ctx = require_embedl_hub_context()

    if not model:
        raise ValueError("Please specify a model to compile using --model")
    if not size:
        raise ValueError(
            "Please specify input size using --size, e.g. 1,3,224,224"
        )

    if not output_file:
        output_file = model.with_suffix(f".{runtime}").as_posix()
        console.print(
            f"[yellow]No output file specified, using {output_file}[/]"
        )
    input_size = prepare_input_size(size)
    try:
        res: CompileResult = compile_model(
            project_name=ctx["project_name"],
            experiment_name=ctx["experiment_name"],
            model_path=model,
            device=device,
            runtime=runtime,
            quantize_io=quantize_io,
            output_file=output_file,
            input_size=input_size,
        )
        console.print(f"[green]✓ Compiled model for {res.device}[/]")

        # TODO: upload artifacts / metrics to web
    except (CompileError, ValueError) as error:
        console.print(f"[red]✗ {error}[/]")
        raise typer.Exit(1)
