# Multi-Agent Pipelines

Pipelines let you chain multiple agents together so they collaborate on a task.
Each agent specialises in one thing — one researches, one writes code, one reviews.

---

## How It Works

```
Your task
    │
    ▼
Pipeline (orchestrator)
    │
    ├── Agent A  ──► output ──► Agent B  ──► output ──► Agent C
    │   (researcher)            (coder)                 (reviewer)
    │
    ▼
Final result
```

---

## Pipeline Config

Create a YAML file that lists agent names and a strategy:

```yaml
# agents/my_pipeline.yaml
name: research-then-code
agents:
  - research-agent       # must match name: in agents/research-agent.yaml
  - coder-agent          # must match name: in agents/coder-agent.yaml
strategy: sequential     # sequential | group_chat | supervisor
```

Run it:

```bash
agent pipeline run agents/my_pipeline.yaml "Research Python async patterns and implement an example"
```

---

## Three Strategies

### 1. `sequential` — Chain outputs

Each agent's response becomes the next agent's input.

```
Task → Agent A → [A's output] → Agent B → [B's output] → Agent C → Final result
```

```yaml
name: research-then-code
agents:
  - research-agent
  - coder-agent
strategy: sequential
```

**Best for:** Linear workflows — research → write → review, translate → summarise, etc.

---

### 2. `group_chat` — All agents collaborate

All agents join an AutoGen GroupChat and take turns responding until the task is done.

```
Task
 ├── research-agent: "Here are the key facts..."
 ├── coder-agent: "Based on that, here's the code..."
 ├── reviewer-agent: "I found a bug on line 5..."
 ├── coder-agent: "Fixed. Here's the updated version..."
 └── [done after max_rounds]
```

```yaml
name: collaborative-team
agents:
  - research-agent
  - coder-agent
  - reviewer-agent
strategy: group_chat
max_rounds: 12
```

> **Note:** `group_chat` works best when all agents use the `autogen` backend.

---

### 3. `supervisor` — Smart routing

A supervisor agent reads the task and decides which specialist should handle it.

```
Task → Supervisor: "This is a coding task → route to coder-agent"
                          │
                          ▼
                    coder-agent → Final result
```

```yaml
name: smart-router
agents:
  - supervisor
  - coder-agent
  - research-agent
  - data-analyst
strategy: supervisor
supervisor_agent: supervisor   # must be one of the agents listed above
```

The supervisor agent's `instructions` should describe all available specialists so it can route correctly:

```yaml
# agents/supervisor.yaml
name: supervisor
backend: semantic_kernel
instructions: |
  You are a routing supervisor. Available specialists:
  - coder-agent: writes Python code and fixes bugs
  - research-agent: researches topics and summarises information
  - data-analyst: analyses datasets and creates visualisations

  When given a task, reply with ONLY the name of the specialist
  that should handle it. Nothing else.
```

---

## Full Config Reference

```yaml
name: my-pipeline           # Unique pipeline name
agents:
  - agent-one               # Listed in order (used for sequential strategy)
  - agent-two
  - agent-three
strategy: sequential        # sequential | group_chat | supervisor
max_rounds: 10              # Max conversation rounds (group_chat / supervisor only)
supervisor_agent: agent-one # Required when strategy is 'supervisor'
```

---

## Example: Research → Code Pipeline

**`agents/research-agent.yaml`:**
```yaml
name: research-agent
backend: semantic_kernel
instructions: |
  You are a research assistant. When given a topic, provide a clear
  technical summary including key concepts and best practices.
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
tools:
  - name: web_search
    module: tools.web_search
    function: search_web
```

**`agents/coder-agent.yaml`:**
```yaml
name: coder-agent
backend: autogen
instructions: |
  You are a Python developer. Given a technical brief, write clean,
  well-commented, runnable Python code that demonstrates the concepts.
llm:
  model: gpt-4o
  api_key_env: OPENAI_API_KEY
```

**`agents/research-then-code.yaml`:**
```yaml
name: research-then-code
agents:
  - research-agent
  - coder-agent
strategy: sequential
```

**Run:**
```bash
agent pipeline run agents/research-then-code.yaml \
  "Python asyncio — key patterns for concurrent HTTP requests"
```

What happens:
1. `research-agent` researches the topic and produces a summary
2. `coder-agent` receives that summary and writes example code

---

## Running a Pipeline

```bash
agent pipeline run <pipeline-config> "<task>" [--agents-dir <dir>]
```

| Option | Default | Description |
|--------|---------|-------------|
| `pipeline-config` | required | Path to pipeline YAML file |
| `task` | required | The task/question to solve |
| `--agents-dir` | `agents/` | Directory containing agent YAML files |

```bash
# Default — looks for agent configs in agents/
agent pipeline run agents/research-then-code.yaml "Explain Python decorators"

# Custom agents directory
agent pipeline run pipelines/my-pipeline.yaml "..." --agents-dir my-agents/
```

---

## Next Steps

- [Deployment](./06-deployment.md) — deploy pipelines to production
- [Setup Guide](./01-setup.md) — back to installation
