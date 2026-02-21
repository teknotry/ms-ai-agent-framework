"""
Semantic Kernel backend adapter.

Creates a Kernel with OpenAIChatCompletion and wraps tools as KernelPlugins.
"""

from __future__ import annotations

import os
from typing import Callable, List

from agent_framework.config.schema import AgentConfig
from agent_framework.core.base_agent import BaseAgent
from agent_framework.observability.logger import get_logger

logger = get_logger(__name__)


class SemanticKernelAgent(BaseAgent):
    """Agent backed by Microsoft Semantic Kernel."""

    def __init__(self, config: AgentConfig) -> None:
        super().__init__(config)
        self._kernel = None
        self._agent = None
        self._pending_tools: List[Callable] = []
        self._build()

    def _build(self) -> None:
        try:
            from semantic_kernel import Kernel
            from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, AzureChatCompletion
            from semantic_kernel.agents import ChatCompletionAgent
        except ImportError:
            raise ImportError(
                "semantic-kernel is not installed. "
                "Install with: pip install 'ms-ai-agent-framework[semantic-kernel]'"
            )

        kernel = Kernel()

        api_key = os.environ.get(self.config.llm.api_key_env, "")

        if self.config.llm.base_url and "azure" in self.config.llm.base_url.lower():
            service = AzureChatCompletion(
                service_id="chat",
                deployment_name=self.config.llm.model,
                endpoint=self.config.llm.base_url,
                api_key=api_key,
                api_version=self.config.llm.api_version or "2024-02-01",
            )
        else:
            service = OpenAIChatCompletion(
                service_id="chat",
                ai_model_id=self.config.llm.model,
                api_key=api_key,
            )

        kernel.add_service(service)

        # Register already-known tools
        for fn in self._tools:
            self._add_plugin(kernel, fn)

        self._kernel = kernel
        self._agent = ChatCompletionAgent(
            service=service,
            kernel=kernel,
            name=self.config.name,
            instructions=self.config.instructions,
        )

    def _add_plugin(self, kernel, fn: Callable) -> None:
        """Wrap a plain function as a KernelPlugin and add it to the kernel."""
        try:
            from semantic_kernel.functions import kernel_function
            from semantic_kernel.plugin_definition import KernelPlugin
        except ImportError:
            return

        # Decorate with kernel_function if not already decorated
        if not hasattr(fn, "__kernel_function__"):
            fn = kernel_function(description=fn.__doc__ or fn.__name__)(fn)

        plugin = KernelPlugin.from_object(plugin_instance=None, plugin_name=fn.__name__, functions=[fn])
        kernel.add_plugin(plugin)

    def register_tool(self, fn: Callable) -> None:
        super().register_tool(fn)
        if self._kernel is not None:
            self._add_plugin(self._kernel, fn)

    async def run(self, message: str) -> str:
        logger.info("sk_run", agent=self.name, message_preview=message[:80])
        from semantic_kernel.contents import ChatHistory

        history = ChatHistory()
        history.add_user_message(message)

        response = await self._agent.get_response(messages=history)
        return str(response)

    async def reset(self) -> None:
        self._build()
