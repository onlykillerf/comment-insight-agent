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
    "nba_game": {
        "name": "Demo: 马刺 vs 尼克斯 G6 虎扑舆情分析",
        "domain": "basketball",
        "board": "nba",
        "match_name": "马刺 vs 尼克斯 G6",
        "home_team": "马刺",
        "away_team": "尼克斯",
        "match_stage": "系列赛 G6",
        "match_date": "2026-06-20",
        "keywords": ["马刺", "尼克斯", "G6", "判罚", "战术", "关键球"],
        "semantic_query": "分析虎扑网友对马刺与尼克斯 G6 的情绪、争议焦点、球员表现和战术观点",
        "news_context": "演示背景：系列赛进入第六场，双方围绕轮换、篮板和关键球执行展开较量。该背景为合成数据，不代表真实赛果。",
        "source_path": "data/demo/nba_game_comments.csv",
    },
    "world_cup_game": {
        "name": "Demo: 世界杯淘汰赛虎扑舆情分析",
        "domain": "football",
        "board": "world_cup",
        "match_name": "阿根廷 vs 法国 世界杯 1/8 决赛",
        "home_team": "阿根廷",
        "away_team": "法国",
        "match_stage": "世界杯 1/8 决赛",
        "match_date": "2026-06-24",
        "keywords": ["世界杯", "阿根廷", "法国", "VAR", "换人", "防线"],
        "semantic_query": "分析虎扑网友对世界杯淘汰赛的情绪、判罚争议、球员发挥和战术观点",
        "news_context": "演示背景：世界杯进入淘汰赛阶段，双方阵容完整度、体能和临场调整成为赛前关注点。该背景为合成数据。",
        "source_path": "data/demo/world_cup_game_comments.csv",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create and run a focused Hupu sports demo task.")
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), default="nba_game")
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
            platforms=["hupu"],
            board=scenario["board"],
            match_name=scenario["match_name"],
            home_team=scenario["home_team"],
            away_team=scenario["away_team"],
            match_stage=scenario["match_stage"],
            match_date=scenario["match_date"],
            thread_urls=[],
            news_urls=[],
            news_context=scenario["news_context"],
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

    print("Demo dataset is missing; generating focused sports CSV files first.")
    generate_demo_data("all", 320)
    if not path.exists():
        raise FileNotFoundError(f"Demo dataset was not generated: {path}")
    return path


if __name__ == "__main__":
    main()
