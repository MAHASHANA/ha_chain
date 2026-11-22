"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

# Pool tuning only applies to server databases; SQLite (tests, Render demo)
# rejects pool_size/max_overflow.
_pool_kwargs = (
    {}
    if settings.DATABASE_URL.startswith("sqlite")
    else {"pool_size": 20, "max_overflow": 10, "pool_pre_ping": True, "pool_recycle": 300}
)

async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    **_pool_kwargs,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a transactional async session.

    The session is committed on successful exit and rolled back on exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
