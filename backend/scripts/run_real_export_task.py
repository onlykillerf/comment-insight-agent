from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal, init_db
from app.models import Task
from app.services.persistence import run_and_store_task

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a real exported-comment analysis task.")
    parser.add_argument("--source-path", required=True, help="CSV/JSON/JSONL/SQLite export path.")
    parser.add_argument("--platform", default="xhs", help="Platform alias, e.g. xhs, weibo, bili.")
    parser.add_argument("--domain", default="sports", help="Analysis domain.")
    parser.add_argument("--name", default="Real exported comment analysis", help="Task name.")
    parser.add_argument("--keywords", default="梅西,世界杯,表现", help="Comma-separated keywords.")
    parser.add_argument(
        "--semantic-query",
        default="分析用户对梅西本次世界杯表现的评论",
        help="Semantic query for the analysis task.",
    )
    parser.add_argument("--max-comments", type=int, default=300)
    parser.add_argument("--similarity-threshold", type=float, default=0.9)
    parser.add_argument("--disable-llm", action="store_true", help="Disable LLM insight generation.")
    return parser.parse_args()


def resolve_source_path(source_path: str) -> str:
    path = Path(source_path)
    if path.exists():
        return str(path)
    project_path = PROJECT_ROOT / source_path
    if project_path.exists():
        return str(project_path)
    raise FileNotFoundError(f"Export file or directory not found: {source_path}")


def main() -> None:
    args = parse_args()
    source_path = resolve_source_path(args.source_path)
    keywords = [item.strip() for item in args.keywords.replace("，", ",").split(",") if item.strip()]

    init_db()
    db = SessionLocal()
    try:
        task = Task(
            name=args.name,
            domain=args.domain,
            platforms=[args.platform],
            keywords=keywords,
            semantic_query=args.semantic_query,
            time_range={},
            max_comments=args.max_comments,
            similarity_threshold=args.similarity_threshold,
            language="zh",
            sentiment_focus="all",
            enable_llm=not args.disable_llm,
            data_source="mediacrawler",
            source_path=source_path,
            status="created",
            progress={},
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        summary = run_and_store_task(db, task)
        print(f"Task #{task.id} completed")
        print(f"Summary: {summary}")
        print(f"Report: http://127.0.0.1:3000/tasks/{task.id}/report")
        print(f"Markdown: http://127.0.0.1:8000/api/tasks/{task.id}/report/markdown")
    finally:
        db.close()


if __name__ == "__main__":
    main()

