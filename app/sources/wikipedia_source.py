"""
Wikipedia source — good for definitional / background / encyclopedic
queries. Kept separate from general web search so the LLM can choose it
specifically when the query calls for authoritative background context.
"""
from __future__ import annotations

import wikipedia

from app.config import settings

SOURCE_NAME = "wikipedia"


def search(query: str, max_results: int | None = None) -> list[dict]:
    max_results = max_results or settings.MAX_RESULTS_PER_SOURCE
    results = []
    try:
        titles = wikipedia.search(query, results=max_results)
    except Exception:
        titles = []

    for title in titles:
        try:
            page = wikipedia.page(title, auto_suggest=False, redirect=True)
            content = page.summary[:3000]
            results.append(
                {
                    "source": SOURCE_NAME,
                    "title": page.title,
                    "url": page.url,
                    "content": content,
                }
            )
        except Exception:
            continue
    return results
