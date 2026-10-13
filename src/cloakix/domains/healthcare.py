"""Healthcare domain: medical record numbers (MRN) and insurance numbers.

MRN formats differ between hospitals (plain digits, letters + digits, with dashes),
so they are detected from context words such as "MRN" or "رقم الملف".
Unlabelled long numbers are still caught by the general ``ID_NUMBER`` safety net.
"""

from __future__ import annotations

from cloakix.packs import DomainPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.common import ID_TOKEN

CONTEXT = {
    "en": {
        "MRN": [
            "mrn",
            "mr#",
            "mr no",
            "mr number",
            "medical record",
            "medical record number",
            "record no",
            "record number",
            "file",
            "file no",
            "file number",
            "file#",
            "hospital no",
            "hospital number",
            "patient no",
            "patient number",
            "patient id",
            "health record",
            "health id",
        ],
        "INSURANCE": [
            "insurance",
            "insurance no",
            "insurance number",
            "insurance card",
            "policy",
            "policy no",
            "policy number",
            "member id",
            "member no",
            "membership",
        ],
    },
    "ar": {
        "MRN": [
            "ملف",
            "رقم الملف",
            "ملفي",
            "رقم ملفي",
            "الملف الطبي",
            "رقم المريض",
            "الرقم الطبي",
            "السجل الطبي",
            "رقم السجل",
            "سجل طبي",
            "رقم المراجع",
        ],
        "INSURANCE": [
            "تأمين",
            "التأمين",
            "بطاقة التأمين",
            "رقم التأمين",
            "بوليصة",
            "وثيقة التأمين",
            "رقم العضوية",
            "العضوية",
        ],
    },
}


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "mrn",
            "MRN",
            [Pattern(ID_TOKEN, 0.15)],
            context_key="MRN",
            context_boost=0.6,
        ),
        PatternRecognizer(
            "insurance_number",
            "INSURANCE_NUMBER",
            [Pattern(ID_TOKEN, 0.15)],
            context_key="INSURANCE",
            context_boost=0.55,
        ),
    ]


PACK = DomainPack(code="healthcare", name="Healthcare", context=CONTEXT, recognizers=_recognizers)
