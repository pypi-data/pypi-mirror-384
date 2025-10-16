# Copyright (C) 2025 Embedl AB
"""
On-device profiling of models via Qualcomm AI Hub.
This module provides functionality to profile model latency and memory usage
on a target device, returning detailed execution statistics.
"""

from numbers import Number
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Tuple

import qai_hub as hub
import tabulate

from embedl_hub.core.hardware.qualcomm_ai_hub import create_device
from embedl_hub.core.hub_logging import console
from embedl_hub.core.onnx_utils import maybe_package_onnx_folder_to_file
from embedl_hub.core.qai_hub_utils import (
    get_global_qai_hub_client,
    get_job_result,
    parse_runtime_info,
)
from embedl_hub.core.tracking_utils import experiment_context
from embedl_hub.tracking import RunType, log_metric, log_param


class ProfileError(RuntimeError):
    """Raised when Qualcomm AI Hub profile job fails or times out."""


def _to_ms(val: Number):
    "Always return milliseconds as float, or None if not available."
    return float(val) / 1000.0 if val is not None else None


def _count_layers_by_unit(execution_detail: List[dict]) -> Dict[str, int]:
    """Count layers by compute unit (CPU, GPU, NPU) from execution detail."""
    counts = {"CPU": 0, "GPU": 0, "NPU": 0}
    for layer in execution_detail:
        unit = layer.get("compute_unit")
        if unit in counts:
            counts[unit] += 1
    return counts


def _to_megabytes(val: Number):
    "Convert bytes to megabytes as float, or None if not available."
    return float(val) / (1024 * 1024) if val is not None else None


def _log_metrics(summary: dict) -> None:
    """Log profiling metrics to the tracking system."""
    log_metric(
        "$latency",
        summary.get("mean_ms"),
    )
    log_metric(
        "$peak_memory_usage",
        summary.get("peak_memory_usage_mb"),
    )
    for unit, count in summary.get("layers_by_unit", {}).items():
        log_metric(
            f"$num_layers_{unit.lower()}",
            count,
        )


def _log_layers(details: list) -> None:
    """Log layer information to the tracking system."""

    for idx, layer in enumerate(details):
        log_param(f"$layer_name_{idx}", layer["name"])
        log_param(f"$layer_type_{idx}", layer["type"])
        log_param(f"$layer_compute_unit_{idx}", layer["compute_unit"])
        log_metric("$latency_per_layer", layer["execution_time"], idx)
        log_metric("$cycles_per_layer", layer["execution_cycles"], idx)


def _collect_top_n_layer_times(
    execution_detail, num: int
) -> List[Tuple[float, str, str]]:
    """
    Collect layer execution times for the top n slowest layers from the profile detail.

    Returns a list of tuples (time_ms, layer_name, layer_type) in descending order of time.
    """
    all_layer_times = [
        (_to_ms(layer["execution_time"]), layer["name"], layer["type"])
        for layer in execution_detail
    ]
    return sorted(all_layer_times, reverse=True)[:num]


def _make_layer_names_unique(execution_detail: List[dict]) -> None:
    """Modify execution_detail in-place to ensure all layer names are unique."""

    class LayerNamer:
        """Helper class to generate unique layer names."""

        def __init__(self, layer_details: dict):
            self.all_names_unique = True
            self.seen_names = set()
            for layer in layer_details:
                name = layer.get("name")
                if name in self.seen_names or name == "":
                    self.all_names_unique = False
                    break
                self.seen_names.add(name)

            self.counts: Dict[str, int] = {}

        def __call__(self, layer_name: str, layer_type: str) -> str:
            if self.all_names_unique and layer_name:
                return layer_name
            count = self.counts.get(layer_type, 0)
            new_layer_name = f"{layer_type.lower()}_{count}"
            self.counts[layer_type] = count + 1
            return new_layer_name

    layer_namer = LayerNamer(execution_detail)

    for layer in execution_detail:
        layer["name"] = layer_namer(layer["name"], layer["type"])


def profile_model(
    model: Path,
    device: str,
    project_name: Optional[str] = None,
    experiment_name: Optional[str] = None,
) -> tuple[dict, dict]:
    """
    Profile model latency on a target device using Qualcomm AI Hub.
    Returns (summary_dict, full_profile_dict).
    Raises ProfileError on failure.
    """
    with experiment_context(
        project_name=project_name,
        experiment_name=experiment_name,
        run_type=RunType.BENCHMARK,
    ):
        hub_device = create_device(device)
        log_param("$device", device)

        with TemporaryDirectory() as tmpdir:
            model = maybe_package_onnx_folder_to_file(model, tmpdir)
            try:
                job = hub.submit_profile_job(
                    model=model,
                    device=hub_device,
                )
            except Exception as exc:
                raise ProfileError("Failed to submit profile job.") from exc

        log_param("$qai_hub_job_id", job.job_id)

        try:
            prof = job.download_profile()
        except Exception as exc:
            raise ProfileError("Failed to download profile.") from exc

        try:
            job_result = get_job_result(
                job.job_id, get_global_qai_hub_client().config
            )
            runtime = parse_runtime_info(job_result)
        except RuntimeError as exc:
            raise ProfileError(
                "Failed to extract runtime info from job."
            ) from exc
        log_param("$runtime", runtime)

        summary = prof.get("execution_summary", {})
        execution_detail = prof.get("execution_detail", [])
        _make_layer_names_unique(execution_detail)
        layer_counts = _count_layers_by_unit(execution_detail)
        layer_times = _collect_top_n_layer_times(execution_detail, 5)
        summary_dict = {
            "mean_ms": _to_ms(summary.get("estimated_inference_time")),
            "peak_memory_usage_mb": _to_megabytes(
                summary.get("estimated_inference_peak_memory")
            ),
            "layer_times": layer_times,
            "layers": prof.get("layers", []),
            "layers_by_unit": layer_counts,
        }
        _log_metrics(summary_dict)

        _log_layers(execution_detail)
        return summary_dict, prof


def _make_layer_times_table(layer_times: list) -> str:
    """Create a pretty-printed table of layer execution times as a string, with a title."""
    headers = ["Name", "Type", "Time (ms)"]
    rows = [
        [name, layer_type, f"{time:.2f}" if time is not None else "—"]
        for time, name, layer_type in layer_times
    ]
    title = f"Layer execution times (Top {len(layer_times)})"
    table = tabulate.tabulate(rows, headers=headers, tablefmt="github")
    return f"\n{title}\n{table}\n"


def print_profile_summary(summary: dict) -> None:
    """Print latency summary to the user in a consistent way."""
    if summary.get("mean_ms") is not None:
        console.print(f"[green]✓ Mean latency:[/] {summary['mean_ms']:.2f} ms")
    if summary.get("peak_memory_usage_mb") is not None:
        console.print(
            f"[green]✓ Peak memory usage:[/] {summary['peak_memory_usage_mb']:.2f} MB"
        )
    if summary.get("layers_by_unit"):
        units = summary["layers_by_unit"]
        console.print(
            f"[green]✓ Layers by compute unit:[/] NPU={units['NPU']}, GPU={units['GPU']}, CPU={units['CPU']}"
        )
    if summary.get("layer_times"):
        table = _make_layer_times_table(summary["layer_times"])
        console.print(table)
