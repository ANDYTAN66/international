from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NewsItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_name: str
    source_url: str
    article_url: str
    title: str
    summary: str
    content: str
    language: str
    published_at: datetime
    fetched_at: datetime
    china_related: bool
    image_url: str | None
    country_tags: list[str]
    topic_tags: list[str]


class NewsListResponse(BaseModel):
    total: int
    items: list[NewsItem]


class PushEvent(BaseModel):
    type: str
    count: int


class SourceHealthItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_name: str
    feed_url: str
    last_status: str
    consecutive_failures: int
    last_error: str | None
    last_latency_ms: int | None
    last_items_count: int
    last_checked_at: datetime
    last_success_at: datetime | None


class SourceHealthResponse(BaseModel):
    items: list[SourceHealthItem]


class RetryMetrics(BaseModel):
    pending: int
    due: int
