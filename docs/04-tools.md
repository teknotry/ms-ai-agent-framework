# Tools

Tools are Python functions that agents can call to interact with the outside world —
search the web, read files, call APIs, run calculations, and more.

---

## How Tools Work

```
User message
     │
     ▼
   Agent (LLM)
     │  decides to call a tool
     ▼
 Tool function runs  ──► returns result
     │
     ▼
   Agent (LLM)
     │  uses result to form response
     ▼
   Response to user
```

Tools are plain Python functions. The framework automatically:
1. Loads them from the module path in your agent YAML
2. Passes them to the backend (AutoGen / Semantic Kernel / Azure)
3. Lets the LLM decide when and how to call them

---

## Built-in Tool: Docs Crawler

Located at [tools/docs_crawler.py](../tools/docs_crawler.py).

### `fetch_page(url)`

Fetches a single web page and returns cleaned text plus all links found on it.

```python
from tools.docs_crawler import fetch_page

result = fetch_page("https://fastapi.tiangolo.com")
print(result["title"])     # "FastAPI - FastAPI"
print(result["content"])   # cleaned text of the page
print(result["links"])     # list of all absolute URLs found on the page
print(result["error"])     # None if successful, error message if failed
```

**Returns:**
```python
{
    "url": "https://fastapi.tiangolo.com",
    "title": "FastAPI",
    "content": "## FastAPI\n\nFastAPI is a modern...",
    "links": ["https://fastapi.tiangolo.com/tutorial/", ...],
    "error": None
}
```

---

### `crawl_docs(urls, max_depth, max_pages, stay_on_origin, delay_seconds)`

Recursively crawls from seed URLs, following sublinks up to `max_depth` levels deep.

```python
from tools.docs_crawler import crawl_docs

result = crawl_docs(
    urls=["https://fastapi.tiangolo.com/tutorial/"],
    max_depth=2,           # follow links 2 levels deep (default: 2)
    max_pages=20,          # stop after 20 pages total (default: 20)
    stay_on_origin=True,   # only follow links on same domain (default: True)
    delay_seconds=0.3,     # polite delay between requests (default: 0.3)
)
print(f"Fetched {result['total_fetched']} pages")
```

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `urls` | required | List of seed URLs to start crawling from |
| `max_depth` | `2` | How many link-hops to follow |
| `max_pages` | `20` | Max total pages to fetch |
| `stay_on_origin` | `True` | Only follow links on the same domain |
| `delay_seconds` | `0.3` | Seconds to wait between requests |

**Returns:**
```python
{
    "pages": [
        {"url": "...", "title": "...", "content": "...", "depth": 0},
        {"url": "...", "title": "...", "content": "...", "depth": 1},
    ],
    "skipped": ["https://example.com/large-file.pdf", ...],
    "total_fetched": 5
}
```

---

### `summarise_crawl(crawl_result)`

Formats the output of `crawl_docs()` into a single Markdown document.

```python
from tools.docs_crawler import crawl_docs, summarise_crawl

result = crawl_docs(urls=["https://fastapi.tiangolo.com"])
markdown = summarise_crawl(result)
print(markdown)
```

Output format:
```markdown
# [FastAPI](https://fastapi.tiangolo.com)  _(depth 0)_

## Introduction
FastAPI is a modern, fast web framework...

---

  # [Tutorial](https://fastapi.tiangolo.com/tutorial/)  _(depth 1)_

  ## First Steps
  ...

---
_Crawled 5 pages. Skipped 2 pages._
```

---

## Writing a Custom Tool

### Step 1 — Create a file in `tools/`

```python
# tools/my_tools.py
from agent_framework.core.tool_registry import register_tool


@register_tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Replace with a real API call
    return f"Weather in {city}: Sunny, 22°C"


@register_tool
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression. Example: '2 + 2 * 10'"""
    allowed = {k: v for k, v in __builtins__.items()
               if k in ("abs", "round", "min", "max", "sum", "pow")}
    try:
        return str(eval(expression, {"__builtins__": allowed}))
    except Exception as e:
        return f"Error: {e}"
```

### Step 2 — Reference it in your agent YAML

```yaml
tools:
  - name: get_weather
    module: tools.my_tools
    function: get_weather
    description: Get the current weather forecast for any city

  - name: calculate
    module: tools.my_tools
    function: calculate
    description: Evaluate a mathematical expression
```

### Step 3 — Run the agent

```bash
agent chat agents/my-agent.yaml
# You: What's the weather in London?
# Agent: [calls get_weather("London")]
#        The weather in London is Sunny, 22°C.
```

---

## Tool Guidelines

| Do | Don't |
|----|-------|
| Write a clear `"""docstring"""` — the LLM reads it to decide when to call the tool | Leave the docstring blank |
| Return a string (or something easily serialisable) | Return complex objects the LLM can't read |
| Handle exceptions inside the tool and return an error string | Let exceptions bubble up unhandled |
| Keep each tool focused on one thing | Put too much logic in one tool |

---

## Using Tools Directly in Python

You can use any tool in your own scripts without running an agent:

```python
from tools.docs_crawler import crawl_docs, summarise_crawl
from tools.web_search import search_web

# Crawl docs
result = crawl_docs(["https://docs.python.org/3/"], max_depth=1, max_pages=5)
print(summarise_crawl(result))

# Web search (stub — replace with real API)
print(search_web("python asyncio tutorial"))
```

---

## Next Steps

- [Multi-Agent Pipelines](./05-pipelines.md) — use tools across multiple agents
- [Deployment](./06-deployment.md) — deploy agents with tools to production
