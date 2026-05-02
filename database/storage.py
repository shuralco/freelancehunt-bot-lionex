"""
Persistent dedupe storage.

Postgres у production (DATABASE_URL → Coolify supabase-db:5432) — пережиє
перезапуск контейнера, дублів більше не буде. SQLite — fallback для
локального dev без env.
"""
import os
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete

from .models import Base, SentProject
from utils.logger import logger


def _resolve_database_url() -> str:
    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        return "sqlite+aiosqlite:///./bot_data.db"
    # asyncpg не сприймає query-string з ?schema=public — обрізаємо.
    if "?" in raw:
        raw = raw.split("?", 1)[0]
    if raw.startswith("postgresql+asyncpg://"):
        return raw
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+asyncpg://", 1)
    return raw


DATABASE_URL = _resolve_database_url()

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    host = DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
    logger.info(f"Database initialized ({host})")


async def is_project_sent(project_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SentProject).where(SentProject.project_id == project_id)
        )
        return result.scalar_one_or_none() is not None


async def save_sent_project(project_id: int):
    async with AsyncSessionLocal() as session:
        new_project = SentProject(project_id=project_id)
        session.add(new_project)
        await session.commit()


async def clean_old_projects(days: int = 30):
    cutoff = datetime.utcnow() - timedelta(days=days)
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(SentProject).where(SentProject.created_at < cutoff)
        )
        await session.commit()
    logger.info(f"Cleaned projects older than {days} days")
