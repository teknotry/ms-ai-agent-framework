"""Factory function to instantiate the correct backend from an AgentConfig."""

from __future__ import annotations

from agent_framework.config.schema import AgentConfig
from agent_framework.core.base_agent import BaseAgent
from agent_framework.core.tool_registry import ToolRegistry


def create_agent(config: AgentConfig, registry: ToolRegistry | None = None) -> BaseAgent:
    """
    Instantiate the appropriate backend agent for *config*.

    If *registry* is provided its tools are injected into the agent after creation.
    """
    if config.backend == "autogen":
        from agent_framework.backends.autogen_backend import AutogenAgent
        agent = AutogenAgent(config)
    elif config.backend == "semantic_kernel":
        from agent_framework.backends.semantic_kernel_backend import SemanticKernelAgent
        agent = SemanticKernelAgent(config)
    elif config.backend == "azure":
        from agent_framework.backends.azure_agent_backend import AzureAgent
        agent = AzureAgent(config)
    else:
        raise ValueError(f"Unknown backend: {config.backend!r}. Choose autogen | semantic_kernel | azure")

    if registry:
        registry.inject(agent)

    return agent
