"""Tests for ToolRegistry."""

import pytest
from agent_framework.core.tool_registry import ToolRegistry


def greet(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


def test_register_and_get():
    reg = ToolRegistry()
    reg.register(greet)
    fn = reg.get("greet")
    assert fn("World") == "Hello, World!"


def test_register_custom_name():
    reg = ToolRegistry()
    reg.register(greet, name="say_hello")
    assert reg.get("say_hello")("Bob") == "Hello, Bob!"


def test_get_missing_raises():
    reg = ToolRegistry()
    with pytest.raises(KeyError, match="missing_tool"):
        reg.get("missing_tool")


def test_all_returns_list():
    reg = ToolRegistry()
    reg.register(greet)
    reg.register(add)
    assert len(reg.all()) == 2


def test_inject_into_agent():
    from unittest.mock import MagicMock
    from agent_framework.config.schema import AgentConfig

    cfg = AgentConfig(name="test", backend="autogen", instructions="x")
    agent = MagicMock()
    agent.name = "test"

    reg = ToolRegistry()
    reg.register(greet)
    reg.inject(agent)
    agent.register_tool.assert_called_once_with(greet)
