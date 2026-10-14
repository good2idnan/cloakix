"""Region-independent recognizers: email, URL, IP, card, IBAN, passport, dates and more."""

from __future__ import annotations

import re

from cloakix.recognizers.base import (
    AnalysisInput,
    Detection,
    Pattern,
    PatternRecognizer,
    Recognizer,
)
from cloakix.validators import digits_only, iban_valid, ip_valid, luhn_valid

# Boundaries for number-like values: not glued to other digits or Latin letters.
NB = r"(?<![0-9A-Za-z])"
NA = r"(?![0-9A-Za-z])"

# An ID-like token: 3+ digits, optionally letters, "-" or "/" (778812, MR-12345, A1234567).
# Plain years (Gregorian 1900-2099, Hijri 1300-1499) are excluded so dates near a keyword
# are not taken as IDs.
ID_TOKEN = (
    NB + r"(?!(?:13|14|19|20)[0-9]{2}" + NA + r")(?=[A-Za-z0-9/\-]*[0-9]{3})"
    r"[A-Za-z0-9][A-Za-z0-9/\-]{1,18}[A-Za-z0-9]" + NA
)


def email() -> Recognizer:
    return PatternRecognizer(
        "email",
        "EMAIL",
        [
            Pattern(
                r"(?<![\w.+\-])[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}",
                0.95,
            )
        ],
    )


def url() -> Recognizer:
    return PatternRecognizer(
        "url",
        "URL",
        [Pattern(r"(?:https?://|www\.)[^\s<>\"'،]*[^\s<>\"'،.,;:!?)\]]", 0.85)],
    )


def ip_address() -> Recognizer:
    return PatternRecognizer(
        "ip_address",
        "IP_ADDRESS",
        [
            Pattern(r"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])", 0.5),
            Pattern(r"(?<![\w:])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{1,4}(?![\w:])", 0.5),
        ],
        validator=ip_valid,
        validated_score=0.8,
    )


def _card_valid(number: str) -> bool:
    return 13 <= len(number) <= 19 and number[0] in "23456" and luhn_valid(number)


def credit_card() -> Recognizer:
    return PatternRecognizer(
        "credit_card",
        "CREDIT_CARD",
        [Pattern(NB + r"[0-9](?:[ \-]?[0-9]){12,18}" + NA, 0.3)],
        validator=_card_valid,
        validated_score=0.9,
        preprocess=digits_only,
        context_key="CREDIT_CARD",
    )


class IbanRecognizer(Recognizer):
    """IBANs, optionally written in groups of four. Picks the longest checksum-valid span."""

    name = "iban"
    _START = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]{2}[0-9]{2}(?:[ \-]?[A-Za-z0-9]){11,32}")

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        out = []
        for m in self._START.finditer(data.text):
            raw = m.group()
            # Grouped IBANs may only end at a group boundary; compact ones anywhere.
            if " " in raw or "-" in raw:
                ends = [i for i, ch in enumerate(raw) if ch in " -"] + [len(raw)]
            else:
                ends = list(range(15, len(raw) + 1))
            for end in sorted(ends, reverse=True):
                if end >= 15 and iban_valid(raw[:end]):
                    out.append(Detection("IBAN", m.start(), m.start() + end, 0.95, self.name))
                    break
        return out


def passport() -> Recognizer:
    return PatternRecognizer(
        "passport",
        "PASSPORT",
        [Pattern(NB + r"[A-Za-z]{1,2}[0-9]{6,9}" + NA, 0.2)],
        context_key="PASSPORT",
        context_boost=0.5,
    )


def social_handle() -> Recognizer:
    return PatternRecognizer(
        "social_handle",
        "SOCIAL_HANDLE",
        [Pattern(r"(?<![\w@])@[A-Za-z0-9_](?:[A-Za-z0-9_.]{0,28}[A-Za-z0-9_])?(?![\w@])", 0.7)],
    )


def bank_account() -> Recognizer:
    return PatternRecognizer(
        "bank_account",
        "BANK_ACCOUNT",
        [Pattern(NB + r"[0-9](?:[ \-]?[0-9]){7,21}" + NA, 0.2)],
        context_key="BANK_ACCOUNT",
        context_boost=0.4,
    )


def reference_number() -> Recognizer:
    """Booking, appointment, invoice, claim, ticket numbers: context-driven."""
    return PatternRecognizer(
        "reference_number",
        "REFERENCE_NUMBER",
        [Pattern(ID_TOKEN, 0.15)],
        context_key="REFERENCE",
        context_boost=0.55,
    )


def po_box() -> Recognizer:
    return PatternRecognizer(
        "po_box",
        "ADDRESS",
        [
            Pattern(
                r"(?:P\.?\s?O\.?\s?Box|Post\s+Box|ص\s?\.\s?ب\s?\.?|صندوق\s+(?:ال)?بريد)"
                r"\s*[:#.]?\s*[0-9]{2,7}",
                0.85,
            ),
            Pattern(NB + r"[0-9]{5}(?:-[0-9]{4})?" + NA, 0.15),
        ],
        context_key="ADDRESS",
        context_boost=0.45,
    )


