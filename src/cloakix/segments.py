"""Split mixed Arabic/English text into same-script runs."""

from __future__ import annotations

import re

_ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")
_LATIN = re.compile(r"[A-Za-z]")
_WORD = re.compile(r"\S+")

# Longer "words" (URLs, long IDs, hostile input such as "a/a/a/…") never contain a name, and
# feeding them to the NER models costs seconds. They are left out of the segments, so only
# the rules see them.
MAX_WORD_LENGTH = 64


def script_segments(text: str) -> tuple[tuple[int, int, str], ...]:
    """Return ``(start, end, language)`` runs where language is ``"ar"`` or ``"en"``.

    Words without letters (numbers, punctuation) join the surrounding run. Words longer than
    ``MAX_WORD_LENGTH`` end the current run and are not part of any run.
    """
    segments: list[tuple[int, int, str]] = []
    broken = False
    for m in _WORD.finditer(text):
        word = m.group()
        if len(word) > MAX_WORD_LENGTH:
            broken = True
            continue
        if _ARABIC.search(word):
            lang = "ar"
        elif _LATIN.search(word):
            lang = "en"
        else:
            continue
        if segments and segments[-1][2] == lang and not broken:
            segments[-1] = (segments[-1][0], m.end(), lang)
        else:
            segments.append((m.start(), m.end(), lang))
        broken = False
    return tuple(segments)
