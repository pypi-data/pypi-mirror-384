# Copyright (C) 2025 Embedl AB

"""Module for measuring PSNR between float and quantized ONNX models."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Tuple

import numpy as np
import onnx
import onnxruntime as ort
from onnx import ModelProto, NodeProto, TensorProto, helper, numpy_helper

from embedl_hub.thirdparty.aimet.utils import compute_psnr


def load_model(path: str) -> ModelProto:
    """Loads an ONNX model, including external data."""
    return onnx.load(path, load_external_data=True)


def save_model(model: ModelProto, out_path: Path):
    """Saves an ONNX model, creating the directory if it doesn't exist."""
    onnx.save_model(model, out_path)


def _infer_model_shapes(model: ModelProto) -> ModelProto:
    """Infers shapes and types for all tensors in the model."""
    return onnx.shape_inference.infer_shapes(
        model, strict_mode=True, data_prop=True
    )


def _get_value_info_index(
    model: ModelProto,
) -> Dict[str, Tuple[int, List[int]]]:
    """Creates a dictionary mapping tensor names to their type and shape."""
    index = {}

    def add_value_info_to_index(value_info):
        tensor_type = value_info.type.tensor_type
        if tensor_type and tensor_type.elem_type != 0:
            dims = []
            if tensor_type.HasField("shape"):
                for dim in tensor_type.shape.dim:
                    dims.append(
                        dim.dim_value if dim.HasField("dim_value") else None
                    )
            else:
                dims = None
            index[value_info.name] = (tensor_type.elem_type, dims)

    for value_info in (
        list(model.graph.input)
        + list(model.graph.output)
        + list(model.graph.value_info)
    ):
        add_value_info_to_index(value_info)
    return index


def _make_tensors_outputs(model: ModelProto, tensor_names: List[str]):
    """
    Adds the given tensors to the model's output list.
    It infers shapes and types to create the necessary ValueInfoProto.
    """
    inferred_model = ModelProto()
    inferred_model.CopyFrom(model)
    try:
        inferred_model = _infer_model_shapes(inferred_model)
    except Exception:
        # Shape inference may fail, but we can try to proceed.
        pass

    value_info_index = _get_value_info_index(inferred_model)
    existing_outputs = {o.name for o in model.graph.output}

    for tensor_name in tensor_names:
        if tensor_name in existing_outputs:
            continue

        if tensor_name in value_info_index:
            elem_type, dims = value_info_index[tensor_name]
            value_info = helper.make_tensor_value_info(
                tensor_name, elem_type, dims if dims is not None else None
            )
        else:
            # Fallback for tensors without inferred types (common for intermediate tensors)
            value_info = helper.make_tensor_value_info(
                tensor_name, TensorProto.FLOAT, None
            )
        model.graph.output.append(value_info)


def run_inference(
    model_path: Path, feed_dict: Dict[str, np.ndarray]
) -> Dict[str, np.ndarray]:
    """
    Runs inference on an ONNX model using ONNX Runtime.
    """
    session = ort.InferenceSession(
        model_path, providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
    )

    # If the model has a single input, auto-map the input name.
    if len(feed_dict) == 1 and len(session.get_inputs()) == 1:
        input_tensor = next(iter(feed_dict.values()))
        input_name = session.get_inputs()[0].name
        feed_dict = {input_name: input_tensor}

    # Validate input names
    session_input_names = {i.name for i in session.get_inputs()}
    unknown_inputs = [k for k in feed_dict if k not in session_input_names]
    if unknown_inputs:
        raise ValueError(
            f"Unknown input(s) {unknown_inputs}. Available: {sorted(session_input_names)}"
        )

    output_names = [o.name for o in session.get_outputs()]
    outputs = session.run(output_names, feed_dict)
    return dict(zip(output_names, outputs))


def get_initializer_dict(model: ModelProto) -> Dict[str, np.ndarray]:
    """Returns a dictionary of model initializers."""
    return {
        init.name: numpy_helper.to_array(init)
        for init in model.graph.initializer
    }


# --------------------
# Graph Analysis
# --------------------
def get_all_node_output_names(model: ModelProto) -> List[str]:
    """Returns a list of all unique node output tensor names in the model."""
    all_outputs = []
    for node in model.graph.node:
        all_outputs.extend([o for o in node.output if o])

    # De-duplicate while preserving order
    seen = set()
    unique_outputs = []
    for tensor_name in all_outputs:
        if tensor_name not in seen:
            seen.add(tensor_name)
            unique_outputs.append(tensor_name)
    return unique_outputs


