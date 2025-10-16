# Copyright (C) 2025 Embedl AB

"""
CLI command to benchmark a model's performance on a device.

This command profiles the latency of a compiled model on a specified device
and saves the results in JSON format. Both a summary and a full profile
are generated and saved to the specified output directory. The full profile
includes detailed performance metrics useful for debugging.
"""

import json
from datetime import datetime
from pathlib import Path

import typer

# All other embedl_hub imports should be done inside the function.
from embedl_hub.cli.helper import DEVICE_HELPER

benchmark_cli = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
)


@benchmark_cli.command("benchmark")
def benchmark_command(
    model: Path = typer.Option(
        ...,
        "-m",
        "--model",
        help="Path to a compiled model file (.tflite, .onnx, or .bin), or "
        "to a directory containing an ONNX model and its data files.",
        show_default=False,
    ),
    device: str = typer.Option(
        ..., "-d", "--device", help=DEVICE_HELPER, show_default=False
    ),
    output_dir: Path = typer.Option(
        None, "--output-dir", "-o", help="Output folder for benchmark JSONs"
    ),
):
    """Benchmark compiled model on device and measure it's performance.

    Examples:
    ---------
    Benchmark a .tflite model on Samsung Galaxy S25 and save results to
    the default benchmarks folder:

        $ embedl-hub benchmark -m my_model.tflite -d "Samsung Galaxy S25"

    Benchmark an .onnx model on Samsung Galaxy 8 Elite QRD and save
    results to a custom output directory:

        $ embedl-hub benchmark -m my_model.onnx -d "Samsung Galaxy 8 Elite QRD" -o results/

    """

    # pylint: disable=import-outside-toplevel
    from embedl_hub.cli.utils import assert_api_config
    from embedl_hub.core.benchmark import (
        ProfileError,
        print_profile_summary,
        profile_model,
    )
    from embedl_hub.core.context import require_embedl_hub_context
    from embedl_hub.core.hub_logging import console
    # pylint: enable=import-outside-toplevel

    assert_api_config()
    ctx = require_embedl_hub_context()

    console.log(f"profiling {model.name} on {device} using Qualcomm AI Hub")
    try:
        summary, full = profile_model(
            model,
            device,
            project_name=ctx["project_name"],
            experiment_name=ctx["experiment_name"],
        )
    except (ValueError, ProfileError) as e:
        console.print(f"[red]✗ profiling failed:[/] {e}")
        raise typer.Exit(1)
    print_profile_summary(summary)

    if output_dir is None:
        outdir = Path("benchmarks")
    else:
        outdir = Path(output_dir)
    outdir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = outdir / f"{model.stem}_{ts}.json"
    full_path = outdir / f"{model.stem}_{ts}.full.json"

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    console.print(f"[green]✓ Saved benchmark summary to:[/] {summary_path}")

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(full, f, indent=2)
    console.print(
        f"[green]✓ Saved full Qualcomm AI Hub benchmark to:[/] {full_path}"
    )
