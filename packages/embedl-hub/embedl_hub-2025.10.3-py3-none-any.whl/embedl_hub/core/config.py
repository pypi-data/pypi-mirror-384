# Copyright (C) 2025 Embedl AB

"""Base class for configuration management."""

import importlib
import os
from contextlib import contextmanager
from pathlib import Path
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

import yaml
from jinja2 import Environment, StrictUndefined
from mergedeep import Strategy, merge
from pydantic import BaseModel

# Global variable to store default configurations (yaml files)
default_configs: Dict[str, str] = {
    "quantize": "quantization_config.yaml.j2",
}

T = TypeVar("T", bound="ExperimentConfig")


def load_defaults(file_name: str) -> Dict[str, Any]:
    """Load default configuration from a YAML file."""
    template_content = importlib.resources.read_text(
        "embedl_hub.core.default_configs", file_name
    )

    # Define the Jinja environment
    env = Environment(
        undefined=StrictUndefined,  # blows up if you reference a var you didn't supply
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Make env-variables visible in the environment
    env.globals.update(os.environ)

    rendered = env.from_string(template_content).render()
    return yaml.safe_load(rendered)


@contextmanager
def temp_img_size_env(env_vars: Dict[str, Any]):
    """Temporarily overwrite environment variables and undo on exit."""
    # stash old values
    old = {k: os.environ.get(k) for k in env_vars}
    # set new ones
    os.environ.update(env_vars)
    try:
        yield
    finally:
        # restore (or delete if not set before)
        for k, v in old.items():
            if v is None:
                del os.environ[k]
            else:
                os.environ[k] = v


def load_default_config_with_size(
    config_class: Type['ExperimentConfig'],
    size: Optional[str],
    default_config_name: str,
):
    """Load the default config, populating the config with the correct sizes.

    Sizes are either provided by the user in the cli or defined in a jinja2 template.
    The population is done by temporarily defining the sizes as env-variables and
    read by the reader.
    """
    if size is None:
        env_vars = {}
    else:
        h_and_w = size.split(',')
        if len(h_and_w) != 2:
            raise ValueError(
                "Expected `size` to be a comma separated set of two values, e.g. 224,224."
            )
        env_vars = {"IMG_H": h_and_w[0], "IMG_W": h_and_w[1]}
    with temp_img_size_env(env_vars):
        cfg = config_class.model_construct(
            **load_defaults(default_configs[default_config_name])
        )
        return cfg


class ExperimentConfig(BaseModel):
    """Base class for experiment configuration."""

    def to_yaml(self, path: Path) -> str:
        """Convert the configuration to a YAML string."""
        yaml_txt = yaml.dump(self.model_dump)
        if path is not None:
            path.write_text(yaml_txt)
        return yaml_txt

    @classmethod
    def from_yaml(cls: Type[T], path: Union[str, Path]) -> T:
        """Load the configuration from a YAML file."""
        return cls.model_construct(
            **yaml.safe_load(Path(path).read_text("utf-8"))
        )

    def merge_yaml(
        self: T, other: Optional[Union[str, Path]], **override
    ) -> T:
        """Merge another YAML file into the current configuration."""
        return self.merge_dict(
            yaml.safe_load(Path(other).read_text("utf-8")) if other else None,
            **override,
        )

    def merge_dict(
        self: T, other: Optional[Mapping[str, Any]], **override
    ) -> T:
        """
        Merge *other* (usually parsed YAML) and **override (kwargs) into a copy.
        Precedence: kwargs > other > self.
        """
        base = self.model_dump()
        if other is not None:
            merged = merge(base, other, strategy=Strategy.REPLACE)
        else:
            merged = base
        merged = merge(
            merged, override, strategy=Strategy.REPLACE
        )  # kwargs win last
        return self.__class__.model_construct(**merged).cast_str_to_path()

    def cast_str_to_path(self: T) -> T:
        """
        Casts string attributes to Path objects if the type hint is Path.

        This is useful when loading from sources that don't distinguish
        between strings and paths, like environment variables.
        """
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name)
            if isinstance(value, str):
                # Check if the field's type annotation is Path or Optional[Path]
                # This is a simplified check. For more complex types like
                # Union[Path, int], a more robust check would be needed.
                is_path_type = field_info.annotation is Path
                if not is_path_type:
                    origin = get_origin(field_info.annotation)
                    if origin:  # Handles Union, Optional, etc.
                        args = get_args(field_info.annotation)
                        if Path in args:
                            is_path_type = True

                if is_path_type:
                    setattr(self, field_name, Path(value))
        return self

    def validate_config(self) -> None:
        """Validate the configuration."""
        self.model_validate(self.model_dump())
