"""Hostile inputs must not slow the engine down (all values are synthetic).

Before 0.1.2, inputs such as "1-1-1-…" took several seconds because of quadratic regex
backtracking. Each case below is the maximum API text length (20,000 characters).
"""

import time

import pytest

from cloakix import Masker

N = 20_000
BUDGET_S = 2.0  # generous for slow CI machines; locally these take well under 0.5 s

HOSTILE = {
    "dashed digits": "1-" * (N // 2),
    "slashed letters": "https://" + "a/" * (N // 2 - 5),
    "spaced digits": "1 " * (N // 2),
    "dotted digits": "1." * (N // 2),
    "long token": "A" * N,
    "email-like": "a@" + "b." * (N // 2 - 2) + "x",
    "arabic titles": "الدكتور " * (N // 8),
    "english titles": "Dr. " * (N // 4),
    "zero width": "​" * N,
}


@pytest.mark.parametrize("text", HOSTILE.values(), ids=HOSTILE.keys())
def test_hostile_input_is_fast(masker: Masker, text: str) -> None:
    start = time.perf_counter()
    masker.mask(text)
    assert time.perf_counter() - start < BUDGET_S


def test_text_with_thousands_of_identifiers_is_fast(masker: Masker) -> None:
    text = "0551234567 " * (N // 11)  # ~1,800 phone numbers
    start = time.perf_counter()
    result = masker.mask(text)
    assert time.perf_counter() - start < BUDGET_S
    assert len(result.entities) == N // 11


def test_many_known_values_are_fast(masker: Masker) -> None:
    known = {"PERSON": [f"name{i} person{i}" for i in range(500)]}  # API allows 200
    start = time.perf_counter()
    result = masker.mask("hello name5 person5", known=known)
    assert time.perf_counter() - start < BUDGET_S
    assert result.text == "hello <PERSON_1>"
