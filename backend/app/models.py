from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class NewsArticle(Base):
    __tablename__ = 'news_articles'
    __table_args__ = (
        UniqueConstraint('article_url', name='uq_news_article_url'),
        Index('idx_news_published_at', 'published_at'),
        Index('idx_news_china_related', 'china_related'),
        Index('idx_news_country_tags', 'country_tags_blob'),
        Index('idx_news_topic_tags', 'topic_tags_blob'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_url: Mapped[str] = mapped_column(String(512), nullable=False)
    article_url: Mapped[str] = mapped_column(String(1024), nullable=False)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default='')
    content_en: Mapped[str] = mapped_column(Text, nullable=False, default='')
    content_zh: Mapped[str | None] = mapped_column(Text, nullable=True)

    language_detected: Mapped[str] = mapped_column(String(16), nullable=False, default='en')
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    china_related: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    country_tags_blob: Mapped[str] = mapped_column(String(1024), nullable=False, default='|')
    topic_tags_blob: Mapped[str] = mapped_column(String(1024), nullable=False, default='|')


class SourceHealth(Base):
    __tablename__ = 'source_health'
    __table_args__ = (
        UniqueConstraint('source_name', name='uq_source_health_name'),
        Index('idx_source_health_status', 'last_status'),
        Index('idx_source_health_checked', 'last_checked_at'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    feed_url: Mapped[str] = mapped_column(String(1024), nullable=False)

    last_status: Mapped[str] = mapped_column(String(16), nullable=False, default='unknown')
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_items_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class IngestionFailure(Base):
    __tablename__ = 'ingestion_failures'
    __table_args__ = (
        Index('idx_ingest_failure_due', 'resolved', 'next_retry_at'),
        Index('idx_ingest_failure_source', 'source_name'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False, default='{}')

    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    next_retry_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
