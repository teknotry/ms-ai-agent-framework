"""
Tool registry — discover, register, and inject tools into agents.

Usage (decorator style):
    @register_tool
    def web_search(query: str) -> str: ...

Usage (programmatic):
    registry = ToolRegistry()
    registry.register(my_fn)
    registry.inject(agent)
"""

from __future__ import annotations

import importlib
import inspect
from typing import Callable, Dict, List, Optional

from agent_framework.config.schema import AgentConfig, ToolConfig
from agent_framework.observability.logger import get_logger

logger = get_logger(__name__)

# Module-level default registry (used by the @register_tool decorator)
_default_registry: Optional["ToolRegistry"] = None


def _get_default_registry() -> "ToolRegistry":
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def register_tool(fn: Callable) -> Callable:
    """Decorator to register a function in the default global ToolRegistry."""
    _get_default_registry().register(fn)
    return fn


class ToolRegistry:
    """Holds a mapping of tool name → callable and injects them into agents."""

    def __init__(self) -> None:
        self._tools: Dict[str, Callable] = {}

    def register(self, fn: Callable, name: Optional[str] = None) -> None:
        """Register *fn* under *name* (defaults to fn.__name__)."""
        tool_name = name or fn.__name__
        self._tools[tool_name] = fn
        logger.debug("tool_registered", name=tool_name)

    def get(self, name: str) -> Callable:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry. Registered: {list(self._tools)}")
        return self._tools[name]

    def all(self) -> List[Callable]:
        return list(self._tools.values())

    def load_from_config(self, tool_configs: List[ToolConfig]) -> None:
        """
        Dynamically import and register tools declared in an AgentConfig.

        Each ToolConfig specifies a module path and function name:
            module: "tools.web_search"
            function: "search_web"
        """
        for tc in tool_configs:
            mod = importlib.import_module(tc.module)
            fn = getattr(mod, tc.function)
            if tc.description:
                fn.__doc__ = tc.description
            self.register(fn, name=tc.name)

    def inject(self, agent: "BaseAgent") -> None:  # noqa: F821
        """Register all tools in this registry onto *agent*."""
        for fn in self._tools.values():
            agent.register_tool(fn)
        logger.debug("tools_injected", agent=agent.name, count=len(self._tools))

    @classmethod
    def from_agent_config(cls, config: AgentConfig) -> "ToolRegistry":
        """Create a ToolRegistry pre-loaded with all tools declared in *config*."""
        registry = cls()
        registry.load_from_config(config.tools)
        return registry
