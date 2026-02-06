from __future__ import annotations

import re

CHINA_TERMS = [
    'china',
    'chinese',
    'beijing',
    'shanghai',
    'hong kong',
    'taiwan',
    'xi jinping',
    'prc',
]


def is_china_related(*texts: str) -> bool:
    payload = ' '.join(texts).lower()
    for term in CHINA_TERMS:
        if re.search(rf'\b{re.escape(term)}\b', payload):
            return True
    return False
