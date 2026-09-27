"""
General web search source. Uses DuckDuckGo (no API key required) to find
candidate pages, then fetches and extracts readable text from each so the
agent has real page content to reason over, not just search snippets.
"""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

from app.config import settings

SOURCE_NAME = "web_search"


def _extract_page_text(url: str, max_chars: int = 3000) -> str:
    try:
        resp = requests.get(
            url,
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": "Mozilla/5.0 (research-agent-bot)"},
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text[:max_chars]
    except Exception:
        return ""


def search(query: str, max_results: int | None = None) -> list[dict]:
    max_results = max_results or settings.MAX_RESULTS_PER_SOURCE
    results = []
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
    except Exception:
        hits = []

    for hit in hits:
        url = hit.get("href") or hit.get("url") or ""
        title = hit.get("title", "")
        snippet = hit.get("body", "")
        page_text = _extract_page_text(url) if url else ""
        content = page_text if len(page_text) > len(snippet) else snippet
        if not content:
            continue
        results.append(
            {
                "source": SOURCE_NAME,
                "title": title,
                "url": url,
                "content": content,
            }
        )
    return results
