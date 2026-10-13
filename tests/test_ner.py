"""Model tests: download ~870 MB on first run. Run with ``pytest -m ner``."""

import pytest

from cloakix import Masker

pytestmark = pytest.mark.ner


@pytest.fixture(scope="module")
def ner_masker() -> Masker:
    pytest.importorskip("transformers")
    return Masker(ner=True).load()


def test_arabic_name_without_title(ner_masker: Masker) -> None:
    text = "محمد صالح طلب مني أتواصل معكم"
    types = [(e.type, text[e.start : e.end]) for e in ner_masker.analyze(text)]
    assert ("PERSON", "محمد صالح") in types


def test_arabic_relative_and_city(ner_masker: Masker) -> None:
    result = ner_masker.mask("زرت المستشفى مع أخي فهد السبيعي في الرياض")
    assert result.text == "زرت المستشفى مع أخي <PERSON_1> في <LOCATION_1>"


def test_english_name_and_city(ner_masker: Masker) -> None:
    result = ner_masker.mask("I came with John Smith from Dubai.")
    assert result.text == "I came with <PERSON_1> from <LOCATION_1>."
