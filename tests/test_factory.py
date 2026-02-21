"""Tests for the backend factory — ensures correct adapter is selected."""

import pytest
from unittest.mock import patch, MagicMock

from agent_framework.config.schema import AgentConfig
from agent_framework.backends.factory import create_agent


def _cfg(backend: str) -> AgentConfig:
    return AgentConfig(name="test", backend=backend, instructions="x")


def test_create_autogen_agent():
    with patch("agent_framework.backends.autogen_backend.AutogenAgent.__init__", return_value=None) as mock:
        with patch("agent_framework.backends.autogen_backend.AutogenAgent._build"):
            from agent_framework.backends.autogen_backend import AutogenAgent
            with patch.object(AutogenAgent, "__init__", return_value=None):
                agent = create_agent(_cfg("autogen"))
                assert isinstance(agent, AutogenAgent)


def test_create_sk_agent():
    from agent_framework.backends.semantic_kernel_backend import SemanticKernelAgent
    with patch.object(SemanticKernelAgent, "__init__", return_value=None):
        agent = create_agent(_cfg("semantic_kernel"))
        assert isinstance(agent, SemanticKernelAgent)


def test_create_azure_agent():
    from agent_framework.backends.azure_agent_backend import AzureAgent
    with patch.object(AzureAgent, "__init__", return_value=None):
        agent = create_agent(_cfg("azure"))
        assert isinstance(agent, AzureAgent)


def test_unknown_backend_raises():
    cfg = AgentConfig(name="x", backend="autogen", instructions="x")
    cfg.backend = "unknown"  # bypass literal validation
    with pytest.raises(ValueError, match="Unknown backend"):
        create_agent(cfg)
