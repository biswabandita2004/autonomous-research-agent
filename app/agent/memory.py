"""
Long-term memory for past searches. Deliberately a plain local JSON file
rather than a database — this bonus feature only needs to persist across
runs, and keeping it dependency-free means the project needs zero extra
infrastructure beyond the LLM key.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone

from app.config import settings


def _ensure_file() -> None:
    os.makedirs(os.path.dirname(settings.HISTORY_FILE) or ".", exist_ok=True)
    if not os.path.exists(settings.HISTORY_FILE):
        with open(settings.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load_history() -> list[dict]:
    _ensure_file()
    with open(settings.HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_search(query: str, summary: dict, sources_used: list[str]) -> str:
    _ensure_file()
    history = load_history()
    entry_id = str(uuid.uuid4())
    history.append(
        {
            "id": entry_id,
            "query": query,
            "sources_used": sources_used,
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    with open(settings.HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    return entry_id


def find_similar_past_searches(query: str, limit: int = 3) -> list[dict]:
    terms = [t.lower() for t in query.split() if len(t) > 2]
    if not terms:
        return []
    history = load_history()
    matches = [h for h in history if any(t in h["query"].lower() for t in terms)]
    matches.sort(key=lambda h: h["timestamp"], reverse=True)
    return matches[:limit]
