"""
Removes duplicate/near-duplicate/irrelevant results before they reach the
LLM for summarization — keeps the context window clean and avoids the
summary repeating the same fact three times because three sources said it.
"""
from __future__ import annotations

from difflib import SequenceMatcher


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def deduplicate(results: list[dict], similarity_threshold: float = 0.85) -> list[dict]:
    deduped: list[dict] = []
    seen_urls: set[str] = set()

    for item in results:
        url = item.get("url", "")
        content = (item.get("content") or "").strip()

        if not content or len(content) < 40:
            # Too short to be useful — treat as irrelevant/noise
            continue
        if url and url in seen_urls:
            continue

        is_duplicate = any(_similarity(content[:500], kept["content"][:500]) > similarity_threshold for kept in deduped)
        if is_duplicate:
            continue

        deduped.append(item)
        if url:
            seen_urls.add(url)

    return deduped
