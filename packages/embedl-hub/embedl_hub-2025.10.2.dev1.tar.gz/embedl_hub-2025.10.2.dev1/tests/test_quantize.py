# Copyright (C) 2025 Embedl AB

"""Tests for the quantization module in the Embedl Hub SDK."""

from pathlib import Path

import numpy as np
import onnx
import pytest
from onnx import TensorProto, helper

from embedl_hub.core.quantization.quantization_config import QuantizationConfig
from embedl_hub.core.quantization.quantize import (
    _load_calibration_data,
    make_calibration_dataset,
)


def _create_onnx_model(model_path: Path, input_names: list[str]):
    """Helper function to create a dummy ONNX model."""
    inputs = [
        helper.make_tensor_value_info(name, TensorProto.FLOAT, [1, 3, 16, 16])
        for name in input_names
    ]
    output = helper.make_tensor_value_info(
        "output", TensorProto.FLOAT, [1, 10]
    )
    nodes = [
        helper.make_node("Add", [name, name], [f"add_{name}"])
        for name in input_names
    ]
    # Dummy node to consume all inputs
    final_node = helper.make_node(
        "Sum", [f"add_{name}" for name in input_names], ["output"]
    )

    graph_def = helper.make_graph(
        nodes + [final_node], "test-model", inputs, [output]
    )
    model_def = helper.make_model(graph_def, producer_name="test")
    onnx.save(model_def, model_path)


@pytest.fixture
def temp_path(tmp_path: Path) -> Path:
    """Fixture to create a temporary directory for tests."""
    return tmp_path


def test_single_input_model(temp_path: Path):
    """Test make_calibration_dataset with a single input model."""
    model_path = temp_path / "single_input.onnx"
    _create_onnx_model(model_path, ["input1"])

    data_path = temp_path / "cal_data"
    data_path.mkdir()
    for i in range(3):
        np.save(data_path / f"sample_{i}.npy", np.random.rand(1, 3, 16, 16))

    config = QuantizationConfig(
        model=model_path,
        data_path=data_path,
        num_samples=3,
        output_file=temp_path / "out.onnx",
    )
    dataset = make_calibration_dataset(config)

    assert isinstance(dataset, dict)
    assert "input1" in dataset
    assert len(dataset["input1"]) == 3
    sample = dataset["input1"][0]
    assert sample.shape == (1, 3, 16, 16)


def test_multiple_input_model(temp_path: Path):
    """Test make_calibration_dataset with a multiple input model."""
    model_path = temp_path / "multi_input.onnx"
    input_names = ["input1", "input2"]
    _create_onnx_model(model_path, input_names)

    data_path = temp_path / "cal_data"
    data_path.mkdir()
    for name in input_names:
        input_dir = data_path / name
        input_dir.mkdir()
        for i in range(2):
            np.save(
                input_dir / f"sample_{i}.npy", np.random.rand(1, 3, 16, 16)
            )

    config = QuantizationConfig(
        model=model_path,
        data_path=data_path,
        num_samples=2,
        output_file=temp_path / "out.onnx",
    )
    dataset = make_calibration_dataset(config)

    assert isinstance(dataset, dict)
    assert "input1" in dataset
    assert "input2" in dataset
    assert len(dataset["input1"]) == 2
    assert len(dataset["input2"]) == 2
    input1_sample = dataset["input1"][0]
    assert input1_sample.shape == (1, 3, 16, 16)
    input2_sample = dataset["input2"][0]
    assert input2_sample.shape == (1, 3, 16, 16)


def test_invalid_data_path(temp_path: Path):
    """Test error when data_path is not a directory."""
    model_path = temp_path / "model.onnx"
    _create_onnx_model(model_path, ["input1"])
    config = QuantizationConfig(
        model=model_path,
        data_path=temp_path / "non_existent",
        num_samples=2,
        output_file=temp_path / "out.onnx",
    )
    with pytest.raises(ValueError):
        make_calibration_dataset(config)


def test_missing_input_dir_for_multi_input(temp_path: Path):
    """Test error when an input directory is missing for a multi-input model."""
    model_path = temp_path / "multi_input.onnx"
    _create_onnx_model(model_path, ["input1", "input2"])

    data_path = temp_path / "cal_data"
    data_path.mkdir()
    (data_path / "input1").mkdir()  # Only create dir for input1

    config = QuantizationConfig(
        model=model_path,
        data_path=data_path,
        num_samples=1,
        output_file=temp_path / "out.onnx",
    )
    with pytest.raises(FileNotFoundError):
        make_calibration_dataset(config)


def test_no_npy_files_found(temp_path: Path):
    """Test error when no .npy files are found in the data directory."""
    model_path = temp_path / "model.onnx"
    _create_onnx_model(model_path, ["input1"])

    data_path = temp_path / "cal_data"
    data_path.mkdir()

    config = QuantizationConfig(
        model=model_path,
        data_path=data_path,
        num_samples=1,
        output_file=temp_path / "out.onnx",
    )
    with pytest.raises(FileNotFoundError):
        make_calibration_dataset(config)


def test_load_calibration_data_single_input(temp_path: Path):
    """Test _load_calibration_data with a single input model."""
    model_path = temp_path / "single_input.onnx"
    _create_onnx_model(model_path, ["input1"])

    data_path = temp_path / "cal_data"
    data_path.mkdir()
    for i in range(5):
        np.save(data_path / f"sample_{i}.npy", np.random.rand(1, 3, 16, 16))

    config = QuantizationConfig(
        model=model_path,
        data_path=data_path,
        num_samples=3,
        output_file=temp_path / "out.onnx",
    )
    data = _load_calibration_data(config)

    assert "input1" in data
    assert len(data["input1"]) == 3
    assert config.num_samples == 3


def test_load_calibration_data_multi_input(temp_path: Path):
    """Test _load_calibration_data with a multi-input model."""
    model_path = temp_path / "multi_input.onnx"
    input_names = ["input1", "input2"]
    _create_onnx_model(model_path, input_names)

    data_path = temp_path / "cal_data"
    data_path.mkdir()
    for name in input_names:
        input_dir = data_path / name
        input_dir.mkdir()
        for i in range(5):
            np.save(
                input_dir / f"sample_{i}.npy", np.random.rand(1, 3, 16, 16)
            )

    config = QuantizationConfig(
        model=model_path,
        data_path=data_path,
        num_samples=2,
        output_file=temp_path / "out.onnx",
    )
    data = _load_calibration_data(config)

    assert "input1" in data
    assert "input2" in data
    assert len(data["input1"]) == 2
    assert len(data["input2"]) == 2
    assert config.num_samples == 2


def test_load_calibration_data_num_samples_greater_than_available(
    temp_path: Path,
):
    """Test _load_calibration_data when num_samples is more than available."""
    model_path = temp_path / "single_input.onnx"
    _create_onnx_model(model_path, ["input1"])

    data_path = temp_path / "cal_data"
    data_path.mkdir()
    for i in range(3):
        np.save(data_path / f"sample_{i}.npy", np.random.rand(1, 3, 16, 16))

    config = QuantizationConfig(
        model=model_path,
        data_path=data_path,
        num_samples=10,
        output_file=temp_path / "out.onnx",
    )
    data = _load_calibration_data(config)

    assert "input1" in data
    assert len(data["input1"]) == 3
    assert config.num_samples == 3


if __name__ == "__main__":
    pytest.main([__file__])
