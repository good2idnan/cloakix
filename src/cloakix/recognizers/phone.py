"""Phone number recognizer driven by per-country rules (see ``cloakix.regions``)."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from cloakix.recognizers.base import AnalysisInput, Detection, Recognizer


@dataclass(frozen=True)
class PhoneRule:
    """How phone numbers look in one country.

    Attributes:
        country: region code, e.g. ``"sa"``.
        calling_code: international calling code without ``+``, e.g. ``"966"``.
        national: regex for the national significant number (no trunk prefix).
        trunk_prefix: digit dialled before the national number locally (``"0"``), or ``""``.
        bare_local: optional regex for numbers written locally without any prefix
            (8-digit countries such as Qatar or Kuwait). These score low on their own
            and need a context word such as "mobile" / "جوال" to be masked as PHONE.
    """

    country: str
    calling_code: str
    national: str
    trunk_prefix: str = "0"
    bare_local: str | None = None


# A run of digits with optional separators: "+966 55 123 4567", "(055) 123-4567", "0551234567".
_CANDIDATE = re.compile(r"(?<![0-9A-Za-z])(?:\+|\()?[0-9][0-9 \-.()]*[0-9](?![0-9A-Za-z])")
_GROUP = re.compile(r"\+?[0-9]+")
_DATE_SHAPE = re.compile(
    r"[0-9]{1,2}[\-.][0-9]{1,2}[\-.][0-9]{2,4}|[0-9]{4}[\-.][0-9]{1,2}[\-.][0-9]{1,2}"
)

SCORE_INTERNATIONAL = 0.9
SCORE_LOCAL = 0.75
SCORE_CALLING_CODE_NO_PLUS = 0.7
SCORE_UNKNOWN_INTERNATIONAL = 0.6
SCORE_BARE_LOCAL = 0.45


class PhoneRecognizer(Recognizer):
    name = "phone"

    def __init__(self, rules: Sequence[PhoneRule], context_boost: float = 0.35) -> None:
        # Longest calling codes first so "+971" is not mistaken for a shorter code.
        self.rules = sorted(rules, key=lambda r: len(r.calling_code), reverse=True)
        self._national = {r.country: re.compile(r.national) for r in self.rules}
        self._bare = {r.country: re.compile(r.bare_local) for r in self.rules if r.bare_local}
        self.context_boost = context_boost

    def _classify(
        self, digits: str, international: bool, plus: bool = False
    ) -> tuple[str, float] | None:
        if international:
            for rule in self.rules:
                if digits.startswith(rule.calling_code):
                    nsn = digits[len(rule.calling_code) :]
                    if rule.trunk_prefix and nsn.startswith(rule.trunk_prefix):
                        nsn = nsn[len(rule.trunk_prefix) :]  # "+966 055..." is common
                    if self._national[rule.country].fullmatch(nsn):
                        return rule.country, SCORE_INTERNATIONAL
            # Other countries: trust the "+" sign, but not a bare "00" prefix.
            if plus and 8 <= len(digits) <= 15:
                return "intl", SCORE_UNKNOWN_INTERNATIONAL
            return None
        for rule in self.rules:
            tp = rule.trunk_prefix
            if (
                tp
                and digits.startswith(tp)
                and self._national[rule.country].fullmatch(digits[len(tp) :])
            ):
                return rule.country, SCORE_LOCAL
        for rule in self.rules:
            if digits.startswith(rule.calling_code) and self._national[rule.country].fullmatch(
                digits[len(rule.calling_code) :]
            ):
                return rule.country, SCORE_CALLING_CODE_NO_PLUS
        for rule in self.rules:
            bare = self._bare.get(rule.country)
            if bare is not None and bare.fullmatch(digits):
                return rule.country, SCORE_BARE_LOCAL
        return None

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        text = data.text
        out: list[Detection] = []
        for cand in _CANDIDATE.finditer(text):
            groups = [
                (cand.start() + g.start(), cand.start() + g.end())
                for g in _GROUP.finditer(cand.group())
            ]
            i = 0
            while i < len(groups):
                hit = None
                # Longest valid number starting at group i wins.
                for j in range(min(len(groups), i + 6) - 1, i - 1, -1):
                    start, end = groups[i][0], groups[j][1]
                    raw = text[start:end]
                    digits = "".join(c for c in raw if c.isascii() and c.isdigit())
                    if not 7 <= len(digits) <= 15 or _DATE_SHAPE.fullmatch(raw):
                        continue
                    international = raw.startswith("+") or digits.startswith("00")
                    if digits.startswith("00"):
                        digits = digits[2:]
                    result = self._classify(digits, international, raw.startswith("+"))
                    if result is not None:
                        hit = (start, end, result, j)
                        break
                if hit is None:
                    i += 1
                    continue
                start, end, (country, score), j = hit
                if data.context.has_context(data.folded, "PHONE", start, end):
                    score = min(1.0, score + self.context_boost)
                out.append(Detection("PHONE", start, end, score, f"phone_{country}"))
                i = j + 1
        return out
