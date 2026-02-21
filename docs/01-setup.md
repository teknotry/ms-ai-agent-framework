# Setup Guide

This guide walks you through installing and configuring **ms-ai-agent-framework** from scratch.

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.10 or higher | `python --version` |
| pip | latest | `pip --version` |
| OpenAI API key | — | [platform.openai.com](https://platform.openai.com) |

> **Azure users only:** You also need an Azure subscription and an [Azure AI Foundry](https://ai.azure.com) project to use the `azure` backend.

---

## Step 1 — Clone or Download the Project

```bash
# If you have the folder already
cd /path/to/ms-ai-agent-framework

# Or clone from your repo
git clone <your-repo-url>
cd ms-ai-agent-framework
```

---

## Step 2 — Install the Framework

The framework uses optional extras so you only install what you need.

```bash
# Core only (CLI + config, no agent backend)
pip install -e "."

# AutoGen backend (multi-agent, code execution)
pip install -e ".[autogen]"

# Semantic Kernel backend (plugin-based agents)
pip install -e ".[semantic-kernel]"

# Azure AI Agent Service backend
pip install -e ".[azure]"

# Gradio browser UI
pip install -e ".[ui]"

# Install everything at once (recommended for development)
pip install -e ".[all]"
```

Also install the docs crawler dependencies (used by the built-in docs reader agent):

```bash
pip install requests beautifulsoup4
```

---

## Step 3 — Set API Keys

### OpenAI

```bash
export OPENAI_API_KEY=sk-...
```

To make this permanent, add it to your shell profile:

```bash
# macOS / Linux (zsh)
echo 'export OPENAI_API_KEY=sk-...' >> ~/.zshrc
source ~/.zshrc

# macOS / Linux (bash)
echo 'export OPENAI_API_KEY=sk-...' >> ~/.bashrc
source ~/.bashrc
```

### Azure OpenAI (optional)

If you are using Azure OpenAI instead of OpenAI, set these instead:

```bash
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
export AZURE_OPENAI_API_VERSION=2024-02-01
```

Then in your agent YAML, set:

```yaml
llm:
  model: gpt-4o           # your Azure deployment name
  api_key_env: AZURE_OPENAI_API_KEY
  base_url: https://<your-resource>.openai.azure.com/
  api_version: "2024-02-01"
```

### Azure AI Agent Service (optional)

```bash
export AZURE_AI_PROJECT_CONNECTION_STRING="<connection string from Azure AI Foundry>"
```

Find the connection string in: **Azure AI Foundry portal → your project → Overview → Project connection string**

---

## Step 4 — Verify Installation

```bash
# Check the CLI is available
agent --version

# List all built-in example agents
agent list agents/
```

Expected output:

```
NAME                      BACKEND            MODEL           FILE
--------------------------------------------------------------------------------
azure-assistant           azure              gpt-4o          agents/example_azure.yaml
coder-agent               autogen            gpt-4o          agents/example_coder.yaml
research-agent            semantic_kernel    gpt-4o          agents/example_research.yaml
```

---

## Step 5 — Run Tests

```bash
python -m pytest tests/ -v
```

All 30 tests should pass. If any fail, check that your dependencies are installed correctly.

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (OpenAI) | OpenAI API key |
| `AZURE_OPENAI_API_KEY` | Yes (Azure OpenAI) | Azure OpenAI API key |
| `AZURE_AI_PROJECT_CONNECTION_STRING` | Yes (azure backend) | Azure AI Foundry connection string |
| `AZURE_RESOURCE_GROUP` | For `agent deploy azure` | Azure resource group name |
| `AZURE_SUBSCRIPTION_ID` | For `agent deploy azure` | Azure subscription ID |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OpenTelemetry collector endpoint |
| `AGENT_DEBUG` | No | Set to `1` for verbose debug logging |

---

## Next Steps

- [Running Agents](./02-running-agents.md) — run, chat, and use the browser UI
- [Creating Agents](./03-creating-agents.md) — define your own agents
- [Built-in Tools](./04-tools.md) — docs crawler and custom tools
- [Multi-Agent Pipelines](./05-pipelines.md) — orchestrate multiple agents
- [Deployment](./06-deployment.md) — local, Docker, and Azure deployment
