"""Egypt: National ID and phone numbers."""

from __future__ import annotations

from cloakix.packs import RegionPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.phone import PhoneRule
from cloakix.validators import egypt_national_id_valid

PHONE = PhoneRule(
    country="eg",
    calling_code="20",
    # mobile 010/011/012/015; landline Cairo 02 + 8 digits, other areas 0xx + 7 digits
    national=r"1[0125][0-9]{8}|2[0-9]{8}|[3-9][0-9]{7,8}",
)


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "eg_national_id",
            "NATIONAL_ID",
            # 14 digits: century + YYMMDD + governorate + serial + check digit.
            [Pattern(r"(?<![0-9A-Za-z])[23][0-9]{13}(?![0-9A-Za-z])", 0.3)],
            validator=egypt_national_id_valid,
            validated_score=0.85,
            context_key="NATIONAL_ID",
        )
    ]


PACK = RegionPack(code="eg", name="Egypt", phone_rules=[PHONE], recognizers=_recognizers)
