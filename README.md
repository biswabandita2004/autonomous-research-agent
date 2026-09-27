# Autonomous Research Agent

An autonomous AI agent that takes a topic/question, **autonomously
decides which external sources to search**, gathers information from
them **in parallel**, removes duplicate/irrelevant content, and produces
a structured, actionable research summary — with export to Markdown/PDF
and memory of past searches.

## Why source selection is genuinely autonomous

`app/agent/research_agent.py` → `_select_sources()` sends the query to
the Groq LLM with a description of each available source and asks it to
choose which are relevant. There is no `if "paper" in query: use arxiv`
logic anywhere — the LLM reads the query and decides. The only hardcoded
piece is the final dispatch from a chosen source *name* to its Python
function (`AVAILABLE_SOURCES` dict), which is plumbing, not decision-making.

## Architecture

```
User Query
   │
   ▼
LLM Source Selection (Groq) ──> picks from: web_search | wikipedia | arxiv
   │
   ▼
Parallel Retrieval (ThreadPoolExecutor — all chosen sources queried at once)
   ├── web_search   → DuckDuckGo search + page text extraction
   ├── wikipedia    → Wikipedia summary API
   └── arxiv        → arXiv public API (papers/abstracts)
   │
   ▼
Deduplication  ──> drops near-duplicate content (difflib similarity) and
   │                too-short/noise results
   ▼
LLM Summarization (Groq) ──> structured JSON:
   │                          key_points, important_findings,
   │                          actionable_insights, references
   ▼
Export (optional) ──> Markdown or PDF file
   │
   ▼
Memory ──> saved to local JSON history, recalled for similar future queries
```

## Features

- **Autonomous source selection** — the LLM picks relevant sources per query.
- **Parallel information gathering** — all chosen sources are queried
  concurrently via `ThreadPoolExecutor`, not sequentially.
- **Deduplication** — near-duplicate results across sources are collapsed
  (`app/agent/dedup.py`) using text similarity, and short/empty results
  are filtered out as noise.
- **Structured summary** — key points, important findings,
  references/sources, and actionable insights, every time.
- **Export** — Markdown or PDF via `export_format` in the request.
- **Memory of past searches** — stored in a local JSON file
  (`data/search_history.json`); similar past searches are surfaced to the
  LLM as extra context on future queries, and the full history is
  browsable via `GET /history`.

## Requirements

- Python 3.10+
- A free [Groq API key](https://console.groq.com/keys)
- Internet access at runtime (to actually query web search / Wikipedia / arXiv)

No database is required — memory is a local JSON file, so setup is just
one API key.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# edit .env and set GROQ_API_KEY=your_key_here

uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger UI.

## Usage

### Option A — CLI demo

```bash
python run_demo.py "latest developments in retrieval augmented generation"
python run_demo.py "transformer self-attention mechanism" --export markdown
python run_demo.py "best budget laptops 2026" --export pdf
```

### Option B — HTTP API

```bash
curl -X POST http://127.0.0.1:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "state of quantum computing in 2026", "export_format": "markdown"}'
```

Example response shape:

```json
{
  "query": "state of quantum computing in 2026",
  "sources_selected": ["web_search", "arxiv"],
  "sources_queried": ["arxiv", "web_search"],
  "raw_results_count": 9,
  "deduplicated_results_count": 6,
  "key_points": ["..."],
  "important_findings": ["..."],
  "references": [{"title": "...", "url": "...", "source": "arxiv"}],
  "actionable_insights": ["..."],
  "export_path": "./outputs/research_20260927_...md",
  "history_id": "a1b2c3..."
}
```

### Browsing past searches

```bash
curl http://127.0.0.1:8000/history
```

## Sample queries to try (show off different source choices)

- `"budget wireless earbuds under $50"` → should select `web_search` only
- `"who was Ada Lovelace"` → should select `wikipedia` (and maybe `web_search`)
- `"attention is all you need transformer paper"` → should select `arxiv`
- `"impact of large language models on scientific research"` → should
  select multiple sources, demonstrating parallel gathering + dedup across them

## Project structure

```
research-agent-project/
├── app/
│   ├── main.py                    # FastAPI app + routes
│   ├── config.py                  # env-based settings
│   ├── models/schemas.py          # request/response models
│   ├── sources/
│   │   ├── web_search.py          # DuckDuckGo search + page extraction
│   │   ├── wikipedia_source.py    # Wikipedia summaries
│   │   └── arxiv_source.py        # arXiv abstracts
│   └── agent/
│       ├── research_agent.py      # source selection + parallel gather + summarize (core)
│       ├── dedup.py               # near-duplicate / noise removal
│       ├── export.py              # Markdown / PDF export
│       └── memory.py              # local JSON search history
├── data/                           # search_history.json lives here
├── outputs/                        # exported Markdown/PDF files land here
├── run_demo.py                     # CLI demo entrypoint
├── requirements.txt
├── .env.example
└── README.md
```

## Design notes / known limitations

- **Web search** uses DuckDuckGo via the `ddgs` package — no API key
  required, but results can vary/rate-limit under heavy use; this is a
  known trade-off of free, keyless search.
- **Page extraction** is a simple readable-text scrape (`BeautifulSoup`)
  and will not work on JS-heavy pages that render content client-side; in
  that case the agent falls back to the search snippet instead.
- **Memory** is a flat local JSON file rather than a database, since this
  is a bonus feature and the project should run with zero infrastructure
  beyond a Groq key — swapping in MongoDB/SQLite is a small, isolated
  change in `app/agent/memory.py`.
- **Deduplication** uses simple text similarity (`difflib`), not
  embeddings — fast and dependency-free, but coarser than a semantic
  dedup would be. Documented here rather than overclaimed.
