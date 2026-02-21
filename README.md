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
pip install -e ".[autogen,semantic-kernel]"   # AutoGen + Semantic Kernel backends
pip install -e ".[ui]"                         # Gradio browser UI
pip install -e ".[all]"                        # Everything

# Scaffold a new project
agent init my-project
cd my-project

# Run an agent (one-shot)
export OPENAI_API_KEY=sk-...
agent run agents/example_agent.yaml "Write a hello world function in Python"

# Or start an interactive chat
agent chat agents/example_agent.yaml

# Or open the browser UI
agent ui agents/example_agent.yaml
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
agent init [PROJECT_DIR]                        Scaffold a new project
agent create <name> --backend <b>               Create agent config template
agent run <config.yaml> "<message>"             Run a single agent (one-shot)
agent chat <config.yaml>                        Interactive terminal chat loop
agent ui <config.yaml>                          Launch Gradio browser chat UI
agent pipeline run <pipeline.yaml> "<task>"     Run a multi-agent pipeline
agent deploy local <config.yaml>                Run as local HTTP server
agent deploy docker <config.yaml>               Build & run in Docker
agent deploy azure <config.yaml>                Deploy to Azure Container Apps
agent list [agents-dir]                         List all agent configs
agent logs <agent-name>                         Stream logs
```

---

## Interactive Chat

### Terminal Chat Loop

Start a back-and-forth conversation with any agent directly in your terminal:

```bash
agent chat agents/my_agent.yaml
```

```
Chatting with 'my-agent' [semantic_kernel]
Type 'exit' or 'quit' to stop. Type 'reset' to clear conversation history.

You: Summarise https://fastapi.tiangolo.com
Agent: FastAPI is a modern, fast web framework...

You: What authentication methods does it support?
Agent: Based on the docs I crawled, FastAPI supports OAuth2, API keys...

You: reset
[Conversation history cleared]

You: exit
Goodbye!
```

**Options:**
```bash
agent chat agents/my_agent.yaml --no-color   # plain output, no colours
```

---

### Gradio Browser UI

Launch a chat window in your browser:

```bash
# Install Gradio
pip install gradio
# or: pip install -e ".[ui]"

agent ui agents/my_agent.yaml
# → opens http://localhost:7860 automatically
```

**Options:**
```bash
agent ui agents/my_agent.yaml --port 8888    # custom port
agent ui agents/my_agent.yaml --share        # create a public Gradio share URL
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

## Built-in Tools

### Docs Crawler (`tools/docs_crawler.py`)

Reads documentation from URLs and recursively follows sublinks.

| Tool | Description |
|------|-------------|
| `fetch_page(url)` | Fetch a single page — returns cleaned text + all links found |
| `crawl_docs(urls, max_depth, max_pages, ...)` | Recursively crawl from seed URLs |
| `summarise_crawl(result)` | Format crawl output into readable Markdown |

**Use via the docs-reader agent:**
```bash
agent chat agents/docs_reader.yaml
# You: Read and summarise https://docs.python.org/3/library/asyncio.html
```

**Use directly in Python:**
```python
from tools.docs_crawler import crawl_docs, summarise_crawl

result = crawl_docs(
    urls=["https://fastapi.tiangolo.com/tutorial/"],
    max_depth=2,       # follow links 2 levels deep
    max_pages=20,      # fetch at most 20 pages total
    stay_on_origin=True,  # only follow links on the same domain
    delay_seconds=0.3,    # polite delay between requests
)
print(f"Fetched {result['total_fetched']} pages")
print(summarise_crawl(result))
```

**Agent config reference (`agents/docs_reader.yaml`):**
```yaml
name: docs-reader-agent
backend: semantic_kernel
instructions: "You are a documentation expert..."
tools:
  - name: fetch_page
    module: tools.docs_crawler
    function: fetch_page
  - name: crawl_docs
    module: tools.docs_crawler
    function: crawl_docs
  - name: summarise_crawl
    module: tools.docs_crawler
    function: summarise_crawl
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
