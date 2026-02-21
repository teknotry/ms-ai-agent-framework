"""
Example web search tool.

Replace the body of search_web() with a real search API call
(e.g. Bing Search API, SerpAPI, Tavily) for production use.
"""

from agent_framework.core.tool_registry import register_tool


@register_tool
def search_web(query: str) -> str:
    """Search the web for *query* and return a text summary of the results."""
    # TODO: integrate a real search API
    # Example with Bing:
    #   import requests
    #   resp = requests.get(
    #       "https://api.bing.microsoft.com/v7.0/search",
    #       headers={"Ocp-Apim-Subscription-Key": os.environ["BING_API_KEY"]},
    #       params={"q": query, "count": 5},
    #   )
    #   results = resp.json().get("webPages", {}).get("value", [])
    #   return "\n".join(f"{r['name']}: {r['snippet']}" for r in results)
    return f"[stub] Search results for: {query}"
