"""Rule-based person-name recognizers.

They catch names that follow a title or an introducing phrase
("Dr. Sara Ali", "الدكتور خالد الحربي", "اسمي محمد", "ابني عبد الله").
They work without any ML model and complement the NER models.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from cloakix.normalize import fold
from cloakix.recognizers.base import AnalysisInput, Detection, Recognizer

_AR_LETTERS = "ء-ي"
_AR_WORD = re.compile(f"[{_AR_LETTERS}]+")
_SPACES = re.compile(r"[ \t]+")

# Particles that are part of Arabic names (folded spelling): bin, bint, abu, umm, abd, al.
AR_NAME_CONNECTORS = frozenset(["بن", "بنت", "ابن", "ابو", "ابا", "ام", "عبد", "ال"])


def _arabic_title_variants(title: str) -> set[str]:
    """Add attached prefixes: و/ف/ب/ك + title, and ل + title (الدكتور -> للدكتور)."""
    variants = {title}
    for prefix in ("و", "ف", "ب", "ك"):
        variants.add(prefix + title)
    if title.startswith("ال"):
        for prefix in ("لل", "ولل", "فلل"):
            variants.add(prefix + title[2:])
    else:
        variants.add("ل" + title)
    return variants


class ArabicTitleNameRecognizer(Recognizer):
    name = "person_title_ar"

    def __init__(
        self,
        titles: Iterable[str],
        strong_titles: Iterable[str],
        stopwords: Iterable[str],
        skip_words: Iterable[str] = (),
        score: float = 0.65,
        strong_score: float = 0.8,
        max_words: int = 4,
    ) -> None:
        titles, strong_titles = list(titles), list(strong_titles)
        self.stopwords = frozenset(fold(w) for w in stopwords)
        self.skip_words = frozenset(fold(w) for w in skip_words)
        # A following title starts a new name: "الدكتور خالد والدكتورة نورة".
        self.title_words: frozenset[str] = frozenset(
            v for t in [*titles, *strong_titles] for v in _arabic_title_variants(fold(t))
        )
        self.score = score
        self.strong_score = strong_score
        self.max_words = max_words
        self._title_re = self._compile(titles)
        self._strong_re = self._compile(strong_titles)

    @staticmethod
    def _compile(titles: Iterable[str]) -> re.Pattern[str] | None:
        variants: set[str] = set()
        for t in titles:
            variants |= _arabic_title_variants(fold(t))
        if not variants:
            return None
        alts = "|".join(
            re.escape(v).replace(r"\ ", r"\s+") for v in sorted(variants, key=len, reverse=True)
        )
        return re.compile(rf"(?<![{_AR_LETTERS}])(?:{alts})(?![{_AR_LETTERS}])[ \t]*[./:]?")

    def _name_after(self, text: str, pos: int) -> tuple[int, int] | None:
        words: list[tuple[int, int, str]] = []
        skipped = 0
        prev_connector = False
        while len(words) < self.max_words:
            sp = _SPACES.match(text, pos)
            if sp:
                pos = sp.end()
            wm = _AR_WORD.match(text, pos)
            if not wm:
                break
            word = wm.group()
            if not words and word in self.skip_words and skipped < 2:
                skipped += 1  # e.g. "الدكتور الاستشاري خالد": skip the job title
                pos = wm.end()
                continue
            if word in self.title_words:
                break
            if not prev_connector and (word in self.stopwords or len(word) < 2):
                break
            words.append((wm.start(), wm.end(), word))
            prev_connector = word in AR_NAME_CONNECTORS
            pos = wm.end()
        while words and words[-1][2] in AR_NAME_CONNECTORS:
            words.pop()
        if not words:
            return None
        return words[0][0], words[-1][1]

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        out = []
        for regex, score in ((self._title_re, self.score), (self._strong_re, self.strong_score)):
            if regex is None:
                continue
            for m in regex.finditer(data.folded):
                span = self._name_after(data.folded, m.end())
                if span:
                    out.append(Detection("PERSON", span[0], span[1], score, self.name))
        return out


_EN_NAME_WORD = r"[A-Z][a-zA-Z'\-]+"
_EN_CONNECTOR = r"(?:bin|bint|ibn|al|el|abu|abd|abdul|van|von|de|da)"


class EnglishTitleNameRecognizer(Recognizer):
    name = "person_title_en"

    def __init__(
        self,
        titles: Iterable[str],
        strong_titles: Iterable[str],
        score: float = 0.65,
        strong_score: float = 0.8,
    ) -> None:
        name = rf"{_EN_NAME_WORD}(?:[ \t]+(?:{_EN_CONNECTOR}[ \t\-]+)?{_EN_NAME_WORD}){{0,3}}"
        self._patterns = []
        for group, sc in ((titles, score), (strong_titles, strong_score)):
            alts = "|".join(
                re.escape(t).replace(r"\ ", r"\s+") for t in sorted(group, key=len, reverse=True)
            )
            if alts:
                regex = re.compile(rf"(?<![A-Za-z])(?i:{alts})\.?:?[ \t]+(?P<name>{name})")
                self._patterns.append((regex, sc))

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        out = []
        for regex, score in self._patterns:
            for m in regex.finditer(data.text):
                out.append(Detection("PERSON", m.start("name"), m.end("name"), score, self.name))
        return out
