# Running Agents

There are three ways to interact with an agent:

| Mode | Command | Best for |
|------|---------|----------|
| **One-shot** | `agent run` | Scripts, automation, single questions |
| **Terminal chat** | `agent chat` | Development, quick exploration |
| **Browser UI** | `agent ui` | Demos, sharing with non-technical users |

---

## One-Shot Run

Send a single message and get one response. The agent exits immediately after.

```bash
agent run agents/example_research.yaml "What is Semantic Kernel?"
```

Output:
```
Running agent 'research-agent' [semantic_kernel]...

--- Response ---
Semantic Kernel is an open-source SDK from Microsoft that lets you integrate
large language models (LLMs) into your applications...
```

**When to use:** Automation pipelines, CI/CD steps, scripting.

---

## Terminal Chat Loop

Start a back-and-forth conversation that maintains context between messages.

```bash
agent chat agents/example_research.yaml
```

```
Chatting with 'research-agent' [semantic_kernel]
Type 'exit' or 'quit' to stop. Type 'reset' to clear conversation history.

You: What is FastAPI?
Agent: FastAPI is a modern Python web framework...

You: How does it handle authentication?
Agent: FastAPI supports several authentication methods including...

You: reset
[Conversation history cleared]

You: exit
Goodbye!
```

### Chat Commands

| Command | Action |
|---------|--------|
| `exit` or `quit` | End the session |
| `reset` | Clear conversation history (start fresh) |
| `Ctrl+C` | Force quit |

### Options

```bash
# Disable coloured output (useful for logging or piping)
agent chat agents/example_research.yaml --no-color
```

---

## Browser UI (Gradio)

Launches a full chat interface in your browser — no terminal needed after launch.

### Install Gradio

```bash
pip install gradio
# or
pip install -e ".[ui]"
```

### Launch

```bash
agent ui agents/example_research.yaml
```

The browser opens automatically at `http://localhost:7860`.

### What the UI looks Like

```
┌─────────────────────────────────────────────────────┐
│  research-agent                                     │
│  Backend: semantic_kernel  |  Model: gpt-4o         │
│  You are a research assistant...                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│   [Chat history]                                    │
│                                                     │
│   You:   What is AutoGen?                           │
│   Agent: AutoGen is Microsoft's open-source...      │
│                                                     │
├─────────────────────────────┬───────────────────────┤
│  Type your message...       │       Send            │
├─────────────────────────────┴───────────────────────┤
│  Reset conversation                                 │
└─────────────────────────────────────────────────────┘
```

### Options

```bash
# Use a different port
agent ui agents/example_research.yaml --port 8888

# Create a public shareable URL (via Gradio cloud)
agent ui agents/example_research.yaml --share
```

> **Note:** `--share` creates a temporary public URL (valid for 72 hours) that anyone can access. Useful for demos.

---

## Running the Docs Reader Agent

The built-in `docs_reader` agent can crawl and summarise any documentation website.

```bash
agent chat agents/docs_reader.yaml
```

Example conversation:

```
You: Read and summarise https://fastapi.tiangolo.com
Agent: [crawls the page and sublinks...]
       FastAPI is a modern, fast web framework for building APIs with Python...
       Key features:
         - Automatic OpenAPI docs
         - Type hint-based validation
         ...

You: What does it say about dependency injection?
Agent: Based on the docs I just read, FastAPI has a powerful dependency
       injection system...

You: Now also read https://flask.palletsprojects.com and compare the two
Agent: [crawls Flask docs...]
       Comparing FastAPI and Flask:
       | Feature | FastAPI | Flask |
       ...
```

---

## Running a Pipeline (Multiple Agents)

```bash
agent pipeline run agents/example_pipeline.yaml \
  "Research Python async patterns and write example code"
```

See [Multi-Agent Pipelines](./05-pipelines.md) for details.

---

## Next Steps

- [Creating Agents](./03-creating-agents.md) — define your own agents
- [Built-in Tools](./04-tools.md) — docs crawler and custom tools
- [Multi-Agent Pipelines](./05-pipelines.md) — orchestrate multiple agents
