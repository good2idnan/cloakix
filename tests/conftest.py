"""Shared fixtures. All identifiers in the tests are fictitious."""

from __future__ import annotations

import pytest

from cloakix import Masker
from cloakix.validators import luhn_check_digit


@pytest.fixture(scope="session")
def masker() -> Masker:
    """Rules-only masker: fast and deterministic (no model download)."""
    return Masker(ner=False)


def make_luhn(prefix: str) -> str:
    return prefix + luhn_check_digit(prefix)


def make_iban(country: str, bban: str) -> str:
    numeric = "".join(str(int(c, 36)) for c in bban + country + "00")
    check = 98 - int(numeric) % 97
    return f"{country}{check:02d}{bban}"


def found(masker: Masker, text: str) -> list[tuple[str, str]]:
    """(type, value) pairs detected in ``text``."""
    return [(e.type, text[e.start : e.end]) for e in masker.analyze(text)]
