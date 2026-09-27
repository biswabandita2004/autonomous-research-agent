"""
Quick CLI demo — run a research query from the terminal without starting
the FastAPI server.

Usage:
    python run_demo.py "latest developments in retrieval augmented generation"
    python run_demo.py "transformer attention mechanism" --export markdown
"""
import argparse
import json

from app.agent.research_agent import ResearchAgent
from app.agent.memory import save_search
from app.agent.export import export_markdown, export_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="The topic or question to research")
    parser.add_argument("--export", choices=["markdown", "pdf"], default=None)
    args = parser.parse_args()

    agent = ResearchAgent()
    result = agent.research(args.query)
    summary = result["summary"]

    print(json.dumps(result, indent=2, default=str))

    if args.export == "markdown":
        path = export_markdown(args.query, summary)
        print(f"\nMarkdown summary exported to: {path}")
    elif args.export == "pdf":
        path = export_pdf(args.query, summary)
        print(f"\nPDF summary exported to: {path}")

    save_search(args.query, summary, result["sources_queried"])


if __name__ == "__main__":
    main()
