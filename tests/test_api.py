from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from cloakix import Masker
from cloakix.api.app import create_app


@pytest.fixture()
def client(masker: Masker) -> Iterator[TestClient]:
    with TestClient(create_app(masker)) as c:
        yield c


def test_health(client: TestClient) -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_mask(client: TestClient) -> None:
    text = "اسمي أحمد، جوالي 0551234567"
    body = client.post("/v1/mask", json={"text": text}).json()
    assert body["masked_text"] == "اسمي <PERSON_1>، جوالي <PHONE_1>"
    phone = body["entities"][1]
    assert phone["type"] == "PHONE"
    assert text[phone["start"] : phone["end"]] == "0551234567"
    assert "0551234567" not in str(body)  # original values are never returned


def test_mask_with_operator_and_known(client: TestClient) -> None:
    body = client.post(
        "/v1/mask",
        json={
            "text": "call 0551234567, Salman",
            "operator": "type",
            "known": {"PERSON": ["Salman"]},
        },
    ).json()
    assert body["masked_text"] == "call <PHONE>, <PERSON>"


def test_batch(client: TestClient) -> None:
    body = client.post("/v1/mask/batch", json={"texts": ["call 0551234567", "hello"]}).json()
    assert [r["masked_text"] for r in body["results"]] == ["call <PHONE_1>", "hello"]


def test_analyze(client: TestClient) -> None:
    body = client.post("/v1/analyze", json={"text": "mail a@b.com"}).json()
    assert [e["type"] for e in body["entities"]] == ["EMAIL"]


def test_entities(client: TestClient) -> None:
    names = {e["name"] for e in client.get("/v1/entities").json()}
    assert {"PERSON", "PHONE", "MRN", "NATIONAL_ID"} <= names


def test_api_key(masker: Masker, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOAKIX_API_KEY", "s3cret")
    with TestClient(create_app(masker)) as c:
        assert c.post("/v1/mask", json={"text": "x"}).status_code == 401
        ok = c.post("/v1/mask", json={"text": "x"}, headers={"X-API-Key": "s3cret"})
        assert ok.status_code == 200


def test_text_too_long(masker: Masker, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOAKIX_MAX_TEXT_LENGTH", "10")
    with TestClient(create_app(masker)) as c:
        assert c.post("/v1/mask", json={"text": "x" * 11}).status_code == 422
