from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.schemas import TaskOut
from app.services.task_execution_service import task_execution_service

router = APIRouter(prefix="/api/demos", tags=["demos"])


DEMO_SCENARIOS = {
    "basketball": {
        "name": "篮球赛后舆情一键 Demo",
        "domain": "basketball",
        "board": "nba",
        "match_name": "马刺 vs 尼克斯比赛讨论",
        "home_team": "马刺",
        "away_team": "尼克斯",
        "match_stage": "系列赛",
        "keywords": ["马刺", "尼克斯", "球员表现", "裁判", "战术"],
    },
    "football": {
        "name": "足球赛后舆情一键 Demo",
        "domain": "football",
        "board": "world-cup",
        "match_name": "世界杯焦点比赛讨论",
        "home_team": "主队",
        "away_team": "客队",
        "match_stage": "世界杯",
        "keywords": ["世界杯", "球员表现", "裁判", "战术", "换人"],
    },
}


@router.post("/{scenario}", response_model=TaskOut, status_code=202)
def run_demo(scenario: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> TaskOut:
    """Create and queue a deterministic MockLLM demo from the browser."""

    preset = DEMO_SCENARIOS.get(scenario)
    if not preset:
        raise HTTPException(status_code=404, detail="未知 Demo 场景")
    task = Task(
        **preset,
        platforms=["hupu"],
        thread_urls=[],
        news_urls=[],
        news_context="",
        semantic_query="分析虎扑网友的情绪、争议焦点、主要观点与事实依据",
        time_range={},
        max_comments=120,
        similarity_threshold=0.86,
        language="zh",
        sentiment_focus="all",
        enable_llm=True,
        llm_mode="mock",
        enable_image_analysis=False,
        max_image_comments=0,
        data_source="mock",
        field_mapping={},
        status="created",
        progress={},
        error_message="",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    state = task_execution_service.queue(task.id)
    background_tasks.add_task(task_execution_service.start, task.id)
    for field, value in state.items():
        setattr(task, field, value)
    return TaskOut.model_validate(task)
