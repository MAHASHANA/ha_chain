"""FastAPI application factory."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings

# Register UUID adapter for SQLite (converts uuid.UUID ↔ str transparently)
import sqlite3
import uuid as _uuid
sqlite3.register_adapter(_uuid.UUID, str)
sqlite3.register_converter("UUID", lambda b: _uuid.UUID(b.decode()))

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle hook.

    Import models here so that ``Base.metadata`` is fully populated before
    any database operation (e.g. Alembic auto-generation).
    """
    import app.models  # noqa: F401 -- side-effect import to register all tables

    # Create tables for SQLite dev mode
    from app.db.session import async_engine
    from app.db.base import Base as MainBase
    from app.database import Base as MatchingBase

    # Collect both metadata objects
    all_bases = [MainBase, MatchingBase]

    # Patch PostgreSQL-specific types for SQLite compatibility
    if "sqlite" in str(async_engine.url):
        from sqlalchemy import JSON, String
        from sqlalchemy.dialects.postgresql import UUID, JSONB

        for base in all_bases:
            for table in base.metadata.tables.values():
                for col in table.columns:
                    if isinstance(col.type, UUID):
                        col.type = String(36)
                    elif isinstance(col.type, JSONB):
                        col.type = JSON()

    async with async_engine.begin() as conn:
        for base in all_bases:
            await conn.run_sync(base.metadata.create_all)

    yield


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title=settings.APP_NAME,
        description="Blockchain-based legalized hawala remittance platform with tokenized asset investment",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.APP_DEBUG,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Register API v1 router
    # ------------------------------------------------------------------
    from app.api.v1.router import api_v1_router

    application.include_router(api_v1_router)

    # ------------------------------------------------------------------
    # Demo endpoints (faucet, matching trigger)
    # ------------------------------------------------------------------
    from app.api.v1.demo import demo_router

    application.include_router(demo_router)

    @application.get("/health", tags=["ops"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    # ------------------------------------------------------------------
    # Serve web UI static files (must be last -- catch-all)
    # ------------------------------------------------------------------
    if WEB_DIR.is_dir():
        application.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

    return application


app = create_app()
