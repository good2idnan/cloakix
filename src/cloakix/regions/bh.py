"""Bahrain: CPR number and phone numbers."""

from __future__ import annotations

from cloakix.packs import RegionPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.phone import PhoneRule
from cloakix.validators import bahrain_cpr_valid

PHONE = PhoneRule(
    country="bh",
    calling_code="973",
    national=r"3[0-9]{7}|66[0-9]{6}|1[37][0-9]{6}",
    trunk_prefix="",
    bare_local=r"3[0-9]{7}|66[0-9]{6}",
)


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "bh_cpr",
            "NATIONAL_ID",
            # 9 digits starting with birth YYMM; no public checksum, so a context word is needed.
            [Pattern(r"(?<![0-9A-Za-z])[0-9]{9}(?![0-9A-Za-z])", 0.2)],
            validator=bahrain_cpr_valid,
            validated_score=0.35,
            context_key="NATIONAL_ID",
        )
    ]


PACK = RegionPack(code="bh", name="Bahrain", phone_rules=[PHONE], recognizers=_recognizers)
