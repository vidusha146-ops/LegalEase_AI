import logging
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine if using SQLite or PostgreSQL
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine_kwargs = {
    "echo": False,
    "future": True,
}

if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

# Create Async Engine
engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Create Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a managed async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """Verifies that the database engine can execute queries successfully."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def init_db() -> None:
    """Creates database tables if they do not already exist, and migrates new columns."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Check SQLite table columns for legal_drafts
        try:
            res = await conn.execute(text("PRAGMA table_info(legal_drafts)"))
            existing_cols = [row[1] for row in res.fetchall()]
            if existing_cols:
                if "docx_path" not in existing_cols:
                    await conn.execute(text("ALTER TABLE legal_drafts ADD COLUMN docx_path VARCHAR(512)"))
                if "draft_metadata_json" not in existing_cols:
                    await conn.execute(text("ALTER TABLE legal_drafts ADD COLUMN draft_metadata_json TEXT"))
        except Exception as e:
            logger.debug(f"Table column migration notice: {e}")
    logger.info("Database tables initialized successfully.")
