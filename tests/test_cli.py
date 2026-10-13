import json

import pytest

from cloakix.cli import main


def test_cli_mask(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["mask", "--no-ner", "جوالي 0551234567"]) == 0
    assert capsys.readouterr().out.strip() == "جوالي <PHONE_1>"


def test_cli_mask_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["mask", "--no-ner", "--json", "mail a@b.com"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["masked_text"] == "mail <EMAIL_1>"


def test_cli_entities(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["entities"]) == 0
    assert "NATIONAL_ID" in capsys.readouterr().out
