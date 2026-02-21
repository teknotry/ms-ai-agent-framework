"""Tests for Pipeline orchestration."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agent_framework.config.schema import PipelineConfig, AgentConfig
from agent_framework.core.pipeline import Pipeline


def _make_agent(name: str, backend: str = "autogen", response: str = "ok") -> MagicMock:
    cfg = AgentConfig(name=name, backend=backend, instructions="x")
    agent = MagicMock()
    agent.name = name
    agent.config = cfg
    agent.run = AsyncMock(return_value=response)
    return agent


@pytest.mark.asyncio
async def test_sequential_pipeline():
    agent_a = _make_agent("a", response="output-from-a")
    agent_b = _make_agent("b", response="final-output")

    cfg = PipelineConfig(name="pipe", agents=["a", "b"], strategy="sequential")
    pipe = Pipeline(cfg, {"a": agent_a, "b": agent_b})

    result = await pipe.run("start")
    assert result == "final-output"
    agent_a.run.assert_called_once_with("start")
    agent_b.run.assert_called_once_with("output-from-a")


@pytest.mark.asyncio
async def test_supervisor_pipeline():
    supervisor = _make_agent("supervisor", response="specialist-b")
    spec_a = _make_agent("specialist-a", response="result-a")
    spec_b = _make_agent("specialist-b", response="result-b")

    cfg = PipelineConfig(
        name="pipe",
        agents=["supervisor", "specialist-a", "specialist-b"],
        strategy="supervisor",
        supervisor_agent="supervisor",
    )
    pipe = Pipeline(cfg, {"supervisor": supervisor, "specialist-a": spec_a, "specialist-b": spec_b})
    result = await pipe.run("do something")

    assert result == "result-b"
    spec_b.run.assert_called_once_with("do something")
    spec_a.run.assert_not_called()


@pytest.mark.asyncio
async def test_supervisor_bad_routing_fallback():
    supervisor = _make_agent("supervisor", response="nonexistent-agent")
    spec = _make_agent("specialist", response="fallback-result")

    cfg = PipelineConfig(
        name="pipe",
        agents=["supervisor", "specialist"],
        strategy="supervisor",
        supervisor_agent="supervisor",
    )
    pipe = Pipeline(cfg, {"supervisor": supervisor, "specialist": spec})
    result = await pipe.run("task")
    assert result == "fallback-result"
