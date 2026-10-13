"""United Arab Emirates: Emirates ID and phone numbers."""

from __future__ import annotations

from cloakix.packs import RegionPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.phone import PhoneRule
from cloakix.validators import digits_only, emirates_id_valid

PHONE = PhoneRule(
    country="ae",
    calling_code="971",
    national=r"5[0-9]{8}|[2-79][0-9]{7}",  # mobile 05x, landline 02-09
)


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "ae_emirates_id",
            "NATIONAL_ID",
            # 784-YYYY-NNNNNNN-C, dashes optional; Luhn check digit.
            [
                Pattern(
                    r"(?<![0-9A-Za-z])784[ \-]?[0-9]{4}[ \-]?[0-9]{7}[ \-]?[0-9](?![0-9A-Za-z])",
                    0.5,
                )
            ],
            validator=emirates_id_valid,
            validated_score=0.95,
            preprocess=digits_only,
            context_key="NATIONAL_ID",
        )
    ]


PACK = RegionPack(
    code="ae", name="United Arab Emirates", phone_rules=[PHONE], recognizers=_recognizers
)
