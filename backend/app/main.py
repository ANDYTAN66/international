from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import SessionLocal, get_db, init_db, wait_for_db_ready
from .news_service import (
    ingest_news_batch,
    query_filter_options,
    query_news,
    query_news_detail,
    query_retry_metrics,
    query_source_health,
)
from .realtime import ws_manager
from .schemas import NewsItem, NewsListResponse, RetryMetrics, SourceHealthItem, SourceHealthResponse

scheduler = AsyncIOScheduler()
logger = logging.getLogger(__name__)


async def scheduled_ingest() -> None:
    try:
        async with SessionLocal() as db:
            await ingest_news_batch(db)
    except Exception:
        logger.exception('scheduled ingest failed')


@asynccontextmanager
async def lifespan(_: FastAPI):
    await wait_for_db_ready()
    await init_db()
    scheduler.add_job(scheduled_ingest, 'interval', seconds=settings.poll_seconds, max_instances=1, coalesce=True)
    scheduler.start()

    # Prime first fetch in background so API becomes available immediately.
    kickoff_task = asyncio.create_task(scheduled_ingest())

    try:
        yield
    finally:
        kickoff_task.cancel()
        scheduler.shutdown()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/')
async def root() -> dict:
    return {'status': 'ok', 'service': settings.app_name}


@app.get('/health')
async def health() -> dict:
    return {'status': 'ok'}


@app.get(f'{settings.api_prefix}/news', response_model=NewsListResponse)
async def list_news(
    lang: str = Query(default='en', pattern='^(en|zh)$'),
    china_only: bool = Query(default=False),
    q: str | None = Query(default=None),
    country: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> NewsListResponse:
    total, items = await query_news(
        db,
        lang=lang,
        china_only=china_only,
        q=q,
        country=country,
        topic=topic,
        limit=limit,
        offset=offset,
    )
    return NewsListResponse(total=total, items=[NewsItem(**item) for item in items])


@app.get(f'{settings.api_prefix}/news/{{article_id}}', response_model=NewsItem)
async def get_news_detail(
    article_id: int,
    lang: str = Query(default='en', pattern='^(en|zh)$'),
    db: AsyncSession = Depends(get_db),
) -> NewsItem:
    item = await query_news_detail(db, article_id=article_id, lang=lang)
    if not item:
        raise HTTPException(status_code=404, detail='News not found')
    return NewsItem(**item)


@app.get(f'{settings.api_prefix}/sources/health', response_model=SourceHealthResponse)
async def get_sources_health(db: AsyncSession = Depends(get_db)) -> SourceHealthResponse:
    items = await query_source_health(db)
    return SourceHealthResponse(items=[SourceHealthItem(**item) for item in items])


@app.get(f'{settings.api_prefix}/filters')
async def get_filters() -> dict[str, list[str]]:
    return await query_filter_options()


@app.get(f'{settings.api_prefix}/retry/metrics', response_model=RetryMetrics)
async def get_retry_queue_metrics(db: AsyncSession = Depends(get_db)) -> RetryMetrics:
    metrics = await query_retry_metrics(db)
    return RetryMetrics(**metrics)


@app.websocket('/ws/news')
async def news_ws(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
