from __future__ import annotations

import copy
import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone

from app.config import get_settings
from app.database import SessionLocal
from app.models import Task
from app.services.exceptions import TaskCancelledError
from app.services.persistence import initial_progress, run_and_store_task

logger = logging.getLogger(__name__)


class TaskExecutionService:
    """Small in-process queue with persistent task state for local/open-source use."""

    def __init__(self, max_workers: int | None = None) -> None:
        workers = max_workers or max(1, get_settings().task_worker_count)
        self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="comment-insight")
        self._futures: dict[int, Future] = {}
        self._cancel_events: dict[int, threading.Event] = {}
        self._lock = threading.RLock()

    def queue(self, task_id: int) -> dict:
        with self._lock:
            existing = self._futures.get(task_id)
            if (existing and not existing.done()) or task_id in self._cancel_events:
                raise ValueError("任务已经在队列中")
            with SessionLocal() as db:
                task = db.get(Task, task_id)
                if not task:
                    raise LookupError("任务不存在")
                if task.status in {"queued", "running"}:
                    raise ValueError("任务正在运行")
                task.status = "queued"
                task.error_message = ""
                task.cancel_requested = False
                task.queued_at = datetime.now(timezone.utc)
                task.started_at = None
                task.finished_at = None
                task.run_attempt = int(task.run_attempt or 0) + 1
                task.progress = initial_progress()
                db.commit()
                state = {
                    "status": task.status,
                    "run_attempt": task.run_attempt,
                    "queued_at": task.queued_at,
                    "started_at": task.started_at,
                    "finished_at": task.finished_at,
                    "progress": copy.deepcopy(task.progress),
                    "error_message": task.error_message,
                    "cancel_requested": task.cancel_requested,
                }
            cancel_event = threading.Event()
            self._cancel_events[task_id] = cancel_event
            return state

    def start(self, task_id: int) -> None:
        """Start work after the HTTP queued response has been sent."""

        with self._lock:
            cancel_event = self._cancel_events.get(task_id)
            if not cancel_event:
                return
            if cancel_event.is_set():
                self._mark_cancelled(task_id)
                self._cleanup(task_id)
                return
            future = self.executor.submit(self._execute, task_id, cancel_event)
            self._futures[task_id] = future
            future.add_done_callback(lambda _future, current_id=task_id: self._cleanup(current_id))

    def submit(self, task_id: int) -> dict:
        """Queue and start immediately for CLI and service callers."""

        state = self.queue(task_id)
        self.start(task_id)
        return state

    def cancel(self, task_id: int) -> bool:
        with SessionLocal() as db:
            task = db.get(Task, task_id)
            if not task:
                raise LookupError("任务不存在")
            if task.status not in {"queued", "running"}:
                return False
            task.cancel_requested = True
            task.error_message = "正在取消任务，当前 Agent 结束后停止。"
            db.commit()
        with self._lock:
            event = self._cancel_events.get(task_id)
            future = self._futures.get(task_id)
            if event:
                event.set()
            cancelled_before_start = bool(future and future.cancel())
        if cancelled_before_start:
            self._mark_cancelled(task_id)
        return True

    def recover_stale_tasks(self) -> int:
        """Mark work interrupted by a process restart instead of leaving it running forever."""

        with SessionLocal() as db:
            rows = db.query(Task).filter(Task.status.in_(["queued", "running"])).all()
            for task in rows:
                task.status = "failed"
                task.error_message = "服务重启中断了任务，请点击重试。"
                task.finished_at = datetime.now(timezone.utc)
                task.cancel_requested = False
            db.commit()
            return len(rows)

    def wait(self, task_id: int, timeout: float = 30) -> None:
        with self._lock:
            future = self._futures.get(task_id)
        if future:
            future.result(timeout=timeout)

    def _execute(self, task_id: int, cancel_event: threading.Event) -> None:
        with SessionLocal() as db:
            task = db.get(Task, task_id)
            if not task:
                return
            if cancel_event.is_set() or task.cancel_requested:
                self._mark_cancelled(task_id)
                return
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            task.error_message = ""
            db.commit()

            def progress_callback(progress: dict) -> None:
                with SessionLocal() as progress_db:
                    current = progress_db.get(Task, task_id)
                    if current:
                        current.progress = copy.deepcopy(progress)
                        if current.status == "queued":
                            current.status = "running"
                        progress_db.commit()

            def cancel_check() -> bool:
                if cancel_event.is_set():
                    return True
                with SessionLocal() as check_db:
                    current = check_db.get(Task, task_id)
                    return bool(current and current.cancel_requested)

            try:
                run_and_store_task(
                    db,
                    task,
                    progress_callback=progress_callback,
                    cancel_check=cancel_check,
                )
            except TaskCancelledError:
                logger.info("Task %s cancelled", task_id)
            except Exception:
                logger.exception("Task %s failed", task_id)

    def _mark_cancelled(self, task_id: int) -> None:
        with SessionLocal() as db:
            task = db.get(Task, task_id)
            if task:
                task.status = "cancelled"
                task.error_message = "任务已由用户取消。"
                task.cancel_requested = True
                task.finished_at = datetime.now(timezone.utc)
                db.commit()

    def _cleanup(self, task_id: int) -> None:
        with self._lock:
            self._futures.pop(task_id, None)
            self._cancel_events.pop(task_id, None)


task_execution_service = TaskExecutionService()
