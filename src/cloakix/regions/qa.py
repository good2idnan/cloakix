"""Qatar: QID and phone numbers."""

from __future__ import annotations

from cloakix.packs import RegionPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.phone import PhoneRule
from cloakix.validators import qatar_qid_valid

PHONE = PhoneRule(
    country="qa",
    calling_code="974",
    national=r"[3-7][0-9]{7}",
    trunk_prefix="",
    bare_local=r"[3-7][0-9]{7}",
)


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "qa_qid",
            "NATIONAL_ID",
            # 11 digits starting with 2 or 3; no public checksum, so a context word is needed.
            [Pattern(r"(?<![0-9A-Za-z])[23][0-9]{10}(?![0-9A-Za-z])", 0.3)],
            validator=qatar_qid_valid,
            validated_score=0.45,
            context_key="NATIONAL_ID",
        )
    ]


PACK = RegionPack(code="qa", name="Qatar", phone_rules=[PHONE], recognizers=_recognizers)
