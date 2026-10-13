"""Kuwait: Civil ID and phone numbers."""

from __future__ import annotations

from cloakix.packs import RegionPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.phone import PhoneRule
from cloakix.validators import kuwait_civil_id_valid

PHONE = PhoneRule(
    country="kw",
    calling_code="965",
    national=r"[2569][0-9]{7}",
    trunk_prefix="",
    bare_local=r"[569][0-9]{7}",
)


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "kw_civil_id",
            "NATIONAL_ID",
            # 12 digits: century + YYMMDD birth date + serial + check digit.
            [Pattern(r"(?<![0-9A-Za-z])[23][0-9]{11}(?![0-9A-Za-z])", 0.3)],
            validator=kuwait_civil_id_valid,
            validated_score=0.7,
            context_key="NATIONAL_ID",
        )
    ]


PACK = RegionPack(code="kw", name="Kuwait", phone_rules=[PHONE], recognizers=_recognizers)
