"""Pydantic models for agent, pipeline, and deployment configuration."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class ToolConfig(BaseModel):
    """Defines a tool/function the agent can call."""
    name: str = Field(description="Unique tool name")
    module: str = Field(description="Python module path, e.g. 'tools.web_search'")
    function: str = Field(description="Function name within the module")
    description: Optional[str] = Field(default=None, description="Human-readable description for the LLM")


class LLMConfig(BaseModel):
    """LLM connection settings."""
    model: str = Field(default="gpt-4o", description="Model name, e.g. gpt-4o")
    api_key_env: str = Field(default="OPENAI_API_KEY", description="Env var name holding the API key")
    base_url: Optional[str] = Field(default=None, description="Custom API base URL (Azure OpenAI etc.)")
    api_version: Optional[str] = Field(default=None, description="API version for Azure OpenAI")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None)


class AgentConfig(BaseModel):
    """Full configuration for a single agent."""
    name: str = Field(description="Unique agent name")
    backend: Literal["autogen", "semantic_kernel", "azure"] = Field(
        description="Which Microsoft framework powers this agent"
    )
    instructions: str = Field(description="System prompt / role instructions for the agent")
    llm: LLMConfig = Field(default_factory=LLMConfig)
    tools: List[ToolConfig] = Field(default_factory=list)
    human_input: bool = Field(default=False, description="Pause and wait for human input each turn")
    max_turns: int = Field(default=10, ge=1)
    # Azure-specific built-in tools
    azure_builtin_tools: List[Literal["code_interpreter", "file_search", "bing_grounding"]] = Field(
        default_factory=list
    )
    # Extra backend-specific kwargs passed through verbatim
    extra: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_azure_tools(self) -> "AgentConfig":
        if self.azure_builtin_tools and self.backend != "azure":
            raise ValueError("azure_builtin_tools can only be used with the 'azure' backend")
        return self


class PipelineConfig(BaseModel):
    """Configuration for a multi-agent pipeline."""
    name: str
    agents: List[str] = Field(description="Ordered list of agent names (from agent config files)")
    strategy: Literal["sequential", "group_chat", "supervisor"] = Field(
        default="sequential",
        description=(
            "sequential: chain outputs; "
            "group_chat: AutoGen GroupChat; "
            "supervisor: first agent routes to others"
        ),
    )
    max_rounds: int = Field(default=10, ge=1, description="Max conversation rounds (group_chat/supervisor)")
    supervisor_agent: Optional[str] = Field(
        default=None, description="Name of the supervisor agent (required for supervisor strategy)"
    )

    @model_validator(mode="after")
    def validate_supervisor(self) -> "PipelineConfig":
        if self.strategy == "supervisor" and not self.supervisor_agent:
            raise ValueError("supervisor_agent must be set when strategy is 'supervisor'")
        return self


class DeployConfig(BaseModel):
    """Deployment target configuration, embedded in agent config or standalone."""
    target: Literal["local", "docker", "azure"] = "local"
    port: int = Field(default=8080, description="Port to expose the agent HTTP server")
    # Docker
    image_name: Optional[str] = None
    docker_registry: Optional[str] = None
    # Azure
    azure_subscription_id: Optional[str] = None
    azure_resource_group: Optional[str] = None
    azure_location: str = Field(default="eastus")
    azure_container_app_env: Optional[str] = None