def get_post_quantization_map(model: ModelProto) -> Dict[str, dict]:
    """
    Creates a map of tensors that are inputs to QuantizeLinear nodes.

    For each tensor `T` that is consumed by a `QuantizeLinear` node, this function
    records the output name of the `QuantizeLinear` node, and the scale and zero-point
    values used for quantization.

    Returns:
        A dictionary mapping a tensor name to its quantization info:
        {
            "tensor_name": {
                "ql_out": <output_name_of_quantize_linear>,
                "scale": <scale_value>,
                "zp": <zero_point_value>
            }
        }
    """
    initializers = get_initializer_dict(model)
    consumers: Dict[str, List[NodeProto]] = {}
    for node in model.graph.node:
        for input_name in node.input:
            consumers.setdefault(input_name, []).append(node)

    post_quantization_map = {}
    for tensor_name, consumer_nodes in consumers.items():
        quantize_linear_nodes = [
            node for node in consumer_nodes if node.op_type == "QuantizeLinear"
        ]
        if not quantize_linear_nodes:
            continue

        quant_node = quantize_linear_nodes[0]
        if len(quant_node.input) >= 3:
            scale_name, zp_name = quant_node.input[1], quant_node.input[2]
            if scale_name in initializers and zp_name in initializers:
                post_quantization_map[tensor_name] = {
                    "ql_out": quant_node.output[0],
                    "scale": initializers[scale_name].astype(np.float32),
                    "zp": initializers[zp_name],
                }
    return post_quantization_map


def add_debug_outputs(
    model: ModelProto, tensor_names: List[str]
) -> ModelProto:
    """Clones a model and adds the specified tensors to its outputs."""
    cloned_model = ModelProto()
    cloned_model.CopyFrom(model)
    _make_tensors_outputs(cloned_model, tensor_names)
    if not cloned_model.opset_import:  # Safety check
        cloned_model.opset_import.extend(model.opset_import)
    return cloned_model


def dequantize_tensor(
    quantized_tensor: np.ndarray,
    scale: np.ndarray,
    zero_point: np.ndarray,
    original_ndim: int,
) -> np.ndarray:
    """Dequantizes a tensor using its scale and zero-point."""
    if np.size(scale) == 1 and np.size(zero_point) == 1:
        return (
            quantized_tensor.astype(np.float32) - float(zero_point)
        ) * float(scale)

    # Handle per-channel quantization (common in NCHW format)
    if original_ndim >= 2 and (
        scale.size == quantized_tensor.shape[1]
        or np.size(zero_point) == quantized_tensor.shape[1]
    ):
        # Reshape scale and zero-point for broadcasting
        broadcast_shape = (1, -1) + (1,) * (original_ndim - 2)
        scale_b = np.array(scale, dtype=np.float32).reshape(broadcast_shape)
        zp_b = np.array(zero_point, dtype=np.float32).reshape(broadcast_shape)
        return (quantized_tensor.astype(np.float32) - zp_b) * scale_b

    # Fallback for other cases
    return (
        quantized_tensor.astype(np.float32)
        - np.array(zero_point, dtype=np.float32)
    ) * np.array(scale, dtype=np.float32)


def _prepare_debug_model(
    model_path: str,
    tmp_folder: Path,
    extra_output_names: Optional[List[str]] = None,
) -> Tuple[Path, List[str]]:
    """Prepares a model for debug inference by adding all tensor outputs."""
    model = load_model(model_path)
    tensor_names = get_all_node_output_names(model)
    all_outputs = list(set(tensor_names + (extra_output_names or [])))
    debug_model = add_debug_outputs(model, all_outputs)
    debug_model_path = tmp_folder / f"{Path(model_path).stem}_debug.onnx"
    save_model(debug_model, debug_model_path)
    return debug_model_path, tensor_names


def _calculate_psnr_for_tensors(
    float_tensor_names: List[str],
    float_outputs: Dict[str, np.ndarray],
    qdq_outputs: Dict[str, np.ndarray],
    post_quantization_map: Dict[str, dict],
) -> List[dict]:
    """Calculates PSNR for corresponding float and dequantized tensors."""
    results = []
    for tensor_name in float_tensor_names:
        if (
            tensor_name not in float_outputs
            or tensor_name not in post_quantization_map
        ):
            continue

        quant_info = post_quantization_map[tensor_name]
        ql_out_name = quant_info["ql_out"]
        if ql_out_name not in qdq_outputs:
            continue

        float_tensor = float_outputs[tensor_name]
        quantized_tensor = qdq_outputs[ql_out_name]
        scale, zero_point = quant_info["scale"], quant_info["zp"]
        dequantized_tensor = dequantize_tensor(
            quantized_tensor, scale, zero_point, float_tensor.ndim
        )

        if float_tensor.shape != dequantized_tensor.shape:
            continue

        results.append(
            {
                "layer": tensor_name,
                "shape": tuple(float_tensor.shape),
                "psnr": float(compute_psnr(float_tensor, dequantized_tensor)),
            }
        )
    return results


