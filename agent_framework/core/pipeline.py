"""
Multi-agent pipeline orchestration.

Supports three strategies:
  sequential  — output of agent[N] becomes input of agent[N+1]
  group_chat  — all agents collaborate in an AutoGen GroupChat
  supervisor  — a supervisor agent routes tasks to specialist agents
"""

from __future__ import annotations

from typing import Dict, List

from agent_framework.config.schema import PipelineConfig
from agent_framework.core.base_agent import BaseAgent
from agent_framework.observability.logger import get_logger

logger = get_logger(__name__)


class Pipeline:
    def __init__(self, config: PipelineConfig, agents: Dict[str, BaseAgent]) -> None:
        self.config = config
        self.name = config.name
        self.agents = agents
        self._ordered: List[BaseAgent] = [agents[n] for n in config.agents]

    async def run(self, task: str) -> str:
        logger.info("pipeline_start", pipeline=self.name, strategy=self.config.strategy, task=task[:80])
        if self.config.strategy == "sequential":
            result = await self._run_sequential(task)
        elif self.config.strategy == "group_chat":
            result = await self._run_group_chat(task)
        elif self.config.strategy == "supervisor":
            result = await self._run_supervisor(task)
        else:
            raise ValueError(f"Unknown strategy: {self.config.strategy}")
        logger.info("pipeline_done", pipeline=self.name)
        return result

    async def _run_sequential(self, task: str) -> str:
        current_input = task
        for agent in self._ordered:
            logger.debug("sequential_step", agent=agent.name, input_preview=current_input[:60])
            current_input = await agent.run(current_input)
        return current_input

    async def _run_group_chat(self, task: str) -> str:
        """
        Delegates to AutoGen GroupChat if any backend is autogen,
        otherwise falls back to sequential with context accumulation.
        """
        from agent_framework.backends.autogen_backend import run_group_chat

        autogen_agents = [a for a in self._ordered if a.config.backend == "autogen"]
        if autogen_agents:
            return await run_group_chat(autogen_agents, task, max_rounds=self.config.max_rounds)

        # Fallback: broadcast task to all agents, concatenate responses
        responses = []
        for agent in self._ordered:
            resp = await agent.run(task)
            responses.append(f"[{agent.name}]: {resp}")
        return "\n\n".join(responses)

    async def _run_supervisor(self, task: str) -> str:
        """
        The supervisor agent receives the task plus a list of available specialist agents,
        decides which specialist to call (by name), and we route accordingly.
        """
        if not self.config.supervisor_agent:
            raise ValueError("supervisor_agent not set in pipeline config")

        supervisor = self.agents[self.config.supervisor_agent]
        specialists = {n: a for n, a in self.agents.items() if n != self.config.supervisor_agent}

        specialist_info = "\n".join(
            f"- {name}: {a.config.instructions[:100]}" for name, a in specialists.items()
        )
        routing_prompt = (
            f"You are a supervisor. Available specialists:\n{specialist_info}\n\n"
            f"Task: {task}\n\n"
            f"Reply with ONLY the name of the specialist that should handle this task."
        )

        chosen_name = (await supervisor.run(routing_prompt)).strip()
        logger.info("supervisor_routing", chosen=chosen_name)

        if chosen_name not in specialists:
            # If supervisor gave a bad name, fall back to first specialist
            logger.warning("supervisor_bad_routing", chosen=chosen_name, fallback=list(specialists)[0])
            chosen_name = list(specialists)[0]

        return await specialists[chosen_name].run(task)
