from cloakix.normalize import fold, normalize


def test_arabic_indic_and_persian_digits_become_ascii() -> None:
    assert normalize("٠٥٥١٢٣٤٥٦٧").text == "0551234567"
    assert normalize("۰۳۰۰۱۲۳۴۵۶۷").text == "03001234567"


def test_hidden_characters_removed_and_offsets_mapped_back() -> None:
    original = "call 055​123‏4567 now"
    norm = normalize(original)
    assert norm.text == "call 0551234567 now"
    start = norm.text.index("0551234567")
    s, e = norm.to_original(start, start + 10)
    assert original[s:e] == "055​123‏4567"


def test_arabic_diacritics_and_tatweel_removed() -> None:
    assert normalize("مُحَمَّـــد").text == "محمد"


def test_fold_keeps_length_and_unifies_letters() -> None:
    text = "أحمد إبراهيم مدرسة MRN"
    folded = fold(text)
    assert len(folded) == len(text)
    assert folded == "احمد ابراهيم مدرسه mrn"
