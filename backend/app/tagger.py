from __future__ import annotations

import re

COUNTRY_KEYWORDS: dict[str, tuple[str, ...]] = {
    'china': ('china', 'chinese', 'beijing', 'shanghai', 'hong kong'),
    'taiwan': ('taiwan', 'taipei'),
    'united-states': ('united states', 'u.s.', 'us ', 'washington', 'white house', 'american'),
    'russia': ('russia', 'russian', 'moscow', 'kremlin'),
    'ukraine': ('ukraine', 'kyiv', 'kiev'),
    'united-kingdom': ('united kingdom', 'uk ', 'britain', 'british', 'london'),
    'india': ('india', 'indian', 'new delhi'),
    'japan': ('japan', 'japanese', 'tokyo'),
    'south-korea': ('south korea', 'seoul'),
    'north-korea': ('north korea', 'pyongyang'),
    'iran': ('iran', 'iranian', 'tehran'),
    'israel': ('israel', 'israeli', 'jerusalem'),
    'germany': ('germany', 'german', 'berlin'),
    'france': ('france', 'french', 'paris'),
    'canada': ('canada', 'canadian', 'ottawa'),
    'australia': ('australia', 'australian', 'canberra'),
}

TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    'politics': ('election', 'parliament', 'president', 'minister', 'policy', 'government', 'diplomatic'),
    'economy': ('economy', 'inflation', 'gdp', 'interest rate', 'central bank', 'federal reserve'),
    'business': ('market', 'stocks', 'earnings', 'company', 'merger', 'trade'),
    'technology': ('ai', 'artificial intelligence', 'chip', 'software', 'cyber', 'tech'),
    'science': ('research', 'scientists', 'study', 'space', 'nasa'),
    'health': ('health', 'hospital', 'disease', 'virus', 'vaccine', 'outbreak'),
    'climate': ('climate', 'emissions', 'carbon', 'wildfire', 'flood', 'weather'),
    'energy': ('oil', 'gas', 'energy', 'opec', 'electricity'),
    'war-security': ('war', 'military', 'attack', 'missile', 'defense', 'security', 'conflict'),
    'sports': ('sports', 'olympic', 'fifa', 'nba', 'football', 'tennis'),
}


def _extract_matches(text: str, mapping: dict[str, tuple[str, ...]]) -> list[str]:
    normalized = re.sub(r'\s+', ' ', text.lower())
    hits: list[str] = []
    for tag, keywords in mapping.items():
        for kw in keywords:
            if kw in normalized:
                hits.append(tag)
                break
    return sorted(set(hits))


def extract_country_topic_tags(*texts: str) -> tuple[list[str], list[str]]:
    payload = ' '.join(part for part in texts if part).strip()
    if not payload:
        return [], []

    countries = _extract_matches(payload, COUNTRY_KEYWORDS)
    topics = _extract_matches(payload, TOPIC_KEYWORDS)
    return countries, topics


def supported_countries() -> list[str]:
    return sorted(COUNTRY_KEYWORDS.keys())


def supported_topics() -> list[str]:
    return sorted(TOPIC_KEYWORDS.keys())
