# Copyright (C) 2025 Embedl AB

"""Test the Embedl Hub SDK CLI utils."""

import pytest

from embedl_hub.cli.utils import prepare_input_size


@pytest.mark.parametrize(
    "size_str, expected_tuple",
    [
        ("1,3,224,224", (1, 3, 224, 224)),
        ("1,28,28", (1, 28, 28)),
        ("1", (1,)),
    ],
)
def test_prepare_input_size_valid(size_str, expected_tuple, capsys):
    """Test prepare_input_size with valid comma-separated integer strings."""
    result = prepare_input_size(size_str)
    assert result == expected_tuple
    captured = capsys.readouterr()
    assert f"Using input size: {size_str}" in captured.out


def test_prepare_input_size_empty():
    """Test prepare_input_size with an empty string."""
    assert prepare_input_size("") is None


def test_prepare_input_size_invalid():
    """Test prepare_input_size with an invalid string."""
    with pytest.raises(
        ValueError,
        match="Invalid size format. Use dim0, dim1,..., e.g. 1,3,224,224",
    ):
        prepare_input_size("1,three,224,224")
