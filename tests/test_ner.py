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


@pytest.mark.parametrize(
    "text, expected",
    [
        # The ID number is masked, the word "Iqama" in front of it is not.
        (
            "New employee Sara Al-Qahtani, Iqama 2012345670, mobile 0559998877",
            "New employee <PERSON_1>, Iqama <NATIONAL_ID_1>, mobile <PHONE_1>",
        ),
        ("I waited 45 minutes in the ER", "I waited 45 minutes in the ER"),
        ("Emirates ID 784-1990-1234567-6", "Emirates ID <NATIONAL_ID_1>"),
        ("مستشفى الملك فهد تعامله راقي", "مستشفى الملك فهد تعامله راقي"),
    ],
)
def test_model_does_not_mask_labels_and_common_words(
    ner_masker: Masker, text: str, expected: str
) -> None:
    assert ner_masker.mask(text).text == expected


def test_english_name_and_city(ner_masker: Masker) -> None:
    result = ner_masker.mask("I came with John Smith from Dubai.")
    assert result.text == "I came with <PERSON_1> from <LOCATION_1>."


def test_loading_does_not_download_unpinned_weights(monkeypatch: pytest.MonkeyPatch) -> None:
    """transformers would otherwise fetch a converted copy from an unmerged Hub pull request."""
    pytest.importorskip("transformers")
    import os

    import transformers.modeling_utils as modeling_utils

    from cloakix.languages import LANGUAGES
    from cloakix.ner.transformers_ner import TransformersNerRecognizer

    calls: list[object] = []
    monkeypatch.setattr(modeling_utils, "auto_conversion", lambda *a, **k: calls.append(a))
    monkeypatch.delenv("DISABLE_SAFETENSORS_CONVERSION", raising=False)
    spec = LANGUAGES["ar"].ner_model
    assert spec is not None
    TransformersNerRecognizer(spec).load()
    assert calls == []
    assert "DISABLE_SAFETENSORS_CONVERSION" not in os.environ  # caller's environment restored