def long_number() -> Recognizer:
    """Safety net: any standalone number of 6+ digits not identified as something else."""
    return PatternRecognizer(
        "long_number",
        "ID_NUMBER",
        [
            Pattern(
                r"(?<![0-9A-Za-z.,])(?:[A-Za-z]{1,3}[\-/]?)?[0-9]{6,20}(?![0-9A-Za-z]|[.,][0-9])",
                0.5,
            )
        ],
    )


# --- dates ----------------------------------------------------------------------------------

_EN_MONTHS = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
    r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)
_AR_MONTHS = "|".join(
    [
        # Gregorian (Gulf/Egypt) and Levantine month names
        "يناير",
        "فبراير",
        "مارس",
        "أبريل",
        "ابريل",
        "إبريل",
        "مايو",
        "يونيو",
        "يونيه",
        "يوليو",
        "يوليه",
        "أغسطس",
        "اغسطس",
        "سبتمبر",
        "أكتوبر",
        "اكتوبر",
        "نوفمبر",
        "ديسمبر",
        "كانون الثاني",
        "شباط",
        "آذار",
        "اذار",
        "نيسان",
        "أيار",
        "ايار",
        "حزيران",
        "تموز",
        "آب",
        "اب",
        "أيلول",
        "ايلول",
        "تشرين الأول",
        "تشرين الاول",
        "تشرين الثاني",
        "كانون الأول",
        "كانون الاول",
        # Hijri months
        "محرم",
        "صفر",
        "ربيع الأول",
        "ربيع الاول",
        "ربيع الآخر",
        "ربيع الاخر",
        "ربيع الثاني",
        "جمادى الأولى",
        "جمادى الاولى",
        "جمادى الآخرة",
        "جمادى الاخرة",
        "جمادى الثانية",
        "رجب",
        "شعبان",
        "رمضان",
        "شوال",
        "ذو القعدة",
        "ذي القعدة",
        "ذو الحجة",
        "ذي الحجة",
    ]
)


def _numeric_date_valid(value: str) -> bool:
    parts = [int(p) for p in re.split(r"[/\-.]", value)]
    if len(parts) != 3:
        return False
    if parts[0] > 999:  # year first: Y-M-D
        _, a, b = parts
        return 1 <= a <= 12 and 1 <= b <= 31
    a, b, _ = parts  # D/M/Y or M/D/Y
    return (1 <= a <= 31 and 1 <= b <= 12) or (1 <= a <= 12 and 1 <= b <= 31)


def date() -> Recognizer:
    year = r"(?:19|20|13|14)[0-9]{2}"
    return PatternRecognizer(
        "date",
        "DATE",
        [
            Pattern(
                r"(?<![0-9])[0-9]{1,2}[/\-][0-9]{1,2}[/\-](?:" + year + r"|[0-9]{2})(?![0-9])", 0.6
            ),
            Pattern(r"(?<![0-9.])[0-9]{1,2}\.[0-9]{1,2}\." + year + r"(?![0-9])", 0.6),
            Pattern(r"(?<![0-9])" + year + r"[/\-.][0-9]{1,2}[/\-.][0-9]{1,2}(?![0-9])", 0.6),
        ],
        validator=_numeric_date_valid,
        validated_score=0.6,
    )


def date_text() -> Recognizer:
    year = r"(?:[0-9]{4}|[0-9]{2})"
    return PatternRecognizer(
        "date_text",
        "DATE",
        [
            Pattern(
                r"(?<![0-9])[0-9]{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:"
                + _EN_MONTHS
                + r")\.?(?:,?\s+"
                + year
                + r")?(?![A-Za-z0-9])",
                0.6,
            ),
            Pattern(
                r"(?<![A-Za-z])(?:" + _EN_MONTHS + r")\.?\s+[0-9]{1,2}(?:st|nd|rd|th)?"
                r"(?:,?\s+" + year + r")?(?![0-9])",
                0.6,
            ),
            Pattern(
                r"(?<![0-9])[0-9]{1,2}\s*(?:من\s+)?(?:" + _AR_MONTHS + r")"
                r"(?:\s*(?:سنة|عام)?\s*[0-9]{2,4})?(?:\s*(?:هـ|ه|م)(?![ء-ي]))?",
                0.6,
            ),
        ],
    )


def default_recognizers(catch_all_numbers: bool = True) -> list[Recognizer]:
    recognizers = [
        email(),
        url(),
        ip_address(),
        credit_card(),
        IbanRecognizer(),
        passport(),
        social_handle(),
        bank_account(),
        reference_number(),
        po_box(),
        date(),
        date_text(),
    ]
    if catch_all_numbers:
        recognizers.append(long_number())
    return recognizers
