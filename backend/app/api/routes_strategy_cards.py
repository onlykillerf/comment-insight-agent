from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ABTestDraft, StrategyCard, Task
from app.schemas import ABTestDraftOut, StrategyCardOut

router = APIRouter(prefix="/api", tags=["strategy-cards"])


@router.get("/tasks/{task_id}/strategy-cards", response_model=list[StrategyCardOut])
def list_strategy_cards(task_id: int, db: Session = Depends(get_db)) -> list[StrategyCard]:
    if not db.get(Task, task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    return (
        db.query(StrategyCard)
        .filter(StrategyCard.task_id == task_id, StrategyCard.evidence_count >= 2)
        .order_by(StrategyCard.affected_ratio.desc())
        .all()
    )


@router.get("/strategy-cards/{card_id}/export")
def export_strategy_card(card_id: int, db: Session = Depends(get_db)) -> Response:
    card = _get_card(db, card_id)
    payload = StrategyCardOut.model_validate(card).model_dump(mode="json")
    headers = {"Content-Disposition": f'attachment; filename="strategy-card-{card.id}.json"'}
    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json; charset=utf-8",
        headers=headers,
    )


@router.post(
    "/strategy-cards/{card_id}/ab-test-drafts",
    response_model=ABTestDraftOut,
    status_code=201,
)
def create_ab_test_draft(card_id: int, db: Session = Depends(get_db)) -> ABTestDraft:
    card = _get_card(db, card_id)
    design = card.ab_test_design or {}
    draft = ABTestDraft(
        task_id=card.task_id,
        strategy_card_id=card.id,
        name=f"{card.title} - A/B 测试草案",
        hypothesis=str(design.get("hypothesis") or "验证该证据导向内容是否提升有效阅读。"),
        control=str(design.get("control") or "当前内容版本"),
        variant=str(design.get("variant") or "采用策略卡建议的内容版本"),
        primary_metric=str(design.get("primary_metric") or "完整阅读率"),
        guardrail_metrics=list(design.get("guardrail_metrics") or []),
        sample_size_note=str(design.get("sample_size_note") or "发布前补充流量与周期估算。"),
        status="draft",
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


@router.get("/tasks/{task_id}/ab-test-drafts", response_model=list[ABTestDraftOut])
def list_ab_test_drafts(task_id: int, db: Session = Depends(get_db)) -> list[ABTestDraft]:
    if not db.get(Task, task_id):
        raise HTTPException(status_code=404, detail="任务不存在")
    return (
        db.query(ABTestDraft)
        .filter(ABTestDraft.task_id == task_id)
        .order_by(ABTestDraft.created_at.desc())
        .all()
    )


def _get_card(db: Session, card_id: int) -> StrategyCard:
    card = db.get(StrategyCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="策略卡不存在")
    if card.evidence_count < 2:
        raise HTTPException(status_code=422, detail="证据不足，不能执行该策略卡")
    return card
