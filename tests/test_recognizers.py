import pytest

from cloakix import Masker

from conftest import found, make_iban, make_luhn

# --- phones -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "phone",
    [
        "0551234567",
        "055 123 4567",
        "055-123-4567",
        "+966 55 123 4567",
        "00966551234567",
        "+971 50 123 4567",
        "0501234567",
        "01012345678",
        "+20 100 123 4567",
        "+974 5512 3456",
        "+965 9876 5432",
        "+973 3312 3456",
        "+968 9123 4567",
    ],
)
def test_phone_formats(masker: Masker, phone: str) -> None:
    assert found(masker, f"my number {phone} thanks") == [("PHONE", phone)]


def test_phone_with_arabic_indic_digits(masker: Masker) -> None:
    assert found(masker, "جوالي ٠٥٥١٢٣٤٥٦٧") == [("PHONE", "٠٥٥١٢٣٤٥٦٧")]


def test_eight_digit_local_number_needs_context(masker: Masker) -> None:
    assert found(masker, "واتساب 55123456") == [("PHONE", "55123456")]


def test_date_is_not_a_phone(masker: Masker) -> None:
    assert found(masker, "visit 30-05-2026") == [("DATE", "30-05-2026")]


# --- national IDs -------------------------------------------------------------------------


def test_saudi_national_id_and_iqama(masker: Masker) -> None:
    nid, iqama = make_luhn("101234567"), make_luhn("201234567")
    text = f"رقم الهوية {nid} والإقامة {iqama}"
    assert found(masker, text) == [("NATIONAL_ID", nid), ("NATIONAL_ID", iqama)]


def test_emirates_id_with_dashes(masker: Masker) -> None:
    eid = make_luhn("78419901234567")
    formatted = f"{eid[:3]}-{eid[3:7]}-{eid[7:14]}-{eid[14]}"
    assert found(masker, f"Emirates ID {formatted}") == [("NATIONAL_ID", formatted)]


def test_emirates_id_with_wrong_check_digit_is_still_masked(masker: Masker) -> None:
    eid = make_luhn("78419901234567")
    typo = eid[:-1] + str((int(eid[-1]) + 1) % 10)
    formatted = f"{typo[:3]}-{typo[3:7]}-{typo[7:14]}-{typo[14]}"
    assert found(masker, f"رقم الهوية {formatted}") == [("NATIONAL_ID", formatted)]


def test_egypt_national_id(masker: Masker) -> None:
    assert found(masker, "الرقم القومي 29001010112345") == [("NATIONAL_ID", "29001010112345")]


def test_qatar_qid_with_context(masker: Masker) -> None:
    assert found(masker, "QID 28463412345") == [("NATIONAL_ID", "28463412345")]


# --- healthcare ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, value",
    [
        ("رقم الملف 778812", "778812"),
        ("ورقم ملفي 778812", "778812"),
        ("MRN: A-55821", "A-55821"),
        ("my file no is 99812", "99812"),
        ("patient id MR123456", "MR123456"),
    ],
)
def test_mrn_by_context(masker: Masker, text: str, value: str) -> None:
    assert found(masker, text) == [("MRN", value)]


def test_insurance_number(masker: Masker) -> None:
    assert found(masker, "رقم التأمين 55-12345678") == [("INSURANCE_NUMBER", "55-12345678")]


def test_unlabelled_long_number_is_caught_by_safety_net(masker: Masker) -> None:
    assert found(masker, "please check 9938271 again") == [("ID_NUMBER", "9938271")]


def test_year_is_not_an_id(masker: Masker) -> None:
    assert found(masker, "appointment in 2026 was late") == []


# --- financial & contact ------------------------------------------------------------------


def test_credit_card(masker: Masker) -> None:
    assert found(masker, "card 4111 1111 1111 1111") == [("CREDIT_CARD", "4111 1111 1111 1111")]


def test_iban_grouped_and_followed_by_words(masker: Masker) -> None:
    iban = make_iban("SA", "80000000608010167519")
    grouped = " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))
    assert found(masker, f"IBAN {grouped} please") == [("IBAN", grouped)]


def test_email_url_ip_handle(masker: Masker) -> None:
    text = "mail khalid.h@gmail.com, see https://example.com/p?id=1 from 10.0.0.12 @khalid_99"
    assert found(masker, text) == [
        ("EMAIL", "khalid.h@gmail.com"),
        ("URL", "https://example.com/p?id=1"),
        ("IP_ADDRESS", "10.0.0.12"),
        ("SOCIAL_HANDLE", "@khalid_99"),
    ]


def test_dates(masker: Masker) -> None:
    text = "زرت في 5 مارس 2026 ثم 12/04/2026 و 3 رمضان 1447 هـ"
    assert [t for t, _ in found(masker, text)] == ["DATE", "DATE", "DATE"]


def test_po_box(masker: Masker) -> None:
    assert found(masker, "ص.ب 12345 الرياض") == [("ADDRESS", "ص.ب 12345"), ("LOCATION", "الرياض")]


# --- names (rules) ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, name",
    [
        ("الدكتور خالد الحربي كان ممتاز", "خالد الحربي"),
        ("شكرا للدكتورة نورة", "نورة"),
        ("الدكتور الاستشاري خالد العمري ممتاز", "خالد العمري"),
        ("اسمي عبد الله بن سعيد", "عبد الله بن سعيد"),
        ("Dr. Sara Al-Qahtani was great", "Sara Al-Qahtani"),
        ("my name is Omar Farouk", "Omar Farouk"),
    ],
)
def test_names_after_titles(masker: Masker, text: str, name: str) -> None:
    assert found(masker, text) == [("PERSON", name)]


def test_title_followed_by_ordinary_word_is_not_a_name(masker: Masker) -> None:
    assert found(masker, "الدكتور كان ممتاز جدا") == []
    assert found(masker, "the doctor was great") == []


def test_two_titles_give_two_names(masker: Masker) -> None:
    assert found(masker, "شكرا للدكتور عبد الله القحطاني والدكتورة نورة") == [
        ("PERSON", "عبد الله القحطاني"),
        ("PERSON", "نورة"),
    ]


# --- cities (gazetteer, no model needed) --------------------------------------------------


@pytest.mark.parametrize(
    "text, city",
    [
        ("الدكتور ما شافني في فرع جدة", "جدة"),
        ("ساكن بجدة من سنتين", "جدة"),
        ("رحت للرياض أمس", "رياض"),
        ("حجزت في الإسكندرية", "الإسكندرية"),
        ("The branch in Al Khobar was clean", "Al Khobar"),
        ("I flew from Cairo", "Cairo"),
    ],
)
def test_city_names(masker: Masker, text: str, city: str) -> None:
    assert found(masker, text) == [("LOCATION", city)]


def test_common_words_are_not_cities(masker: Masker) -> None:
    assert found(masker, "العين حمراء والخبر وصلني متأخر") == []
    assert found(masker, "There was hail outside") == []


# --- invisible characters around a value ---------------------------------------------------


def test_hijri_date_masks_the_whole_marker(masker: Masker) -> None:
    text = "الموعد 12 رمضان 1447 هـ تأجل"
    assert masker.mask(text).text == "الموعد <DATE_1> تأجل"
