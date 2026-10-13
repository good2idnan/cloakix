"""Split mixed Arabic/English text into same-script runs."""

from __future__ import annotations

import re

_ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
_LATIN = re.compile(r"[A-Za-z]")
_WORD = re.compile(r"\S+")


def script_segments(text: str) -> tuple[tuple[int, int, str], ...]:
    """Return ``(start, end, language)`` runs where language is ``"ar"`` or ``"en"``.

    Words without letters (numbers, punctuation) join the surrounding run.
    """
    segments: list[tuple[int, int, str]] = []
    for m in _WORD.finditer(text):
        word = m.group()
        if _ARABIC.search(word):
            lang = "ar"
        elif _LATIN.search(word):
            lang = "en"
        else:
            continue
        if segments and segments[-1][2] == lang:
            segments[-1] = (segments[-1][0], m.end(), lang)
        else:
            segments.append((m.start(), m.end(), lang))
    return tuple(segments)
