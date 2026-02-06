from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .classifier import is_china_related
from .config import settings
from .extractor import extract_article_text
from .models import IngestionFailure, NewsArticle, SourceHealth
from .realtime import ws_manager
from .sources import SourceConfig, SourceFetchResult, fetch_all_feeds_with_health, fetch_feed_with_retry
from .tagger import extract_country_topic_tags, supported_countries, supported_topics
from .translator import translate_en_to_zh
from .utils import blob_to_tags, normalize_slug, strip_tracking_params, tags_to_blob


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _next_retry_time(retry_count: int) -> datetime:
    delay = settings.retry_initial_delay_seconds * (2**max(0, retry_count - 1))
    bounded = min(delay, 60 * 60)
    return _utcnow() + timedelta(seconds=bounded)


async def _enqueue_failure(
    db: AsyncSession,
    *,
    stage: str,
    source_name: str,
    target_url: str,
    payload: dict,
    error: str,
) -> None:
    exists_stmt = select(IngestionFailure.id).where(
        IngestionFailure.resolved.is_(False),
        IngestionFailure.stage == stage,
        IngestionFailure.target_url == target_url,
    )
    if await db.scalar(exists_stmt):
        return

    db.add(
        IngestionFailure(
            stage=stage,
            source_name=source_name,
            target_url=target_url,
            payload_json=json.dumps(payload, ensure_ascii=True),
            retry_count=0,
            max_retries=settings.retry_max_attempts,
            next_retry_at=_utcnow() + timedelta(seconds=settings.retry_initial_delay_seconds),
            last_error=error[:1000],
        )
    )


async def _update_source_health(db: AsyncSession, result: SourceFetchResult) -> None:
    current = await db.scalar(select(SourceHealth).where(SourceHealth.source_name == result.source.name))
    if current is None:
        current = SourceHealth(source_name=result.source.name, feed_url=result.source.feed_url)
        db.add(current)

    current.feed_url = result.source.feed_url
    current.last_checked_at = _utcnow()
    current.last_latency_ms = result.latency_ms
    current.last_items_count = len(result.items)

    if result.success:
        current.last_status = 'up'
        current.consecutive_failures = 0
        current.last_error = None
        current.last_success_at = _utcnow()
    else:
        current.consecutive_failures += 1
        current.last_error = (result.error or 'unknown source error')[:1000]
        current.last_status = 'down' if current.consecutive_failures >= 3 else 'degraded'


async def _ingest_one_item(db: AsyncSession, item: dict) -> int:
    normalized_url = strip_tracking_params(item['article_url'])
    exists_stmt = select(NewsArticle.id).where(
        or_(
            NewsArticle.article_url == normalized_url,
            (NewsArticle.title == item['title'])
            & (NewsArticle.source_name == item['source_name'])
            & (NewsArticle.published_at == item['published_at']),
        )
    )
    if await db.scalar(exists_stmt):
        return 0

    content_en = await extract_article_text(normalized_url)
    extraction_failed = False
    if not content_en:
        extraction_failed = True
        content_en = item['summary'] or ''

    content_zh = await translate_en_to_zh(content_en)
    countries, topics = extract_country_topic_tags(item['title'], item['summary'], content_en)
    china_related = 'china' in countries or is_china_related(item['title'], item['summary'], content_en)

    db.add(
        NewsArticle(
            source_name=item['source_name'],
            source_url=item['source_url'],
            article_url=normalized_url,
            title=item['title'],
            summary=item['summary'] or '',
            content_en=content_en,
            content_zh=content_zh,
            language_detected='en',
            published_at=item['published_at'],
            china_related=china_related,
            image_url=item.get('image_url'),
            country_tags_blob=tags_to_blob(countries),
            topic_tags_blob=tags_to_blob(topics),
        )
    )

    if extraction_failed:
        await _enqueue_failure(
            db,
            stage='article_extract',
            source_name=item['source_name'],
            target_url=normalized_url,
            payload={'title': item['title']},
            error='initial content extraction returned empty',
        )
    return 1


async def _ingest_items(db: AsyncSession, items: list[dict]) -> int:
    inserted = 0
    for item in items:
        inserted += await _ingest_one_item(db, item)
    return inserted


async def _retry_article_extract(db: AsyncSession, failure: IngestionFailure) -> bool:
    text = await extract_article_text(failure.target_url)
    if not text:
        return False

    article = await db.scalar(select(NewsArticle).where(NewsArticle.article_url == failure.target_url))
    if article is None:
        return True

    if len(text) <= len(article.content_en or ''):
        return True

    article.content_en = text
    article.content_zh = await translate_en_to_zh(text)
    countries, topics = extract_country_topic_tags(article.title, article.summary, text)
    article.country_tags_blob = tags_to_blob(countries)
    article.topic_tags_blob = tags_to_blob(topics)
    article.china_related = 'china' in countries or is_china_related(article.title, article.summary, text)
    return True


