from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def strip_tracking_params(url: str) -> str:
    if not url:
        return url

    split = urlsplit(url)
    return urlunsplit((split.scheme, split.netloc, split.path, '', split.fragment))


def normalize_slug(value: str) -> str:
    return value.strip().lower().replace(' ', '-')


def tags_to_blob(tags: list[str]) -> str:
    cleaned = sorted({normalize_slug(tag) for tag in tags if tag.strip()})
    if not cleaned:
        return '|'
    return '|' + '|'.join(cleaned) + '|'


def blob_to_tags(blob: str) -> list[str]:
    if not blob or blob == '|':
        return []
    return [part for part in blob.split('|') if part]
