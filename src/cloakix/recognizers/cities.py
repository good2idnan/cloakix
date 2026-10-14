"""City and place names from the region packs (a small gazetteer).

NER models miss some Arabic city names (e.g. "جدة", "القاهرة"), so each region pack lists its
main cities. Arabic names also match with an attached prefix: "بجدة", "والرياض", "للرياض".
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from cloakix.normalize import fold
from cloakix.recognizers.base import AnalysisInput, Detection, Recognizer

_AR = "ء-ي"


def _alternation(words: Iterable[str]) -> str:
    unique = sorted(set(words), key=len, reverse=True)
    return "|".join(re.escape(w).replace(r"\ ", r"\s+") for w in unique)


class CityRecognizer(Recognizer):
    name = "city"

    def __init__(self, cities: Iterable[str], score: float = 0.7) -> None:
        self.score = score
        arabic = [fold(c) for c in cities if re.search(f"[{_AR}]", c)]
        latin = [c for c in cities if c.isascii()]
        self._ar: list[re.Pattern[str]] = []
        if arabic:
            alts = _alternation(arabic)
            # Alone, or after one attached prefix letter (و ف ب ك ل), which stays unmasked.
            self._ar.append(
                re.compile(rf"(?:(?<![{_AR}])|(?<=(?<![{_AR}])[وفبكل]))(?:{alts})(?![{_AR}])")
            )
            # "لل" + name without its "ال": الرياض -> للرياض.
            short = [c[2:] for c in arabic if c.startswith("ال") and len(c) > 3]
            if short:
                self._ar.append(
                    re.compile(rf"(?<=(?<![{_AR}])لل)(?:{_alternation(short)})(?![{_AR}])")
                )
        # Latin names are matched case-sensitively, so "hail" (weather) is not "Hail" (city).
        self._en: re.Pattern[str] | None = None
        if latin:
            self._en = re.compile(rf"(?<![A-Za-z])(?:{_alternation(latin)})(?![A-Za-z])")

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        out = []
        for regex in self._ar:
            for m in regex.finditer(data.folded):
                out.append(Detection("LOCATION", m.start(), m.end(), self.score, self.name))
        if self._en is not None:
            for m in self._en.finditer(data.text):
                out.append(Detection("LOCATION", m.start(), m.end(), self.score, self.name))
        return out
