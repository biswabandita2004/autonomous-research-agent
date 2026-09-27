from typing import Optional
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(..., description="The topic or question to research")
    export_format: Optional[str] = Field(
        default=None, description="'markdown', 'pdf', or None for no export"
    )


class ResearchResponse(BaseModel):
    query: str
    sources_selected: list[str]
    sources_queried: list[str]
    raw_results_count: int
    deduplicated_results_count: int
    key_points: list[str]
    important_findings: list[str]
    references: list[dict]
    actionable_insights: list[str]
    export_path: Optional[str]
    history_id: str
