"""Saudi Arabia: National ID / Iqama and phone numbers."""

from __future__ import annotations

from cloakix.packs import RegionPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.phone import PhoneRule
from cloakix.validators import saudi_id_valid

PHONE = PhoneRule(
    country="sa",
    calling_code="966",
    national=r"5[0-9]{8}|1[1-7][0-9]{7}",  # mobile 05x, landline 011-017
)


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "sa_national_id",
            "NATIONAL_ID",
            # 10 digits: 1 = citizen (National ID), 2 = resident (Iqama); Luhn check digit.
            [Pattern(r"(?<![0-9A-Za-z])[12][0-9]{9}(?![0-9A-Za-z])", 0.3)],
            validator=saudi_id_valid,
            validated_score=0.85,
            context_key="NATIONAL_ID",
        )
    ]


PACK = RegionPack(code="sa", name="Saudi Arabia", phone_rules=[PHONE], recognizers=_recognizers)
