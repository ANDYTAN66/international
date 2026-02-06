from __future__ import annotations

import asyncio

from deep_translator import GoogleTranslator

from .config import settings


def _chunk_text(text: str, size: int = 1800) -> list[str]:
    chunks: list[str] = []
    current = ''
    for para in text.split('\n'):
        para = para.strip()
        if not para:
            continue
        candidate = f'{current}\n{para}'.strip() if current else para
        if len(candidate) <= size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = para[:size]
    if current:
        chunks.append(current)
    return chunks


async def translate_en_to_zh(text: str) -> str | None:
    if not settings.enable_translation:
        return None

    text = text.strip()
    if not text:
        return None

    def _translate() -> str | None:
        try:
            translator = GoogleTranslator(
                source=settings.translation_source_lang,
                target=settings.translation_target_lang,
            )
            parts = _chunk_text(text[:24000])
            if not parts:
                return None
            translated = [translator.translate(part) for part in parts]
            return '\n\n'.join(segment for segment in translated if segment)
        except Exception:
            return None

    return await asyncio.to_thread(_translate)
