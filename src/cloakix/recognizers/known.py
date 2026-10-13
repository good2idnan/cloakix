"""Mask values you already know, e.g. the patient's name and MRN from your database.

This is the most reliable detection method: when a comment is linked to a patient,
pass their details and every occurrence is masked, whatever its format.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

from cloakix.normalize import fold, normalize
from cloakix.recognizers.base import AnalysisInput, Detection, Recognizer
from cloakix.recognizers.names import AR_NAME_CONNECTORS

_WORD_CHARS = r"0-9A-Za-zء-ي"
_EN_CONNECTORS = frozenset(["bin", "bint", "ibn", "al", "el", "abu", "abd", "abdul"])


def _value_pattern(value: str) -> str | None:
    folded = fold(normalize(value).text).strip()
    if not folded:
        return None
    digits = [c for c in folded if c.isdigit()]
    if len(digits) >= 4 and len(digits) >= 0.6 * len(re.sub(r"\W", "", folded)):
        # Mostly numeric: allow any separators between characters ("055 123-4567").
        chars = [c for c in folded if c.isalnum()]
        body = r"[\s\-./]?".join(re.escape(c) for c in chars)
    else:
        body = r"\s+".join(re.escape(part) for part in folded.split())
    start = rf"(?<![{_WORD_CHARS}])"
    if "ء" <= folded[0] <= "ي":
        # Also match after an attached Arabic prefix: "ومحمد", "لمحمد" (prefix stays unmasked).
        start = rf"(?:{start}|(?<=(?<![{_WORD_CHARS}])[وفبكل]))"
    return rf"{start}{body}(?![{_WORD_CHARS}])"


class KnownValuesRecognizer(Recognizer):
    name = "known_value"

    def __init__(self, values: Mapping[str, Iterable[str]], split_names: bool = True) -> None:
        self._patterns: list[tuple[str, re.Pattern[str]]] = []
        for entity_type, items in values.items():
            for value in items:
                candidates = {value}
                if split_names and entity_type == "PERSON":
                    for part in fold(normalize(value).text).split():
                        if (
                            len(part) >= 3
                            and part not in AR_NAME_CONNECTORS
                            and part not in _EN_CONNECTORS
                        ):
                            candidates.add(part)
                for candidate in candidates:
                    pattern = _value_pattern(candidate)
                    if pattern:
                        self._patterns.append((entity_type.upper(), re.compile(pattern)))

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        out = []
        for entity_type, regex in self._patterns:
            for m in regex.finditer(data.folded):
                out.append(Detection(entity_type, m.start(), m.end(), 1.0, self.name))
        return out
