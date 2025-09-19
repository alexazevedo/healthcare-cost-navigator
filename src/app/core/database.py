from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# Lazy initialization of database engines
_engine = None
_sync_engine = None
_AsyncSessionLocal = None


def get_engine():
    """Get or create the async database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL
            or f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:5432/{settings.POSTGRES_DB}",
            echo=settings.DEBUG,
        )
    return _engine


def get_sync_engine():
    """Get or create the sync database engine for LangChain."""
    global _sync_engine
    if _sync_engine is None:
        db_url = (
            settings.DATABASE_URL
            or f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost:5432/{settings.POSTGRES_DB}"
        )
        sync_db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        _sync_engine = create_engine(sync_db_url, pool_pre_ping=True, pool_recycle=300)
    return _sync_engine


def get_async_session_local():
    """Get or create the async session factory."""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _AsyncSessionLocal


class Base(DeclarativeBase):
    pass


# Dependency to get database session
async def get_db() -> AsyncSession:
    async with get_async_session_local()() as session:
        try:
            yield session
        finally:
            await session.close()
