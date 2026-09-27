from __future__ import annotations

import os
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.config import settings


def _build_markdown(query: str, summary: dict) -> str:
    lines = [f"# Research Summary: {query}\n"]

    lines.append("## Key Points\n")
    for point in summary.get("key_points", []):
        lines.append(f"- {point}")
    lines.append("")

    lines.append("## Important Findings\n")
    for finding in summary.get("important_findings", []):
        lines.append(f"- {finding}")
    lines.append("")

    lines.append("## Actionable Insights\n")
    for insight in summary.get("actionable_insights", []):
        lines.append(f"- {insight}")
    lines.append("")

    lines.append("## References\n")
    for ref in summary.get("references", []):
        title = ref.get("title", "Untitled")
        url = ref.get("url", "")
        source = ref.get("source", "")
        lines.append(f"- [{title}]({url}) — *{source}*")

    return "\n".join(lines)


def export_markdown(query: str, summary: dict) -> str:
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    filename = f"research_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    path = os.path.join(settings.OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_build_markdown(query, summary))
    return path


def export_pdf(query: str, summary: dict) -> str:
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
    filename = f"research_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join(settings.OUTPUT_DIR, filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    def write_line(text: str, size: int, bold: bool = False, indent: bool = False):
        pdf.set_font("Helvetica", "B" if bold else "", size)
        pdf.set_x(pdf.l_margin + (5 if indent else 0))
        safe_text = text.encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(
            0, 6, safe_text, new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )

    write_line(f"Research Summary: {query}", 16, bold=True)
    pdf.ln(2)

    def section(title: str, items: list[str]):
        write_line(title, 13, bold=True)
        for item in items:
            write_line(f"- {item}", 11, indent=True)
        pdf.ln(3)

    section("Key Points", summary.get("key_points", []))
    section("Important Findings", summary.get("important_findings", []))
    section("Actionable Insights", summary.get("actionable_insights", []))

    write_line("References", 13, bold=True)
    for ref in summary.get("references", []):
        line = f"{ref.get('title', 'Untitled')} ({ref.get('source', '')}) - {ref.get('url', '')}"
        write_line(line, 10, indent=True)

    pdf.output(path)
    return path
