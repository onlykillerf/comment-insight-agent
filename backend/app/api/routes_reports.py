from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/tasks", tags=["reports"])


@router.get("/{task_id}/report/markdown")
def export_markdown_report(task_id: int, db: Session = Depends(get_db)) -> Response:
    """Export a Markdown analysis report."""

    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    markdown = ReportService().build_markdown(task)
    filename = f"task-{task_id}-comment-insight-report.md"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=markdown, media_type="text/markdown; charset=utf-8", headers=headers)

