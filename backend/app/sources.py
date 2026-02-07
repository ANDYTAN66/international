from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from time import perf_counter

import aiohttp
import feedparser

from .config import settings


@dataclass(frozen=True)
class SourceConfig:
    name: str
    feed_url: str


@dataclass(frozen=True)
class SourceFetchResult:
    source: SourceConfig
    success: bool
    attempts: int
    latency_ms: int | None
    items: list[dict]
    error: str | None


SOURCES: list[SourceConfig] = [
    SourceConfig(name='Google News - World', feed_url='https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en'),
    SourceConfig(name='Google News - China', feed_url='https://news.google.com/rss/search?q=China&hl=en-US&gl=US&ceid=US:en'),
    SourceConfig(name='CNN World', feed_url='http://rss.cnn.com/rss/edition_world.rss'),
    SourceConfig(name='Reuters China (Search)', feed_url='https://www.reuters.com/world/china/rss'),
    SourceConfig(name='Sky News World', feed_url='https://feeds.skynews.com/feeds/rss/world.xml'),
    SourceConfig(name='France24 World', feed_url='https://www.france24.com/en/rss'),
    SourceConfig(name='NPR World', feed_url='https://www.npr.org/rss/rss.php?id=1004'),
    SourceConfig(name='CNBC International', feed_url='https://www.cnbc.com/id/100727362/device/rss/rss.html'),
    SourceConfig(name='CNBC Asia', feed_url='https://www.cnbc.com/id/19832390/device/rss/rss.html'),
    SourceConfig(name='China Daily China', feed_url='https://www.chinadaily.com.cn/rss/china_rss.xml'),
]


async def _download_text(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url, allow_redirects=True) as response:
        response.raise_for_status()
        return await response.text()


async def fetch_feed(source: SourceConfig) -> list[dict]:
    timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
    headers = {'User-Agent': settings.user_agent}

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        xml = await _download_text(session, source.feed_url)

    parsed = await asyncio.to_thread(feedparser.parse, xml)

    items: list[dict] = []
    for entry in parsed.entries[: settings.max_articles_per_source]:
        article_url = entry.get('link', '').strip()
        title = entry.get('title', '').strip()
        if not article_url or not title:
            continue

        summary = (entry.get('summary') or entry.get('description') or '').strip()
        image_url = None

        media_content = entry.get('media_content') or []
        if media_content and isinstance(media_content, list):
            image_url = media_content[0].get('url')

        pub_dt = _parse_published(entry)

        items.append(
            {
                'source_name': source.name,
                'source_url': source.feed_url,
                'article_url': article_url,
                'title': title,
                'summary': summary,
                'published_at': pub_dt,
                'image_url': image_url,
            }
        )

    return items


async def fetch_feed_with_retry(
    source: SourceConfig,
    *,
    max_attempts: int | None = None,
    backoff_seconds: float | None = None,
) -> SourceFetchResult:
    attempts_allowed = max(1, max_attempts or settings.feed_max_retries)
    backoff = settings.feed_retry_backoff_seconds if backoff_seconds is None else backoff_seconds

    last_error: str | None = None
    last_latency_ms: int | None = None
    for attempt in range(1, attempts_allowed + 1):
        started = perf_counter()
        try:
            items = await fetch_feed(source)
            last_latency_ms = int((perf_counter() - started) * 1000)
            return SourceFetchResult(
                source=source,
                success=True,
                attempts=attempt,
                latency_ms=last_latency_ms,
                items=items,
                error=None,
            )
        except Exception as exc:
            text = str(exc).strip()
            last_error = text if text else type(exc).__name__
            last_latency_ms = int((perf_counter() - started) * 1000)
            if attempt < attempts_allowed:
                await asyncio.sleep(backoff * (2 ** (attempt - 1)))

    return SourceFetchResult(
        source=source,
        success=False,
        attempts=attempts_allowed,
        latency_ms=last_latency_ms,
        items=[],
        error=last_error or 'unknown source fetch error',
    )


def _parse_published(entry: dict) -> datetime:
    raw = entry.get('published') or entry.get('updated')
    if raw:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    return datetime.now(timezone.utc)


async def fetch_all_feeds_with_health() -> list[SourceFetchResult]:
    tasks = [fetch_feed_with_retry(source) for source in SOURCES]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    parsed: list[SourceFetchResult] = []
    for idx, result in enumerate(results):
        if isinstance(result, Exception):
            src = SOURCES[idx]
            text = str(result).strip()
            message = text if text else type(result).__name__
            parsed.append(
                SourceFetchResult(
                    source=src,
                    success=False,
                    attempts=settings.feed_max_retries,
                    latency_ms=None,
                    items=[],
                    error=message,
                )
            )
            continue
        parsed.append(result)
    return parsed
