import pytest

from cloakix import Masker


def test_mixed_arabic_english_comment(masker: Masker) -> None:
    text = (
        "الدكتور خالد الحربي كان ممتاز، بس الانتظار طويل. "
        "My mobile 0551234567, file no 778812, email khalid.h@gmail.com"
    )
    assert masker.mask(text).text == (
        "الدكتور <PERSON_1> كان ممتاز، بس الانتظار طويل. "
        "My mobile <PHONE_1>, file no <MRN_1>, email <EMAIL_1>"
    )


def test_same_value_gets_same_tag(masker: Masker) -> None:
    text = "call 0551234567 or 055 123 4567 or 0501112222"
    assert masker.mask(text).text == "call <PHONE_1> or <PHONE_1> or <PHONE_2>"


def test_offsets_point_into_original_text(masker: Masker) -> None:
    text = "جوالي ٠٥٥١٢٣٤٥٦٧ شكرا"
    (entity,) = masker.analyze(text)
    assert text[entity.start : entity.end] == "٠٥٥١٢٣٤٥٦٧"


def test_text_without_identifiers_is_unchanged(masker: Masker) -> None:
    text = "الخدمة ممتازة والانتظار قصير. Great service!"
    result = masker.mask(text)
    assert result.text == text
    assert result.entities == []


@pytest.mark.parametrize(
    "operator, expected",
    [
        ("type", "call <PHONE>"),
        ("redact", "call [REDACTED]"),
        ("mask", "call ******4567"),
    ],
)
def test_operators(masker: Masker, operator: str, expected: str) -> None:
    assert masker.mask("call 0551234567", operator=operator).text == expected


def test_per_type_operator_and_keep() -> None:
    m = Masker(ner=False, operators={"EMAIL": "mask"}, keep=["DATE"])
    result = m.mask("email ahmed@mail.com on 12/03/2026")
    assert result.text == "email a****@mail.com on 12/03/2026"


def test_hash_operator_is_stable_across_calls() -> None:
    m = Masker(ner=False, operator="hash", hash_key="test-secret")
    first = m.mask("call 0551234567").text
    second = m.mask("رقمي 055-123-4567").text
    assert first.split()[-1] == second.split()[-1]
    assert first.startswith("call <PHONE_")


def test_hash_operator_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLOAKIX_HASH_KEY", raising=False)
    with pytest.raises(ValueError, match="secret key"):
        Masker(ner=False, operator="hash")


def test_known_values_are_always_masked(masker: Masker) -> None:
    text = "شكرا يا سلمان، ملفك 4471"
    result = masker.mask(text, known={"PERSON": ["سلمان الدوسري"], "MRN": ["4471"]})
    assert result.text == "شكرا يا <PERSON_1>، ملفك <MRN_1>"


def test_known_name_with_attached_prefix(masker: Masker) -> None:
    result = masker.mask("جاء وسلمان معه", known={"PERSON": ["سلمان"]})
    assert result.text == "جاء و<PERSON_1> معه"


def test_entities_selection() -> None:
    m = Masker(ner=False, entities=["PHONE"])
    assert m.mask("call 0551234567, mail a@b.com").text == "call <PHONE_1>, mail a@b.com"


def test_rejects_unknown_configuration() -> None:
    with pytest.raises(ValueError, match="Unknown region"):
        Masker(ner=False, regions=["xx"])
    with pytest.raises(ValueError, match="Unknown entity"):
        Masker(ner=False, keep=["NOT_A_TYPE"])
    with pytest.raises(ValueError, match="Unknown operator"):
        Masker(ner=False, operator="shred")


def test_batch(masker: Masker) -> None:
    results = masker.mask_batch(["call 0551234567", "no identifiers here"])
    assert [r.text for r in results] == ["call <PHONE_1>", "no identifiers here"]


def test_empty_text(masker: Masker) -> None:
    assert masker.mask("").text == ""


def test_very_long_words_are_kept_away_from_ner_segments() -> None:
    from cloakix.segments import script_segments

    text = "Sara Ali " + "a/" * 5000 + " Omar Khan"
    segments = script_segments(text)
    assert [text[s:e] for s, e, _ in segments] == ["Sara Ali", "Omar Khan"]
