from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.models import Task
from app.services.persistence import run_and_store_task


PROJECT_ROOT = Path(__file__).resolve().parents[2]


SCENARIOS = {
    "nba_draft": {
        "name": "Demo: NBA Draft Opinion Analysis",
        "domain": "nba_draft",
        "platforms": ["xhs", "weibo", "bili", "zhihu"],
        "keywords": ["2026 NBA选秀", "迪班萨", "皮特森", "布泽尔", "顺位"],
        "semantic_query": "Analyze public comments about 2026 NBA draft prospects, draft order debates, player templates, and team fit.",
        "source_path": "data/demo/nba_draft_comments.csv",
    },
    "iaa_game": {
        "name": "Demo: IAA Game Review Pain Point Mining",
        "domain": "iaa_game",
        "platforms": ["weibo", "bili", "tap", "douyin"],
        "keywords": ["IAA游戏", "广告频率", "卡顿", "留存", "激励广告"],
        "semantic_query": "Analyze IAA game reviews and identify ad fatigue, retention blockers, monetization risks, and content opportunities.",
        "source_path": "data/demo/iaa_game_comments.csv",
    },
    "news_event": {
        "name": "Demo: News Event Public Opinion Analysis",
        "domain": "news",
        "platforms": ["weibo", "zhihu", "bili", "toutiao"],
        "keywords": ["新闻事件", "官方通报", "舆情风险", "观点分歧"],
        "semantic_query": "Analyze public comments around a news event, stance divergence, trust risks, and information needs.",
        "source_path": "data/demo/news_event_comments.csv",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and run a complete demo task.")
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), default="nba_draft")
    parser.add_argument("--max-comments", type=int, default=320)
    parser.add_argument("--real-llm", action="store_true", help="Use the configured real LLM provider instead of MockLLM.")
    args = parser.parse_args()

    if not args.real_llm:
        os.environ["LLM_PROVIDER"] = "mock"
        get_settings.cache_clear()

    scenario = SCENARIOS[args.scenario]
    source_path = ensure_demo_dataset(scenario["source_path"])

    init_db()
    db = SessionLocal()
    try:
        task = Task(
            name=scenario["name"],
            domain=scenario["domain"],
            platforms=scenario["platforms"],
            keywords=scenario["keywords"],
            semantic_query=scenario["semantic_query"],
            time_range={"preset": "demo"},
            max_comments=args.max_comments,
            similarity_threshold=0.9,
            language="zh",
            sentiment_focus="all",
            enable_llm=True,
            data_source="csv",
            source_path=str(source_path),
            status="created",
            progress={},
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        summary = run_and_store_task(db, task)
        print(f"Demo scenario `{args.scenario}` completed")
        print(f"Task #{task.id}")
        print(f"Summary: {summary}")
        print(f"Report: http://127.0.0.1:3000/tasks/{task.id}/report")
        print(f"Markdown: http://127.0.0.1:8000/api/tasks/{task.id}/report/markdown")
    finally:
        db.close()


def ensure_demo_dataset(relative_path: str) -> Path:
    path = PROJECT_ROOT / relative_path
    if path.exists():
        return path
    from scripts.seed_demo_data import generate_demo_data

    print("Demo dataset is missing; generating data/demo CSV files first.")
    generate_demo_data("all", 320)
    if not path.exists():
        raise FileNotFoundError(f"Demo dataset was not generated: {path}")
    return path


if __name__ == "__main__":
    main()
