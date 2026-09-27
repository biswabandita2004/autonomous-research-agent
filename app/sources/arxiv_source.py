"""
arXiv source — for research/technical/academic queries (papers, algorithms,
scientific topics). Uses arXiv's free public API, no key required.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

from app.config import settings

SOURCE_NAME = "arxiv"
API_URL = "http://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def search(query: str, max_results: int | None = None) -> list[dict]:
    max_results = max_results or settings.MAX_RESULTS_PER_SOURCE
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    }
    try:
        resp = requests.get(API_URL, params=params, timeout=settings.REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
    except Exception:
        return []

    results = []
    for entry in root.findall("atom:entry", ATOM_NS):
        title_el = entry.find("atom:title", ATOM_NS)
        summary_el = entry.find("atom:summary", ATOM_NS)
        link_el = entry.find("atom:id", ATOM_NS)
        title = title_el.text.strip() if title_el is not None else ""
        summary = summary_el.text.strip() if summary_el is not None else ""
        url = link_el.text.strip() if link_el is not None else ""
        if not summary:
            continue
        results.append(
            {
                "source": SOURCE_NAME,
                "title": title,
                "url": url,
                "content": summary[:3000],
            }
        )
    return results
