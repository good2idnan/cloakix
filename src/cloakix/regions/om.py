"""Oman: Civil number and phone numbers."""

from __future__ import annotations

from cloakix.packs import RegionPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.phone import PhoneRule

PHONE = PhoneRule(
    country="om",
    calling_code="968",
    national=r"[79][0-9]{7}|2[0-9]{7}",
    trunk_prefix="",
    bare_local=r"[79][0-9]{7}",
)


CITIES = [
    "مسقط",
    "صلالة",
    "صحار",
    "نزوى",
    "السيب",
    "Muscat",
    "Salalah",
    "Sohar",
    "Nizwa",
    "Seeb",
]


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "om_civil_id",
            "NATIONAL_ID",
            # Variable length, no public checksum: detected only next to a context word.
            [Pattern(r"(?<![0-9A-Za-z])[0-9]{6,9}(?![0-9A-Za-z])", 0.2)],
            context_key="NATIONAL_ID",
        )
    ]


PACK = RegionPack(
    code="om", name="Oman", phone_rules=[PHONE], recognizers=_recognizers, cities=CITIES
)
