"""
Docs crawler tool — fetch content from URLs and recursively follow sublinks.

Tools exposed:
  fetch_page(url)                          Fetch a single page, return cleaned text + found links
  crawl_docs(urls, max_depth, max_pages)   Recursively crawl from seed URLs, return all content
  summarise_crawl(crawl_result)            Format a crawl result dict into a readable summary
"""

from __future__ import annotations

import re
import time
from collections import deque
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from agent_framework.core.tool_registry import register_tool

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("Install crawl dependencies: pip install requests beautifulsoup4")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "ms-ai-agent-framework/0.1 (docs-reader)"
})

_SKIP_EXTENSIONS = {
    ".pdf", ".zip", ".tar", ".gz", ".png", ".jpg", ".jpeg",
    ".gif", ".svg", ".mp4", ".mp3", ".exe", ".dmg",
}


def _same_origin(base: str, url: str) -> bool:
    """Return True if *url* shares the same scheme+host as *base*."""
    b, u = urlparse(base), urlparse(url)
    return b.scheme == u.scheme and b.netloc == u.netloc


def _skip_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in _SKIP_EXTENSIONS)


def _clean_text(soup: BeautifulSoup) -> str:
    """Extract readable text from a BeautifulSoup document."""
    # Remove noisy tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    # Prefer <main> or <article> content if present
    main = soup.find("main") or soup.find("article") or soup.find(id=re.compile(r"content|main", re.I))
    target = main if main else soup.body or soup

    lines = []
    for elem in target.descendants:
        if elem.name in ("h1", "h2", "h3", "h4"):
            lines.append(f"\n## {elem.get_text(strip=True)}\n")
        elif elem.name == "li":
            lines.append(f"  - {elem.get_text(strip=True)}")
        elif elem.name == "p":
            text = elem.get_text(strip=True)
            if text:
                lines.append(text)
        elif elem.name == "code":
            lines.append(f"`{elem.get_text(strip=True)}`")
        elif elem.name == "pre":
            lines.append(f"\n```\n{elem.get_text(strip=True)}\n```\n")

    return "\n".join(lines).strip()


def _extract_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Return all absolute href links found on the page."""
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        full = urljoin(base_url, href)
        # Strip fragment
        full = full.split("#")[0]
        if full and not _skip_url(full):
            links.append(full)
    return list(dict.fromkeys(links))  # deduplicate while preserving order


# ---------------------------------------------------------------------------
# Public tools
# ---------------------------------------------------------------------------

@register_tool
def fetch_page(url: str) -> Dict[str, Any]:
    """
    Fetch a single web page and return its text content and all links found on it.

    Returns a dict:
      {
        "url": str,
        "title": str,
        "content": str,      # cleaned readable text
        "links": List[str],  # all absolute links found on the page
        "error": str | None
      }
    """
    try:
        resp = _SESSION.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title else url
        content = _clean_text(soup)
        links = _extract_links(soup, url)
        return {"url": url, "title": title, "content": content, "links": links, "error": None}
    except Exception as exc:
        return {"url": url, "title": "", "content": "", "links": [], "error": str(exc)}


@register_tool
def crawl_docs(
    urls: List[str],
    max_depth: int = 2,
    max_pages: int = 20,
    stay_on_origin: bool = True,
    delay_seconds: float = 0.3,
) -> Dict[str, Any]:
    """
    Recursively crawl documentation starting from *urls*.

    Follows sublinks up to *max_depth* levels deep and collects at most *max_pages* pages.

    Args:
        urls:             Seed URLs to start crawling from.
        max_depth:        How many link-hops to follow from each seed (default 2).
        max_pages:        Maximum total pages to fetch (default 20).
        stay_on_origin:   If True, only follow links on the same domain as each seed (default True).
        delay_seconds:    Polite delay between requests (default 0.3s).

    Returns a dict:
      {
        "pages": [{"url", "title", "content", "depth"}, ...],
        "skipped": [url, ...],   # pages that failed or were over limit
        "total_fetched": int
      }
    """
    visited: set[str] = set()
    # queue items: (url, depth, origin_url)
    queue: deque[tuple[str, int, str]] = deque()

    for seed in urls:
        seed = seed.split("#")[0]
        queue.append((seed, 0, seed))

    pages: List[Dict[str, Any]] = []
    skipped: List[str] = []

    while queue and len(pages) < max_pages:
        url, depth, origin = queue.popleft()

        if url in visited:
            continue
        if _skip_url(url):
            skipped.append(url)
            continue

        visited.add(url)
        result = fetch_page(url)

        if result["error"]:
            skipped.append(url)
            continue

        pages.append({
            "url": url,
            "title": result["title"],
            "content": result["content"],
            "depth": depth,
        })

        # Enqueue sublinks if we haven't hit max depth
        if depth < max_depth:
            for link in result["links"]:
                if link not in visited:
                    if stay_on_origin and not _same_origin(origin, link):
                        continue
                    queue.append((link, depth + 1, origin))

        if delay_seconds > 0:
            time.sleep(delay_seconds)

    # Any remaining queue items that weren't fetched due to max_pages
    skipped.extend(item[0] for item in queue if item[0] not in visited)

    return {
        "pages": pages,
        "skipped": list(dict.fromkeys(skipped)),
        "total_fetched": len(pages),
    }


@register_tool
def summarise_crawl(crawl_result: Dict[str, Any]) -> str:
    """
    Format the output of crawl_docs() into a single readable text document
    suitable for the agent to analyse and summarise.

    Returns a Markdown-formatted string with all page contents.
    """
    pages = crawl_result.get("pages", [])
    if not pages:
        return "No pages were fetched."

    sections = []
    for page in pages:
        depth_label = "  " * page["depth"]
        header = f"{depth_label}# [{page['title']}]({page['url']})  _(depth {page['depth']})_"
        sections.append(f"{header}\n\n{page['content']}")

    footer = (
        f"\n\n---\n_Crawled {len(pages)} pages. "
        f"Skipped {len(crawl_result.get('skipped', []))} pages._"
    )
    return "\n\n---\n\n".join(sections) + footer
