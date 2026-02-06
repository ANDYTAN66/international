from __future__ import annotations

import asyncio

import aiohttp
import trafilatura

from .config import settings


async def fetch_article_html(url: str) -> str | None:
    timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
    headers = {'User-Agent': settings.user_agent}

    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url, allow_redirects=True) as response:
                response.raise_for_status()
                return await response.text()
    except Exception:
        return None


def extract_text_from_html(html: str) -> str | None:
    try:
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False,
            no_fallback=False,
            favor_recall=True,
        )
        if text:
            return text.strip()
        return None
    except Exception:
        return None


async def extract_article_text(url: str) -> str:
    html = await fetch_article_html(url)
    if not html:
        return ''

    # HTML parsing can be CPU-heavy; keep it off the event loop.
    text = await asyncio.to_thread(extract_text_from_html, html)
    if not text:
        return ''

    return text[:30000]
