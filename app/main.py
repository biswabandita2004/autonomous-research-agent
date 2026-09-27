"""
FastAPI entrypoint for the Autonomous Research Agent.

Run with:  uvicorn app.main:app --reload
Docs at:   http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.config import settings
from app.agent.research_agent import ResearchAgent
from app.agent.memory import save_search, load_history
from app.agent.export import export_markdown, export_pdf
from app.models.schemas import ResearchRequest, ResearchResponse

app = FastAPI(
    title="Autonomous Research Agent",
    description="Collects information from external sources, analyzes it, and produces a structured summary.",
    version="1.0.0",
)

agent = ResearchAgent()


@app.get("/health")
def health():
    return {"status": "ok", "model": settings.GROQ_MODEL}


@app.post("/research", response_model=ResearchResponse)
def run_research(request: ResearchRequest):
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set. Add it to your .env file.")

    result = agent.research(request.query)
    summary = result["summary"]

    export_path = None
    if request.export_format == "markdown":
        export_path = export_markdown(request.query, summary)
    elif request.export_format == "pdf":
        export_path = export_pdf(request.query, summary)

    history_id = save_search(request.query, summary, result["sources_queried"])

    return ResearchResponse(
        query=result["query"],
        sources_selected=result["sources_selected"],
        sources_queried=result["sources_queried"],
        raw_results_count=result["raw_results_count"],
        deduplicated_results_count=result["deduplicated_results_count"],
        key_points=summary["key_points"],
        important_findings=summary["important_findings"],
        references=summary["references"],
        actionable_insights=summary["actionable_insights"],
        export_path=export_path,
        history_id=history_id,
    )


@app.get("/history")
def get_history(limit: int = 20):
    history = load_history()
    return list(reversed(history))[:limit]
