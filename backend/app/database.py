from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from .config import settings
from .models import Base


def _normalize_database_url(raw_url: str) -> str:
    url = raw_url.strip()
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    if url.startswith('postgresql://'):
        url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)

    split = urlsplit(url)
    query = dict(parse_qsl(split.query, keep_blank_values=True))
    sslmode = query.pop('sslmode', None)
    if sslmode and 'ssl' not in query:
        if sslmode in {'require', 'verify-ca', 'verify-full'}:
            query['ssl'] = 'require'
        elif sslmode == 'disable':
            query['ssl'] = 'disable'

    return urlunsplit((split.scheme, split.netloc, split.path, urlencode(query), split.fragment))


engine = create_async_engine(_normalize_database_url(settings.database_url), pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def wait_for_db_ready() -> None:
    attempts = max(1, settings.startup_db_max_retries)
    delay = max(0.5, settings.startup_db_retry_seconds)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            return
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                await asyncio.sleep(delay)

    if last_error:
        raise last_error


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
