# ms-ai-agent-framework — Documentation

Welcome to the full documentation for **ms-ai-agent-framework**, a unified Python framework
to build, run, and deploy AI agents using Microsoft's agent tools.

---

## Documentation Index

| # | Guide | What you'll learn |
|---|-------|-------------------|
| 1 | [Setup](./01-setup.md) | Install the framework, set API keys, verify installation |
| 2 | [Running Agents](./02-running-agents.md) | One-shot run, terminal chat, browser UI |
| 3 | [Creating Agents](./03-creating-agents.md) | Define agents in YAML, choose a backend |
| 4 | [Tools](./04-tools.md) | Use the docs crawler, write custom tools |
| 5 | [Multi-Agent Pipelines](./05-pipelines.md) | Chain agents with sequential, group chat, or supervisor |
| 6 | [Deployment](./06-deployment.md) | Deploy locally, to Docker, or Azure Container Apps |

---

## 5-Minute Quick Start

```bash
# 1. Install everything in one shot
pip install -e ".[all]"

# 2. Set API key
export OPENAI_API_KEY=sk-...

# 3. List available agents
agent list agents/

# 4. Chat in terminal
agent chat agents/docs_reader.yaml

# 5. Or open the browser UI
pip install gradio
agent ui agents/docs_reader.yaml
```

---

## Supported Backends

| Backend | Install extra | Best for |
|---------|--------------|----------|
| AutoGen | `.[autogen]` | Multi-agent collaboration, code execution |
| Semantic Kernel | `.[semantic-kernel]` | Plugin-based agents, app integration |
| Azure AI Agent Service | `.[azure]` | Managed cloud agents, enterprise |

---

## Project Structure

```
ms-ai-agent-framework/
├── agent_framework/
│   ├── cli.py                  # CLI: agent run / chat / ui / deploy ...
│   ├── config/                 # YAML/JSON schema + loader
│   ├── core/                   # BaseAgent, ToolRegistry, Pipeline
│   ├── backends/               # AutoGen, Semantic Kernel, Azure adapters
│   ├── deploy/                 # Local, Docker, Azure deployers
│   └── observability/          # Structured logging + OpenTelemetry
├── agents/                     # Agent YAML config files
│   ├── docs_reader.yaml
│   ├── example_coder.yaml
│   ├── example_research.yaml
│   ├── example_azure.yaml
│   └── example_pipeline.yaml
├── tools/                      # Tool/plugin Python files
│   ├── docs_crawler.py         # Fetch + crawl web pages
│   └── web_search.py           # Web search stub
├── tests/                      # 30 unit tests
├── docs/                       # This documentation
├── Dockerfile
├── pyproject.toml
└── README.md
```