# --------------------
# Main Comparison Logic
# --------------------
def compare_models(
    float_model_path: str,
    qdq_model_path: str,
    inputs: Dict[str, np.ndarray],
) -> Tuple[List[dict], List[dict]]:
    """
    Compares the layer and model outputs of a float model and a QDQ model.

    This function calculates the PSNR between the float tensor output of each layer
    and the dequantized output of the corresponding layer in the QDQ model. It
    also computes the PSNR for the final model outputs.

    Returns:
        A tuple containing:
        - A list of dictionaries for layer-wise PSNR results.
        - A list of dictionaries for model output PSNR results.
    """
    float_model = load_model(float_model_path)
    qdq_model = load_model(qdq_model_path)
    post_quantization_map = get_post_quantization_map(qdq_model)
    extra_qdq_outputs = [
        info["ql_out"] for info in post_quantization_map.values()
    ]

    with TemporaryDirectory() as tmpdir:
        tmp_folder = Path(tmpdir)

        float_debug_path, float_tensor_names = _prepare_debug_model(
            float_model_path, tmp_folder
        )
        qdq_debug_path, _ = _prepare_debug_model(
            qdq_model_path, tmp_folder, extra_qdq_outputs
        )

        float_outputs = run_inference(float_debug_path, inputs)
        qdq_outputs = run_inference(qdq_debug_path, inputs)

    # Calculate PSNR for intermediate layers
    layer_results = _calculate_psnr_for_tensors(
        float_tensor_names, float_outputs, qdq_outputs, post_quantization_map
    )

    # Calculate PSNR for model outputs
    float_output_names = [o.name for o in float_model.graph.output]
    qdq_output_names = [o.name for o in qdq_model.graph.output]
    output_results = []

    for float_out_name, qdq_out_name in zip(
        float_output_names, qdq_output_names
    ):
        if float_out_name in float_outputs and qdq_out_name in qdq_outputs:
            float_tensor = float_outputs[float_out_name]
            qdq_tensor = qdq_outputs[qdq_out_name]

            if float_tensor.shape != qdq_tensor.shape:
                output_results.append(
                    {
                        "layer": f"{float_out_name} vs {qdq_out_name}",
                        "shape": "NA",
                        "psnr": None,
                        "note": f"Shape mismatch: {float_tensor.shape} vs {qdq_tensor.shape}",
                    }
                )
                continue

            output_results.append(
                {
                    "layer": float_out_name,
                    "shape": tuple(float_tensor.shape),
                    "psnr": float(compute_psnr(float_tensor, qdq_tensor)),
                }
            )

    return layer_results, output_results


def print_comparison_results(title: str, results: List[dict]):
    """Prints the comparison results in a formatted table."""
    print(f"\n=== {title} ===")
    for result in results:
        shape = result["shape"]
        shape_str = str(shape) if isinstance(shape, tuple) else "NA"
        psnr_str = "NA" if result["psnr"] is None else f"{result['psnr']:.3f}"
        note = result.get("note", "")
        print(
            f"{result['layer']:<40} psnr={psnr_str:>8}  shape={shape_str}  {note}"
        )


def measure_psnr_between_models(
    float_model_path: str,
    qdq_model_path: str,
    calibration_data: Dict[str, List[np.ndarray]],
):
    """
    Measures and prints the PSNR between a float model and a QDQ model.
    It computes PSNR for both intermediate layer outputs and final model outputs.

    Args:
        float_model_path: Path to the float ONNX model.
        qdq_model_path: Path to the QDQ ONNX model.
        inputs: Dictionary of input tensors for inference.
        title: Title for the comparison results.
    """
    inputs = {
        k: np.concatenate(v, axis=0) if len(v) > 1 else v[0]
        for k, v in calibration_data.items()
    }
    layer_results, output_results = compare_models(
        float_model_path, qdq_model_path, inputs
    )
    print_comparison_results("Layerwise PSNR", layer_results)

    if output_results:
        print_comparison_results("Model Output PSNR", output_results)

    return layer_results, output_results
