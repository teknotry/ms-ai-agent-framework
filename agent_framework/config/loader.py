"""Load and validate YAML/JSON agent and pipeline configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import yaml

from .schema import AgentConfig, PipelineConfig


def _read_file(path: Union[str, Path]) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    text = path.read_text()
    if path.suffix in (".yaml", ".yml"):
        return yaml.safe_load(text)
    if path.suffix == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported config format: {path.suffix}. Use .yaml, .yml, or .json")


def load_agent_config(path: Union[str, Path]) -> AgentConfig:
    """Load and validate an AgentConfig from a YAML or JSON file."""
    data = _read_file(path)
    return AgentConfig.model_validate(data)


def load_pipeline_config(path: Union[str, Path]) -> PipelineConfig:
    """Load and validate a PipelineConfig from a YAML or JSON file."""
    data = _read_file(path)
    return PipelineConfig.model_validate(data)
