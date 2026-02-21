"""Tests for config schema and loader."""

import textwrap
from pathlib import Path

import pytest

from agent_framework.config.schema import AgentConfig, PipelineConfig, ToolConfig
from agent_framework.config.loader import load_agent_config, load_pipeline_config


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

def test_agent_config_defaults():
    cfg = AgentConfig(
        name="test",
        backend="autogen",
        instructions="You are helpful.",
    )
    assert cfg.max_turns == 10
    assert cfg.human_input is False
    assert cfg.tools == []
    assert cfg.llm.model == "gpt-4o"


def test_agent_config_with_tools():
    cfg = AgentConfig(
        name="test",
        backend="semantic_kernel",
        instructions="Help.",
        tools=[ToolConfig(name="search", module="tools.web_search", function="search_web")],
    )
    assert len(cfg.tools) == 1
    assert cfg.tools[0].name == "search"


def test_azure_builtin_tools_wrong_backend():
    with pytest.raises(ValueError, match="azure_builtin_tools"):
        AgentConfig(
            name="bad",
            backend="autogen",
            instructions="x",
            azure_builtin_tools=["code_interpreter"],
        )


def test_pipeline_supervisor_missing_agent():
    with pytest.raises(ValueError, match="supervisor_agent"):
        PipelineConfig(name="pipe", agents=["a", "b"], strategy="supervisor")


def test_pipeline_supervisor_valid():
    cfg = PipelineConfig(
        name="pipe",
        agents=["supervisor", "specialist"],
        strategy="supervisor",
        supervisor_agent="supervisor",
    )
    assert cfg.strategy == "supervisor"


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------

def test_load_agent_config_yaml(tmp_path: Path):
    yaml_content = textwrap.dedent("""\
        name: yaml-agent
        backend: autogen
        instructions: "You help."
        llm:
          model: gpt-4o
          api_key_env: OPENAI_API_KEY
    """)
    f = tmp_path / "agent.yaml"
    f.write_text(yaml_content)
    cfg = load_agent_config(f)
    assert cfg.name == "yaml-agent"
    assert cfg.backend == "autogen"


def test_load_agent_config_json(tmp_path: Path):
    import json
    data = {
        "name": "json-agent",
        "backend": "azure",
        "instructions": "Help.",
        "azure_builtin_tools": ["code_interpreter"],
    }
    f = tmp_path / "agent.json"
    f.write_text(json.dumps(data))
    cfg = load_agent_config(f)
    assert cfg.name == "json-agent"
    assert "code_interpreter" in cfg.azure_builtin_tools


def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_agent_config("/nonexistent/path/agent.yaml")


def test_load_pipeline_config(tmp_path: Path):
    import yaml as _yaml
    data = {"name": "my-pipeline", "agents": ["a", "b"], "strategy": "sequential"}
    f = tmp_path / "pipeline.yaml"
    f.write_text(_yaml.dump(data))
    cfg = load_pipeline_config(f)
    assert cfg.name == "my-pipeline"
    assert cfg.strategy == "sequential"
