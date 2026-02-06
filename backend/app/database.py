from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
