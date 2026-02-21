# Creating Agents

Agents are defined in YAML config files stored in the `agents/` folder.
Each file maps to one agent and specifies which backend powers it, what model it uses,
its instructions (system prompt), and which tools it can call.

---

## Quick Way — Use the CLI

```bash
agent create my-assistant --backend semantic_kernel
```

This generates `agents/my-assistant.yaml` with a ready-to-edit template:

```yaml
name: my-assistant
backend: semantic_kernel
instructions: "You are a helpful assistant named my-assistant."
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
tools: []
max_turns: 10
```

Run it immediately:

```bash
agent chat agents/my-assistant.yaml
```

---

## Full Config Reference

```yaml
# agents/my_agent.yaml

# --- Required ---
name: my-agent                        # Unique name (used in pipelines and logs)
backend: semantic_kernel              # autogen | semantic_kernel | azure
instructions: |                       # System prompt — defines the agent's role
  You are an expert Python developer.
  Write clean, well-documented code.

# --- LLM settings ---
llm:
  model: gpt-4o                       # Model name
  api_key_env: OPENAI_API_KEY         # Env var that holds your API key
  base_url: null                      # Custom endpoint (e.g. Azure OpenAI URL)
  api_version: null                   # API version (Azure OpenAI only)
  temperature: 0.1                    # 0.0 = deterministic, 2.0 = creative
  max_tokens: null                    # Limit response length (null = model default)

# --- Tools ---
tools:
  - name: web_search                  # Name the agent uses to call this tool
    module: tools.web_search          # Python module path
    function: search_web              # Function name inside the module
    description: Search the web       # Shown to the LLM to decide when to use it

# --- Behaviour ---
max_turns: 10                         # Max back-and-forth rounds before stopping
human_input: false                    # If true, agent pauses and waits for your input each turn

# --- Azure-specific built-in tools (azure backend only) ---
azure_builtin_tools:
  - code_interpreter                  # Run Python code in a sandbox
  - file_search                       # Search uploaded files
  - bing_grounding                    # Real-time web search via Bing

# --- Backend-specific extras (optional) ---
extra:
  code_execution_config:              # AutoGen only: enable code execution
    work_dir: .agent_code   # relative path — works on Windows and Unix
    use_docker: false
```

---

## Choosing a Backend

### `autogen` — Multi-agent, code execution

```yaml
name: coder-agent
backend: autogen
instructions: |
  You are an expert Python developer. Write and test code to solve problems.
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
extra:
  code_execution_config:
    work_dir: .agent_code   # relative path — works on Windows and Unix
    use_docker: false
```

Best for:
- Writing and running code automatically
- Multi-agent group chats (see [Pipelines](./05-pipelines.md))
- Tasks that need iterative refinement

---

### `semantic_kernel` — Plugin-based, single agent

```yaml
name: research-agent
backend: semantic_kernel
instructions: |
  You are a research assistant. Summarise topics clearly in bullet points.
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  temperature: 0.2
tools:
  - name: web_search
    module: tools.web_search
    function: search_web
```

Best for:
- Single agents with tools/plugins
- Embedding AI into an existing application
- When you want fine control over tool usage

---

### `azure` — Managed cloud agent

```yaml
name: azure-assistant
backend: azure
instructions: |
  You are a helpful assistant. Use your tools to answer questions accurately.
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
azure_builtin_tools:
  - code_interpreter
  - file_search
```

Best for:
- Production deployments on Azure
- Agents that need to analyse uploaded files
- Enterprise requirements (compliance, RBAC, scaling)

Requires:
```bash
export AZURE_AI_PROJECT_CONNECTION_STRING="..."
pip install -e ".[azure]"
```

---

## Example: Docs Reader Agent

```yaml
# agents/docs_reader.yaml
name: docs-reader-agent
backend: semantic_kernel
instructions: |
  You are a documentation expert. When given URLs:
  1. Use crawl_docs to fetch all pages and sublinks.
  2. Use summarise_crawl to format the content.
  3. Provide a structured summary with key concepts, getting started steps,
     and important notes. Always cite source URLs.
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
  temperature: 0.1
tools:
  - name: fetch_page
    module: tools.docs_crawler
    function: fetch_page
    description: Fetch a single web page and return its text and links
  - name: crawl_docs
    module: tools.docs_crawler
    function: crawl_docs
    description: Recursively crawl documentation from seed URLs
  - name: summarise_crawl
    module: tools.docs_crawler
    function: summarise_crawl
    description: Format crawled pages into a readable Markdown document
max_turns: 15
```

---

## Example: Azure OpenAI (instead of OpenAI)

```yaml
name: azure-openai-agent
backend: semantic_kernel
instructions: "You are a helpful assistant."
llm:
  model: gpt-4o                              # Your Azure deployment name
  api_key_env: AZURE_OPENAI_API_KEY
  base_url: https://<resource>.openai.azure.com/
  api_version: "2024-02-01"
```

---

## Next Steps

- [Built-in Tools](./04-tools.md) — use and write tools
- [Multi-Agent Pipelines](./05-pipelines.md) — chain agents together
- [Deployment](./06-deployment.md) — run in production
