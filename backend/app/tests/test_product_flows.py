from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.models import Task
from app.services.persistence import initial_progress, run_and_store_task
from app.services.strategy_card_service import StrategyCardService


@pytest.fixture()
def api_client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api-test.db'}",
        connect_args={"check_same_thread": False},
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    class FakeExecutionService:
        def queue(self, task_id: int) -> dict:
            with testing_session() as db:
                task = db.get(Task, task_id)
                assert task is not None
                task.status = "queued"
                task.run_attempt = int(task.run_attempt or 0) + 1
                task.queued_at = datetime.now(timezone.utc)
                task.progress = initial_progress()
                db.commit()
                return {
                    "status": task.status,
                    "run_attempt": task.run_attempt,
                    "queued_at": task.queued_at,
                    "started_at": task.started_at,
                    "finished_at": task.finished_at,
                    "progress": task.progress,
                    "error_message": task.error_message,
                    "cancel_requested": task.cancel_requested,
                }

        def start(self, _task_id: int) -> None:
            return None

        def submit(self, task_id: int) -> dict:
            return self.queue(task_id)

        def cancel(self, task_id: int) -> bool:
            with testing_session() as db:
                task = db.get(Task, task_id)
                assert task is not None
                task.cancel_requested = True
                task.status = "cancelled"
                db.commit()
            return True

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr("app.api.routes_demos.task_execution_service", FakeExecutionService())
    monkeypatch.setattr("app.api.routes_tasks.task_execution_service", FakeExecutionService())
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    get_settings.cache_clear()
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    get_settings.cache_clear()
    engine.dispose()


def test_browser_upload_preview_mapping_and_task_creation(api_client: TestClient) -> None:
    content = "comment_id,comment_text,likes,url\n1,裁判这个回合值得复盘,8,https://example.com/1\n2,球队末节防守很好,15,https://example.com/2\n"
    response = api_client.post(
        "/api/uploads",
        files={"file": ("comments.csv", content.encode("utf-8"), "text/csv")},
        data={"source_kind": "csv"},
    )

    assert response.status_code == 201
    uploaded = response.json()
    assert uploaded["row_count"] == 2
    assert uploaded["status"] == "ready"
    assert uploaded["field_mapping"]["content"] == "comment_text"
    assert uploaded["preview_rows"][0]["comment_text"] == "裁判这个回合值得复盘"

    mapping_response = api_client.patch(
        f"/api/uploads/{uploaded['id']}/mapping",
        json={"field_mapping": {"id": "comment_id", "content": "comment_text", "like_count": "likes", "source_url": "url"}},
    )
    assert mapping_response.status_code == 200
    assert mapping_response.json()["status"] == "ready"

    task_response = api_client.post(
        "/api/tasks",
        json={
            "name": "上传评论分析",
            "domain": "basketball",
            "board": "nba",
            "match_name": "测试比赛",
            "data_source": "csv",
            "upload_id": uploaded["id"],
            "llm_mode": "mock",
        },
    )
    assert task_response.status_code == 200
    task = task_response.json()
    assert task["upload_id"] == uploaded["id"]
    assert task["source_path"]
    assert task["field_mapping"]["content"] == "comment_text"


def test_one_click_demo_is_queued_with_mock_llm(api_client: TestClient) -> None:
    response = api_client.post("/api/demos/basketball")

    assert response.status_code == 202
    task = response.json()
    assert task["status"] == "queued"
    assert task["data_source"] == "mock"
    assert task["llm_mode"] == "mock"
    assert task["run_attempt"] == 1
    assert set(task["progress"]) >= {"understand", "crawl", "insight", "visualize"}


def test_workflow_exception_persists_failed_status(tmp_path, monkeypatch) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'failure.db'}")
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    class BrokenGraph:
        def __init__(self, **_kwargs):
            pass

        def run(self, _task):
            raise RuntimeError("connector exploded")

    monkeypatch.setattr("app.services.persistence.CommentAnalysisGraph", BrokenGraph)
    with session_factory() as db:
        task = Task(
            name="failure case",
            domain="basketball",
            platforms=["hupu"],
            board="nba",
            data_source="mock",
            progress={},
        )
        db.add(task)
        db.commit()
        task_id = task.id
        with pytest.raises(RuntimeError, match="connector exploded"):
            run_and_store_task(db, task)

    with session_factory() as db:
        failed = db.get(Task, task_id)
        assert failed is not None
        assert failed.status == "failed"
        assert failed.error_message == "connector exploded"
        assert failed.finished_at is not None
    engine.dispose()


def test_strategy_cards_use_real_counts_and_evidence() -> None:
    comments = []
    for index in range(120):
        item = {
            "id": f"c-{index}",
            "content": f"评论 {index}",
            "cleaned_content": f"评论 {index}",
            "like_count": index,
            "is_duplicate": False,
        }
        if index < 18:
            item["painpoint"] = {"category": "判罚尺度争议"}
        comments.append(item)

    cards = StrategyCardService().build({"comments": comments, "clusters": []})

    assert len(cards) == 1
    card = cards[0]
    assert card["evidence_count"] == 18
    assert card["sample_size"] == 120
    assert card["affected_ratio"] == 0.15
    assert card["confidence"] == "high"
    assert len(card["evidence_comments"]) == 3
    assert {item["comment_id"] for item in card["evidence_comments"]} <= {item["id"] for item in comments}
