from cloakix.validators import (
    bahrain_cpr_valid,
    egypt_national_id_valid,
    emirates_id_valid,
    iban_valid,
    kuwait_civil_id_valid,
    luhn_valid,
    saudi_id_valid,
)

from conftest import make_iban, make_luhn


def test_luhn() -> None:
    assert luhn_valid("4111111111111111")
    assert not luhn_valid("4111111111111112")


def test_saudi_id_and_iqama() -> None:
    assert saudi_id_valid(make_luhn("101234567"))
    assert saudi_id_valid(make_luhn("201234567"))
    assert not saudi_id_valid(make_luhn("301234567"))  # must start with 1 or 2
    valid = make_luhn("101234567")
    wrong_check_digit = valid[:-1] + str((int(valid[-1]) + 1) % 10)
    assert not saudi_id_valid(wrong_check_digit)


def test_emirates_id() -> None:
    assert emirates_id_valid(make_luhn("78419901234567"))
    assert not emirates_id_valid(make_luhn("78519901234567"))


def test_egypt_national_id() -> None:
    assert egypt_national_id_valid("29001010112345")  # 1990-01-01, Cairo (01)
    assert not egypt_national_id_valid("29013010112345")  # month 13
    assert not egypt_national_id_valid("29001014412345")  # governorate 44 does not exist


def test_kuwait_civil_id() -> None:
    assert kuwait_civil_id_valid("290010112345")
    assert not kuwait_civil_id_valid("290019912345")  # day 99


def test_bahrain_cpr() -> None:
    assert bahrain_cpr_valid("900112345")
    assert not bahrain_cpr_valid("901512345")


def test_iban() -> None:
    assert iban_valid(make_iban("SA", "80000000608010167519"))
    assert iban_valid(make_iban("EG", "0019000500000000263180002"))
    assert not iban_valid("SA0080000000608010167519")
    assert not iban_valid(make_iban("SA", "8000000060801016751"))  # wrong length for SA
