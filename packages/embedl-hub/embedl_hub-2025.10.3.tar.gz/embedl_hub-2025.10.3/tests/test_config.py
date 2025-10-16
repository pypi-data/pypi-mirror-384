# Copyright (C) 2025 Embedl AB

"""Tests for the functionality of the ExperimentConfig class."""

import pytest
import yaml

from embedl_hub.core.config import ExperimentConfig


class MainConfig(ExperimentConfig):
    """Main configuration class for testing. Contains an inner config."""

    a: str = "hello"
    x: int = 3
    y: int = 2


def test_from_dict_and_to_dict_roundtrip():
    """Test the round-trip conversion of a dictionary to a config object and back."""
    data = {"a": "world", "x": 10}
    cfg = MainConfig(**data)
    assert cfg.a == "world"
    assert cfg.x == 10
    assert cfg.y == 2

    # round-trip via to_dict()
    output = cfg.model_dump()
    assert output == {"a": "world", "x": 10, "y": 2}


def test_merge_dict_overrides():
    """Test merging a dictionary into the config object with overrides."""
    cfg1 = MainConfig()
    # override a and y only
    cfg2 = cfg1.merge_dict({"a": "hello world", "y": 5})
    assert cfg2.a == "hello world"  # overridden
    assert cfg2.y == 5
    assert cfg1.y == 2  # original unchanged

    # override via kwargs
    cfg3 = cfg1.merge_dict({}, a="new", x=7)
    assert cfg3.a == "new"
    assert cfg3.x == 7


def test_merge_yaml(tmp_path):
    """Test merging a YAML file into the config object."""
    # create a temporary YAML file
    file = tmp_path / "cfg.yaml"
    yaml.dump({"a": "tmp", "y": 9}, file.open("w"))
    cfg1 = MainConfig()
    cfg4 = cfg1.merge_yaml(file)
    assert cfg4.a == "tmp"
    assert cfg4.y == 9


def test_merge_yaml_with_kwargs(tmp_path):
    """Test merging a YAML file into the config object with kwargs."""
    # create a temporary YAML file
    file = tmp_path / "cfg.yaml"
    yaml.dump({"a": "file", "x": 3, "y": 4}, file.open("w"))
    cfg1 = MainConfig()
    # merge YAML and override with kwargs
    cfg5 = cfg1.merge_yaml(file, a="override", y=99)
    assert cfg5.a == "override"  # kwarg overrides YAML
    assert cfg5.x == 3  # from file
    assert cfg5.y == 99  # kwarg overrides y


if __name__ == "__main__":
    pytest.main([__file__])
