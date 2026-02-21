"""
AutoGen backend adapter.

Wraps autogen-agentchat AssistantAgent + UserProxyAgent.
Also exposes run_group_chat() for Pipeline orchestration.
"""

from __future__ import annotations

import os
from typing import List

from agent_framework.config.schema import AgentConfig
from agent_framework.core.base_agent import BaseAgent
from agent_framework.observability.logger import get_logger

logger = get_logger(__name__)


class AutogenAgent(BaseAgent):
    """Single AutoGen AssistantAgent wrapped in the BaseAgent interface."""

    def __init__(self, config: AgentConfig) -> None:
        super().__init__(config)
        self._assistant = None
        self._proxy = None
        self._build()

    def _build(self) -> None:
        try:
            import autogen
        except ImportError:
            raise ImportError(
                "autogen-agentchat is not installed. "
                "Install with: pip install 'ms-ai-agent-framework[autogen]'"
            )

        api_key = os.environ.get(self.config.llm.api_key_env, "")
        llm_config: dict = {
            "config_list": [
                {
                    "model": self.config.llm.model,
                    "api_key": api_key,
                    **({"base_url": self.config.llm.base_url} if self.config.llm.base_url else {}),
                    **({"api_version": self.config.llm.api_version} if self.config.llm.api_version else {}),
                }
            ],
            "temperature": self.config.llm.temperature,
        }

        self._assistant = autogen.AssistantAgent(
            name=self.config.name,
            system_message=self.config.instructions,
            llm_config=llm_config,
        )

        self._proxy = autogen.UserProxyAgent(
            name=f"{self.config.name}_proxy",
            human_input_mode="ALWAYS" if self.config.human_input else "NEVER",
            max_consecutive_auto_reply=self.config.max_turns,
            code_execution_config=self.config.extra.get("code_execution_config", False),
        )

        # Register tools with the assistant
        for fn in self._tools:
            self._assistant.register_for_llm(description=fn.__doc__ or fn.__name__)(fn)
            self._proxy.register_for_execution()(fn)

    def register_tool(self, fn) -> None:
        super().register_tool(fn)
        # If already built, register immediately
        if self._assistant is not None:
            self._assistant.register_for_llm(description=fn.__doc__ or fn.__name__)(fn)
            self._proxy.register_for_execution()(fn)

    async def run(self, message: str) -> str:
        logger.info("autogen_run", agent=self.name, message_preview=message[:80])
        chat_result = await self._proxy.a_initiate_chat(
            self._assistant,
            message=message,
            max_turns=self.config.max_turns,
        )
        # Return the last assistant message
        for msg in reversed(chat_result.chat_history):
            if msg.get("role") == "assistant":
                return msg.get("content", "")
        return ""

    async def reset(self) -> None:
        self._build()


async def run_group_chat(agents: List[AutogenAgent], task: str, max_rounds: int = 10) -> str:
    """Run a GroupChat with the given AutogenAgents."""
    try:
        import autogen
    except ImportError:
        raise ImportError("autogen-agentchat is required for group_chat strategy.")

    raw_agents = [a._assistant for a in agents]
    # Add a proxy to kick off the conversation
    proxy = autogen.UserProxyAgent(
        name="orchestrator_proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
    )
    raw_agents.append(proxy)

    group_chat = autogen.GroupChat(
        agents=raw_agents,
        messages=[],
        max_round=max_rounds,
    )
    manager = autogen.GroupChatManager(
        groupchat=group_chat,
        llm_config=agents[0]._assistant.llm_config,
    )
    chat_result = await proxy.a_initiate_chat(manager, message=task)

    for msg in reversed(chat_result.chat_history):
        if msg.get("role") == "assistant":
            return msg.get("content", "")
    return ""
