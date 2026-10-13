"""Checksum and structure validators for identifiers.

Each validator receives the identifier as a string of ASCII digits/letters
(separators already removed) and returns ``True`` when it is plausible.
"""

from __future__ import annotations

import datetime as _dt
import ipaddress
import re

ASCII_DIGITS = "0123456789"


def digits_only(value: str) -> str:
    return "".join(c for c in value if c in ASCII_DIGITS)


def luhn_valid(number: str) -> bool:
    """Luhn (mod 10) checksum, used by payment cards, Saudi IDs and Emirates IDs."""
    if len(number) < 2 or not number.isascii() or not number.isdigit():
        return False
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def luhn_check_digit(partial: str) -> str:
    """Return the digit that makes ``partial + digit`` Luhn-valid."""
    for d in ASCII_DIGITS:
        if luhn_valid(partial + d):
            return d
    raise ValueError("unreachable")  # pragma: no cover


# ISO 13616 IBAN lengths for the supported regions plus common counterparts.
IBAN_LENGTHS: dict[str, int] = {
    "SA": 24,
    "AE": 23,
    "QA": 29,
    "KW": 30,
    "BH": 22,
    "OM": 23,
    "EG": 29,
    "JO": 30,
    "LB": 28,
    "PK": 24,
    "TR": 26,
    "GB": 22,
    "DE": 22,
    "FR": 27,
}

_IBAN_SHAPE = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}")


def iban_valid(value: str) -> bool:
    """IBAN structure + length (when the country is known) + mod-97 checksum."""
    iban = re.sub(r"[\s\-]", "", value).upper()
    if not _IBAN_SHAPE.fullmatch(iban):
        return False
    expected = IBAN_LENGTHS.get(iban[:2])
    if expected is not None and len(iban) != expected:
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = "".join(str(int(c, 36)) for c in rearranged)
    return int(numeric) % 97 == 1


def _valid_date(year: int, month: int, day: int) -> bool:
    try:
        date = _dt.date(year, month, day)
    except ValueError:
        return False
    return date <= _dt.date.today()


def saudi_id_valid(number: str) -> bool:
    """Saudi National ID (starts with 1) or Iqama (starts with 2): 10 digits, Luhn."""
    return len(number) == 10 and number[0] in "12" and luhn_valid(number)


def emirates_id_valid(number: str) -> bool:
    """Emirates ID: 784-YYYY-NNNNNNN-C (15 digits), Luhn."""
    return len(number) == 15 and number.startswith("784") and luhn_valid(number)


# Egyptian governorate codes used in digits 8-9 of the national ID (88 = born abroad).
EG_GOVERNORATES = frozenset(
    [
        "01",
        "02",
        "03",
        "04",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "31",
        "32",
        "33",
        "34",
        "35",
        "88",
    ]
)


def egypt_national_id_valid(number: str) -> bool:
    """Egyptian national ID: 14 digits = century + YYMMDD + governorate + serial + check.

    The check-digit algorithm is not public, so the birth date and governorate are validated.
    """
    if len(number) != 14 or number[0] not in "23":
        return False
    century = 1900 if number[0] == "2" else 2000
    year, month, day = century + int(number[1:3]), int(number[3:5]), int(number[5:7])
    return _valid_date(year, month, day) and number[7:9] in EG_GOVERNORATES


def kuwait_civil_id_valid(number: str) -> bool:
    """Kuwait Civil ID: 12 digits = century (2=1900s, 3=2000s) + YYMMDD + serial + check."""
    if len(number) != 12 or number[0] not in "23":
        return False
    century = 1900 if number[0] == "2" else 2000
    year, month, day = century + int(number[1:3]), int(number[3:5]), int(number[5:7])
    return _valid_date(year, month, day)


def qatar_qid_valid(number: str) -> bool:
    """Qatar ID: 11 digits starting with 2 or 3 (century of birth)."""
    return len(number) == 11 and number[0] in "23"


def bahrain_cpr_valid(number: str) -> bool:
    """Bahrain CPR: 9 digits starting with YYMM of birth."""
    return len(number) == 9 and 1 <= int(number[2:4]) <= 12


def ip_valid(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True
