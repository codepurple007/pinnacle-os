from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, init_engine
from app.routers import (
    audit,
    blocked,
    health,
    inbox,
    ingest,
    oauth,
    settings as settings_router,
    status,
    sync,
)
from app.services.founder import get_founder


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_engine()
    from app.db import SessionLocal, engine as db_engine

    Base.metadata.create_all(bind=db_engine)
    db = SessionLocal()
    try:
        get_founder(db)
        db.commit()
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="PinnacleOS",
        version="0.3.0",
        description="Phase 3 foundation: OAuth, ingest, audit, kill switch. No send. No calendar writes.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.web_origin,
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (
        health.router,
        status.router,
        oauth.router,
        settings_router.router,
        inbox.router,
        audit.router,
        ingest.router,
        sync.router,
        blocked.router,
    ):
        application.include_router(router, prefix="/v1")
    return application


app = create_app()
