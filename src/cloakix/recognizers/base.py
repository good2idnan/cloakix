"""Recognizer building blocks.

A recognizer looks at (normalized) text and returns candidate ``Detection``s.
Scores follow one simple, documented scheme:

* each pattern has a base score;
* a passing validator (e.g. a checksum) raises it, a failing one drops the match;
* a context word near the match (e.g. "MRN", "رقم الملف") adds ``context_boost``.

The ``Masker`` keeps detections whose final score reaches its threshold (0.5 by default).
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass

from cloakix.normalize import fold


@dataclass(frozen=True)
class Detection:
    """A span found in the normalized text."""

    type: str
    start: int
    end: int
    score: float
    recognizer: str


class ContextMatcher:
    """Finds context words (in any enabled language) near a span.

    Matching uses the folded text: lower-case, unified Arabic letter variants.
    Arabic terms match as substrings, so prefixes such as "و" / "ب" / "ال" and
    suffixes such as "ي" still match ("ورقم ملفي" contains "رقم" and "ملف").
    Latin terms must sit on word boundaries ("file" does not match "profile").
    """

    def __init__(
        self, terms: Mapping[str, Iterable[str]], window_before: int = 40, window_after: int = 25
    ) -> None:
        self.window_before = window_before
        self.window_after = window_after
        self._patterns: dict[str, re.Pattern[str]] = {}
        for key, words in terms.items():
            parts = []
            for word in sorted({fold(w) for w in words if w.strip()}, key=len, reverse=True):
                escaped = re.escape(word).replace(r"\ ", r"\s*")
                if word.isascii():
                    parts.append(rf"(?<![a-z0-9]){escaped}(?![a-z])")
                else:
                    parts.append(escaped)
            if parts:
                self._patterns[key] = re.compile("|".join(parts))

    def keys(self) -> set[str]:
        return set(self._patterns)

    def has_context(self, folded_text: str, key: str, start: int, end: int) -> bool:
        pattern = self._patterns.get(key)
        if pattern is None:
            return False
        before = folded_text[max(0, start - self.window_before) : start]
        after = folded_text[end : end + self.window_after]
        return bool(pattern.search(before) or pattern.search(after))


@dataclass(frozen=True)
class AnalysisInput:
    """Everything a recognizer may need, computed once per call.

    ``segments`` lists ``(start, end, language)`` runs of Arabic or Latin script,
    so language-specific models only see text in their own language.
    """

    text: str
    folded: str
    context: ContextMatcher
    segments: tuple[tuple[int, int, str], ...] = ()


class Recognizer(ABC):
    """Base class for every recognizer."""

    name: str = "recognizer"

    @abstractmethod
    def analyze(self, data: AnalysisInput) -> list[Detection]:
        """Return detections in ``data.text`` coordinates."""


Validator = Callable[[str], bool]


@dataclass(frozen=True)
class Pattern:
    regex: str
    score: float
    name: str = ""


class PatternRecognizer(Recognizer):
    """Regex + optional validator + optional context words."""

    def __init__(
        self,
        name: str,
        entity_type: str,
        patterns: Sequence[Pattern],
        *,
        validator: Validator | None = None,
        validated_score: float = 0.95,
        context_key: str | None = None,
        context_boost: float = 0.35,
        flags: int = re.IGNORECASE,
        preprocess: Callable[[str], str] | None = None,
    ) -> None:
        self.name = name
        self.entity_type = entity_type
        self._patterns = [(re.compile(p.regex, flags), p.score) for p in patterns]
        self.validator = validator
        self.validated_score = validated_score
        self.context_key = context_key
        self.context_boost = context_boost
        self.preprocess = preprocess

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        found: dict[tuple[int, int], float] = {}
        for regex, base in self._patterns:
            for m in regex.finditer(data.text):
                start, end = m.span("value") if "value" in regex.groupindex else m.span()
                if start == end:
                    continue
                score = base
                if self.validator is not None:
                    value = m.group("value") if "value" in regex.groupindex else m.group()
                    if self.preprocess is not None:
                        value = self.preprocess(value)
                    if not self.validator(value):
                        continue
                    score = max(score, self.validated_score)
                if self.context_key and data.context.has_context(
                    data.folded, self.context_key, start, end
                ):
                    score = min(1.0, score + self.context_boost)
                key = (start, end)
                found[key] = max(found.get(key, 0.0), score)
        return [Detection(self.entity_type, s, e, sc, self.name) for (s, e), sc in found.items()]
