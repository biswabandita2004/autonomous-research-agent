"""
The agent's brain. Two LLM calls per research request:

  1. SOURCE SELECTION — given the query, the LLM decides which of the
     available external sources are worth querying (e.g. a "latest news"
     query shouldn't bother with arXiv; a "transformer architecture"
     query should hit arXiv and web search but skip nothing needlessly).
     This is genuine autonomous source selection, not a keyword switch.

  2. SUMMARIZATION — given deduplicated content pulled from the chosen
     sources, the LLM produces a structured summary (key points,
     findings, references, actionable insights) as JSON.

Between the two, sources are queried **in parallel** (ThreadPoolExecutor)
and results are deduplicated before being handed back to the LLM.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from groq import Groq

from app.config import settings
from app.sources import web_search, wikipedia_source, arxiv_source
from app.agent.dedup import deduplicate
from app.agent.memory import find_similar_past_searches

AVAILABLE_SOURCES = {
    "web_search": web_search.search,
    "wikipedia": wikipedia_source.search,
    "arxiv": arxiv_source.search,
}

SOURCE_SELECTION_PROMPT = """You are a research planning assistant. Given a
user's research query, decide which of the following external knowledge
sources are worth querying:

- "web_search": general web search — best for current events, products,
  opinions, how-tos, and anything not purely academic.
- "wikipedia": best for definitions, background context, historical or
  encyclopedic topics.
- "arxiv": best for academic/scientific/technical research topics
  (algorithms, papers, ML techniques, physics, etc.). Skip this for
  non-technical queries.

Respond with ONLY a JSON array of source names to query, e.g.
["web_search", "wikipedia"]. Select at least one and at most all three —
choose based on genuine relevance to the query, not by default."""

SUMMARY_PROMPT_TEMPLATE = """You are a research analyst. Based ONLY on the
content provided below (retrieved from external sources for the query
"{query}"), produce a structured research summary.

Content from sources:
{content_block}

Notes on similar past searches (may be empty):
{memory_block}

Respond with ONLY a JSON object in this exact shape:
{{
  "key_points": ["...", "..."],
  "important_findings": ["...", "..."],
  "actionable_insights": ["...", "..."],
  "references": [{{"title": "...", "url": "...", "source": "..."}}]
}}

Rules:
- Do not invent facts not present in the provided content.
- "references" should list the actual sources used (title, url, source type).
- Keep each bullet concise (one sentence).
- If no actionable insights genuinely apply, return an empty list for that field.
"""


def _extract_json(text: str) -> Any:
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


class ResearchAgent:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    # ---------------------------------------------------------------
    def _select_sources(self, query: str) -> list[str]:
        response = self.client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": SOURCE_SELECTION_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.0,
        )
        raw = response.choices[0].message.content or "[]"
        try:
            selected = _extract_json(raw)
            selected = [s for s in selected if s in AVAILABLE_SOURCES]
        except Exception:
            selected = []
        if not selected:
            selected = ["web_search"]  # safe fallback so a parse failure never blocks the pipeline
        return selected

    def _gather_parallel(self, query: str, sources: list[str]) -> list[dict]:
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=len(sources) or 1) as executor:
            future_to_source = {
                executor.submit(AVAILABLE_SOURCES[src], query): src for src in sources
            }
            for future in as_completed(future_to_source):
                try:
                    results.extend(future.result())
                except Exception:
                    continue
        return results

    def _summarize(self, query: str, deduped: list[dict], memories: list[dict]) -> dict:
        content_block = "\n\n".join(
            f"[{item['source']}] {item['title']}\nURL: {item['url']}\n{item['content'][:1500]}"
            for item in deduped
        ) or "No content retrieved from any source."

        memory_block = "\n".join(
            f"- Previously searched: \"{m['query']}\" (used sources: {', '.join(m.get('sources_used', []))})"
            for m in memories
        ) or "None."

        prompt = SUMMARY_PROMPT_TEMPLATE.format(query=query, content_block=content_block, memory_block=memory_block)

        response = self.client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        raw = response.choices[0].message.content or "{}"
        try:
            summary = _extract_json(raw)
        except Exception:
            summary = {
                "key_points": [],
                "important_findings": [],
                "actionable_insights": [],
                "references": [],
            }
        # Ensure all expected keys exist even if the LLM omits one
        for key in ("key_points", "important_findings", "actionable_insights", "references"):
            summary.setdefault(key, [])
        return summary

    # ---------------------------------------------------------------
    def research(self, query: str) -> dict:
        selected_sources = self._select_sources(query)
        raw_results = self._gather_parallel(query, selected_sources)
        deduped = deduplicate(raw_results)
        memories = find_similar_past_searches(query)
        summary = self._summarize(query, deduped, memories)

        return {
            "query": query,
            "sources_selected": selected_sources,
            "sources_queried": sorted({r["source"] for r in raw_results}),
            "raw_results_count": len(raw_results),
            "deduplicated_results_count": len(deduped),
            "summary": summary,
        }
