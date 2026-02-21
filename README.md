# ms-ai-agent-framework

A unified Python framework to **build, run, and deploy AI agents** using Microsoft's three agent tools:

| Backend | Best for |
|---------|----------|
| **AutoGen** | Multi-agent collaboration, code generation |
| **Semantic Kernel** | Plugin-based single agents, app integration |
| **Azure AI Agent Service** | Managed cloud agents, enterprise deployments |

---

## Quick Start

```bash
# Install (choose the extras you need)
pip install -e ".[autogen,semantic-kernel]"

# Scaffold a new project
agent init my-project
cd my-project

# Run an agent
export OPENAI_API_KEY=sk-...
agent run agents/example_agent.yaml "Write a hello world function in Python"
```

---

## Defining an Agent (YAML)

```yaml
# agents/my_agent.yaml
name: my-agent
backend: autogen          # autogen | semantic_kernel | azure
instructions: "You are a helpful Python developer."
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  temperature: 0.1
tools:
  - name: web_search
    module: tools.web_search
    function: search_web
    description: Search the web for information
max_turns: 5
```

---

## CLI Reference

```
agent init [PROJECT_DIR]                  Scaffold a new project
agent create <name> --backend <b>         Create agent config template
agent run <config.yaml> "<message>"       Run a single agent
agent pipeline run <pipeline.yaml> "<t>"  Run a multi-agent pipeline
agent deploy local <config.yaml>          Run as local HTTP server
agent deploy docker <config.yaml>         Build & run in Docker
agent deploy azure <config.yaml>          Deploy to Azure Container Apps
agent list [agents-dir]                   List all agent configs
agent logs <agent-name>                   Stream logs
```

---

## Multi-Agent Pipelines

```yaml
# agents/my_pipeline.yaml
name: research-then-code
agents:
  - research-agent      # defined in agents/research-agent.yaml
  - coder-agent         # defined in agents/coder-agent.yaml
strategy: sequential    # sequential | group_chat | supervisor
```

```bash
agent pipeline run agents/my_pipeline.yaml "Research Python async patterns and write example code"
```

---

## Writing Custom Tools

```python
# tools/my_tool.py
from agent_framework.core.tool_registry import register_tool

@register_tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    return str(eval(expression, {"__builtins__": {}}))
```

Reference in your agent YAML:
```yaml
tools:
  - name: calculate
    module: tools.my_tool
    function: calculate
```

---

## Deployment

### Local HTTP server
```bash
agent deploy local agents/my_agent.yaml --port 8080
# POST http://localhost:8080/run  {"message": "Hello"}
```

### Docker
```bash
agent deploy docker agents/my_agent.yaml
```

### Azure Container Apps
```bash
export AZURE_RESOURCE_GROUP=my-rg
export AZURE_SUBSCRIPTION_ID=...
agent deploy azure agents/my_agent.yaml --location eastus
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `AZURE_AI_PROJECT_CONNECTION_STRING` | Azure AI Foundry project connection string |
| `AZURE_RESOURCE_GROUP` | Default Azure resource group for deployments |
| `AZURE_SUBSCRIPTION_ID` | Azure subscription ID |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint for tracing |
| `AGENT_DEBUG` | Set to `1` for verbose debug logging |

---

## Project Structure

```
ms-ai-agent-framework/
├── agent_framework/
│   ├── cli.py                  # CLI entry point
│   ├── config/                 # Schema + loader
│   ├── core/                   # BaseAgent, ToolRegistry, Pipeline
│   ├── backends/               # AutoGen, Semantic Kernel, Azure adapters
│   ├── deploy/                 # Local, Docker, Azure deployers
│   └── observability/          # Structured logging + OpenTelemetry
├── agents/                     # Your agent YAML configs
├── tools/                      # Your custom tools
└── tests/
```