async def process_retry_queue(db: AsyncSession) -> tuple[int, int]:
    now = _utcnow()
    stmt = (
        select(IngestionFailure)
        .where(IngestionFailure.resolved.is_(False), IngestionFailure.next_retry_at <= now)
        .order_by(IngestionFailure.next_retry_at.asc())
        .limit(settings.retry_queue_batch_size)
    )
    jobs = (await db.scalars(stmt)).all()
    if not jobs:
        return 0, 0

    inserted = 0
    processed = 0
    for job in jobs:
        processed += 1
        ok = False
        latest_error = 'unknown retry error'

        try:
            if job.stage == 'feed_fetch':
                result = await fetch_feed_with_retry(
                    SourceConfig(name=job.source_name, feed_url=job.target_url),
                    max_attempts=1,
                    backoff_seconds=0,
                )
                await _update_source_health(db, result)
                if result.success:
                    inserted += await _ingest_items(db, result.items)
                    ok = True
                else:
                    latest_error = result.error or latest_error
            elif job.stage == 'article_extract':
                ok = await _retry_article_extract(db, job)
                if not ok:
                    latest_error = 'article extraction retry failed'
            else:
                ok = True
        except Exception as exc:
            latest_error = str(exc)
            ok = False

        if ok:
            job.resolved = True
            job.last_error = None
            continue

        job.retry_count += 1
        job.last_error = latest_error[:1000]
        if job.retry_count >= job.max_retries:
            job.resolved = True
        else:
            job.next_retry_at = _next_retry_time(job.retry_count)

    return inserted, processed


async def ingest_news_batch(db: AsyncSession) -> int:
    inserted_total = 0

    retry_inserted, _ = await process_retry_queue(db)
    inserted_total += retry_inserted

    source_results = await fetch_all_feeds_with_health()
    for result in source_results:
        await _update_source_health(db, result)
        if result.success:
            inserted_total += await _ingest_items(db, result.items)
            continue

        await _enqueue_failure(
            db,
            stage='feed_fetch',
            source_name=result.source.name,
            target_url=result.source.feed_url,
            payload={'feed_url': result.source.feed_url},
            error=result.error or 'source fetch failed',
        )

    await db.commit()
    if inserted_total:
        await ws_manager.broadcast_json({'type': 'news_inserted', 'count': inserted_total})

    return inserted_total


def _choose_content(article: NewsArticle, lang: str) -> str:
    if lang == 'zh' and article.content_zh:
        return article.content_zh
    return article.content_en


def _to_news_payload(row: NewsArticle, lang: str) -> dict:
    return {
        'id': row.id,
        'source_name': row.source_name,
        'source_url': row.source_url,
        'article_url': row.article_url,
        'title': row.title,
        'summary': row.summary,
        'content': _choose_content(row, lang),
        'language': lang,
        'published_at': row.published_at,
        'fetched_at': row.fetched_at,
        'china_related': row.china_related,
        'image_url': row.image_url,
        'country_tags': blob_to_tags(row.country_tags_blob),
        'topic_tags': blob_to_tags(row.topic_tags_blob),
    }


async def query_news(
    db: AsyncSession,
    *,
    lang: str,
    china_only: bool,
    q: str | None,
    country: str | None,
    topic: str | None,
    limit: int,
    offset: int,
) -> tuple[int, list[dict]]:
    filters = []
    if china_only:
        filters.append(NewsArticle.china_related.is_(True))

    if q and q.strip():
        needle = f"%{q.strip()}%"
        filters.append(
            or_(
                NewsArticle.title.ilike(needle),
                NewsArticle.summary.ilike(needle),
                NewsArticle.content_en.ilike(needle),
                NewsArticle.content_zh.ilike(needle),
                NewsArticle.source_name.ilike(needle),
            )
        )

    if country and country.strip():
        country_slug = normalize_slug(country)
        filters.append(NewsArticle.country_tags_blob.like(f"%|{country_slug}|%"))

    if topic and topic.strip():
        topic_slug = normalize_slug(topic)
        filters.append(NewsArticle.topic_tags_blob.like(f"%|{topic_slug}|%"))

    total_stmt = select(func.count(NewsArticle.id))
    if filters:
        total_stmt = total_stmt.where(*filters)
    total = int((await db.scalar(total_stmt)) or 0)

    stmt = select(NewsArticle)
    if filters:
        stmt = stmt.where(*filters)

    stmt = stmt.order_by(NewsArticle.published_at.desc()).limit(limit).offset(offset)
    rows = (await db.scalars(stmt)).all()
    return total, [_to_news_payload(row, lang) for row in rows]


async def query_news_detail(db: AsyncSession, article_id: int, lang: str) -> dict | None:
    row = await db.get(NewsArticle, article_id)
    if row is None:
        return None
    return _to_news_payload(row, lang)


async def query_source_health(db: AsyncSession) -> list[dict]:
    rows = (await db.scalars(select(SourceHealth).order_by(SourceHealth.source_name.asc()))).all()
    return [
        {
            'source_name': row.source_name,
            'feed_url': row.feed_url,
            'last_status': row.last_status,
            'consecutive_failures': row.consecutive_failures,
            'last_error': row.last_error,
            'last_latency_ms': row.last_latency_ms,
            'last_items_count': row.last_items_count,
            'last_checked_at': row.last_checked_at,
            'last_success_at': row.last_success_at,
        }
        for row in rows
    ]


async def query_filter_options() -> dict[str, list[str]]:
    return {'countries': supported_countries(), 'topics': supported_topics()}


async def query_retry_metrics(db: AsyncSession) -> dict[str, int]:
    now = _utcnow()
    pending = int(
        (await db.scalar(select(func.count(IngestionFailure.id)).where(IngestionFailure.resolved.is_(False)))) or 0
    )
    due = int(
        (
            await db.scalar(
                select(func.count(IngestionFailure.id)).where(
                    IngestionFailure.resolved.is_(False),
                    IngestionFailure.next_retry_at <= now,
                )
            )
        )
        or 0
    )
    return {'pending': pending, 'due': due}
