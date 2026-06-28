from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_health import router as health_router
from app.api.routes_demos import router as demos_router
from app.api.routes_media import router as media_router
from app.api.routes_reports import router as reports_router
from app.api.routes_strategy_cards import router as strategy_cards_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_uploads import router as uploads_router
from app.config import get_settings
from app.database import init_db
from app.services.task_execution_service import task_execution_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    recovered = task_execution_service.recover_stale_tasks()
    if recovered:
        logging.getLogger(__name__).warning("Marked %s interrupted task(s) as failed", recovered)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(media_router)
app.include_router(demos_router)
app.include_router(uploads_router)
app.include_router(tasks_router)
app.include_router(reports_router)
app.include_router(strategy_cards_router)
