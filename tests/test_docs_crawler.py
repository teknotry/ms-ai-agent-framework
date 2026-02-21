"""Tests for the docs_crawler tool."""

from unittest.mock import MagicMock, patch
import pytest

from tools.docs_crawler import fetch_page, crawl_docs, summarise_crawl, _clean_text, _extract_links


SAMPLE_HTML = """
<html>
<head><title>Test Docs Page</title></head>
<body>
  <main>
    <h1>Getting Started</h1>
    <p>Welcome to the docs.</p>
    <h2>Installation</h2>
    <p>Run pip install mylib to install.</p>
    <ul>
      <li>Feature A</li>
      <li>Feature B</li>
    </ul>
    <a href="/guide">User Guide</a>
    <a href="https://external.com/page">External Link</a>
    <a href="#section">Anchor (skip)</a>
  </main>
</body>
</html>
"""


def _mock_response(html: str, url: str = "https://example.com"):
    mock = MagicMock()
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# fetch_page
# ---------------------------------------------------------------------------

@patch("tools.docs_crawler._SESSION")
def test_fetch_page_success(mock_session):
    mock_session.get.return_value = _mock_response(SAMPLE_HTML)
    result = fetch_page("https://example.com")

    assert result["error"] is None
    assert result["title"] == "Test Docs Page"
    assert "Getting Started" in result["content"]
    assert "Welcome to the docs" in result["content"]
    assert "https://example.com/guide" in result["links"]
    assert "https://external.com/page" in result["links"]
    # Anchor links should be excluded
    assert not any("#" in link for link in result["links"])


@patch("tools.docs_crawler._SESSION")
def test_fetch_page_error(mock_session):
    mock_session.get.side_effect = Exception("connection timeout")
    result = fetch_page("https://unreachable.example.com")

    assert result["error"] == "connection timeout"
    assert result["content"] == ""
    assert result["links"] == []


# ---------------------------------------------------------------------------
# crawl_docs
# ---------------------------------------------------------------------------

@patch("tools.docs_crawler.fetch_page")
def test_crawl_single_page_no_depth(mock_fetch):
    mock_fetch.return_value = {
        "url": "https://docs.example.com",
        "title": "Home",
        "content": "Home content",
        "links": ["https://docs.example.com/page1", "https://docs.example.com/page2"],
        "error": None,
    }
    result = crawl_docs(["https://docs.example.com"], max_depth=0, max_pages=5)
    assert result["total_fetched"] == 1
    assert result["pages"][0]["depth"] == 0


@patch("tools.docs_crawler.fetch_page")
def test_crawl_follows_sublinks(mock_fetch):
    def side_effect(url):
        responses = {
            "https://docs.example.com": {
                "url": url, "title": "Home", "content": "home",
                "links": ["https://docs.example.com/guide"],
                "error": None,
            },
            "https://docs.example.com/guide": {
                "url": url, "title": "Guide", "content": "guide content",
                "links": [],
                "error": None,
            },
        }
        return responses.get(url, {"url": url, "title": "", "content": "", "links": [], "error": "not found"})

    mock_fetch.side_effect = side_effect
    result = crawl_docs(["https://docs.example.com"], max_depth=1, max_pages=10, delay_seconds=0)

    urls_fetched = [p["url"] for p in result["pages"]]
    assert "https://docs.example.com" in urls_fetched
    assert "https://docs.example.com/guide" in urls_fetched
    assert result["total_fetched"] == 2


@patch("tools.docs_crawler.fetch_page")
def test_crawl_respects_max_pages(mock_fetch):
    mock_fetch.return_value = {
        "url": "https://docs.example.com",
        "title": "Page",
        "content": "content",
        "links": [f"https://docs.example.com/page{i}" for i in range(50)],
        "error": None,
    }
    result = crawl_docs(["https://docs.example.com"], max_depth=2, max_pages=3, delay_seconds=0)
    assert result["total_fetched"] <= 3


@patch("tools.docs_crawler.fetch_page")
def test_crawl_stays_on_origin(mock_fetch):
    mock_fetch.return_value = {
        "url": "https://docs.example.com",
        "title": "Home",
        "content": "home",
        "links": [
            "https://docs.example.com/internal",
            "https://other-site.com/external",
        ],
        "error": None,
    }
    result = crawl_docs(
        ["https://docs.example.com"], max_depth=1, max_pages=10,
        stay_on_origin=True, delay_seconds=0
    )
    fetched_urls = [p["url"] for p in result["pages"]]
    assert "https://other-site.com/external" not in fetched_urls


@patch("tools.docs_crawler.fetch_page")
def test_crawl_multiple_seeds(mock_fetch):
    def side_effect(url):
        return {"url": url, "title": url, "content": f"content of {url}", "links": [], "error": None}

    mock_fetch.side_effect = side_effect
    result = crawl_docs(
        ["https://site-a.com", "https://site-b.com"],
        max_depth=0, max_pages=10, delay_seconds=0
    )
    assert result["total_fetched"] == 2


# ---------------------------------------------------------------------------
# summarise_crawl
# ---------------------------------------------------------------------------

def test_summarise_crawl_formats_output():
    crawl_result = {
        "pages": [
            {"url": "https://example.com", "title": "Home", "content": "Welcome!", "depth": 0},
            {"url": "https://example.com/guide", "title": "Guide", "content": "How to use.", "depth": 1},
        ],
        "skipped": ["https://example.com/big.pdf"],
        "total_fetched": 2,
    }
    output = summarise_crawl(crawl_result)
    assert "Home" in output
    assert "Guide" in output
    assert "Welcome!" in output
    assert "Crawled 2 pages" in output
    assert "Skipped 1 pages" in output


def test_summarise_crawl_empty():
    result = summarise_crawl({"pages": [], "skipped": [], "total_fetched": 0})
    assert "No pages" in result
