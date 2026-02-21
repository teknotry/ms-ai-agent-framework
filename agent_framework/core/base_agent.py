"""Abstract base class that every backend adapter must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, List

from agent_framework.config.schema import AgentConfig


class BaseAgent(ABC):
    """
    Common interface for all agent backends.

    Every backend (AutoGen, Semantic Kernel, Azure) wraps itself in a subclass
    of BaseAgent so the rest of the framework can treat them uniformly.
    """

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.name = config.name
        self._tools: List[Callable] = []

    def register_tool(self, fn: Callable) -> None:
        """Attach a callable tool to this agent. Called by ToolRegistry."""
        self._tools.append(fn)

    @abstractmethod
    async def run(self, message: str) -> str:
        """
        Send *message* to the agent and return its final text response.

        Implementations must be async-safe and return the full reply as a string.
        """

    @abstractmethod
    async def reset(self) -> None:
        """Clear conversation history / thread state so the agent starts fresh."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} backend={self.config.backend!r}>"
