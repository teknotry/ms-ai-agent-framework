"""
Azure AI Agent Service backend adapter.

Uses azure-ai-projects AIProjectClient to create/retrieve agents and manage threads.
Agents are created idempotently — re-running the same config reuses the existing cloud agent.
"""

from __future__ import annotations

import os
from typing import Optional

from agent_framework.config.schema import AgentConfig
from agent_framework.core.base_agent import BaseAgent
from agent_framework.observability.logger import get_logger

logger = get_logger(__name__)


class AzureAgent(BaseAgent):
    """Agent hosted on Azure AI Agent Service."""

    def __init__(self, config: AgentConfig) -> None:
        super().__init__(config)
        self._client = None
        self._agent_id: Optional[str] = None
        self._thread_id: Optional[str] = None
        self._build()

    def _build(self) -> None:
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential
        except ImportError:
            raise ImportError(
                "azure-ai-projects is not installed. "
                "Install with: pip install 'ms-ai-agent-framework[azure]'"
            )

        conn_str = os.environ.get("AZURE_AI_PROJECT_CONNECTION_STRING", "")
        if not conn_str:
            raise EnvironmentError(
                "AZURE_AI_PROJECT_CONNECTION_STRING environment variable is not set. "
                "Find it in Azure AI Foundry → your project → Overview."
            )

        self._client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=conn_str,
        )
        self._ensure_agent()

    def _ensure_agent(self) -> None:
        """Create the agent in Azure if it doesn't exist yet (idempotent by name)."""
        # Check if an agent with this name already exists
        existing = self._client.agents.list_agents()
        for ag in existing.data:
            if ag.name == self.config.name:
                self._agent_id = ag.id
                logger.info("azure_agent_reused", name=self.config.name, id=ag.id)
                return

        # Build tool list
        tools = []
        for builtin in self.config.azure_builtin_tools:
            if builtin == "code_interpreter":
                tools.append({"type": "code_interpreter"})
            elif builtin == "file_search":
                tools.append({"type": "file_search"})
            elif builtin == "bing_grounding":
                tools.append({"type": "bing_grounding"})

        agent = self._client.agents.create_agent(
            model=self.config.llm.model,
            name=self.config.name,
            instructions=self.config.instructions,
            tools=tools or None,
        )
        self._agent_id = agent.id
        logger.info("azure_agent_created", name=self.config.name, id=agent.id)

    def _get_or_create_thread(self) -> str:
        if not self._thread_id:
            thread = self._client.agents.create_thread()
            self._thread_id = thread.id
            logger.debug("azure_thread_created", thread_id=thread.id)
        return self._thread_id

    def register_tool(self, fn) -> None:
        super().register_tool(fn)
        # Azure AI Agent Service uses built-in tools; custom function tools
        # would require Azure Functions integration which is wired up separately.
        logger.warning(
            "azure_custom_tool_not_supported",
            tool=fn.__name__,
            hint="Use azure_builtin_tools in config or wrap as Azure Function.",
        )

    async def run(self, message: str) -> str:
        logger.info("azure_run", agent=self.name, message_preview=message[:80])
        thread_id = self._get_or_create_thread()

        self._client.agents.create_message(
            thread_id=thread_id,
            role="user",
            content=message,
        )

        run = self._client.agents.create_and_process_run(
            thread_id=thread_id,
            agent_id=self._agent_id,
        )

        if run.status == "failed":
            logger.error("azure_run_failed", error=run.last_error)
            raise RuntimeError(f"Azure agent run failed: {run.last_error}")

        messages = self._client.agents.list_messages(thread_id=thread_id)
        last = messages.get_last_text_message_by_role("assistant")
        return last.text.value if last else ""

    async def reset(self) -> None:
        """Start a fresh thread (conversation history cleared)."""
        self._thread_id = None
        logger.info("azure_thread_reset", agent=self.name)
