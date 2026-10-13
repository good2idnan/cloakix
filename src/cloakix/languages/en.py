"""English language pack."""

from __future__ import annotations

from cloakix.ner.spec import NerModelSpec
from cloakix.packs import LanguagePack
from cloakix.recognizers.base import Recognizer
from cloakix.recognizers.names import EnglishTitleNameRecognizer

CONTEXT = {
    "PHONE": [
        "phone",
        "phone no",
        "mobile",
        "mobile no",
        "mob",
        "cell",
        "cellphone",
        "tel",
        "telephone",
        "call",
        "call me",
        "contact",
        "contact no",
        "whatsapp",
        "my number",
        "fax",
    ],
    "NATIONAL_ID": [
        "national id",
        "id no",
        "id number",
        "id#",
        "identity",
        "iqama",
        "emirates id",
        "eid",
        "qid",
        "qatar id",
        "civil id",
        "civil no",
        "civil number",
        "cpr",
        "national number",
        "nid",
        "residence permit",
        "resident id",
    ],
    "PASSPORT": ["passport", "passport no", "passport number"],
    "CREDIT_CARD": ["card", "credit card", "debit card", "visa", "mastercard", "mada"],
    "BANK_ACCOUNT": ["account", "account no", "account number", "acct", "a/c", "bank account"],
    "REFERENCE": [
        "appointment",
        "booking",
        "reservation",
        "invoice",
        "receipt",
        "claim",
        "ticket",
        "order",
        "case",
        "request",
        "reference",
        "ref",
        "complaint",
        "transaction",
    ],
    "ADDRESS": ["postal code", "post code", "zip", "zip code", "national address"],
}

TITLES = [
    "dr",
    "doctor",
    "mr",
    "mrs",
    "ms",
    "miss",
    "mx",
    "prof",
    "professor",
    "nurse",
    "sister",
    "patient",
    "sir",
    "madam",
    "eng",
    "engineer",
    "capt",
    "captain",
    "sheikh",
    "my son",
    "my daughter",
    "my wife",
    "my husband",
    "my father",
    "my mother",
    "my brother",
    "my sister",
]
STRONG_TITLES = ["my name is", "name is", "name:", "named"]

NER_MODEL = NerModelSpec(
    language="en",
    model_id="dslim/bert-base-NER",
    revision="d1a3e8f13f8c3566299d95fcfc9a8d2382a9affc",
    label_map={"PER": "PERSON", "LOC": "LOCATION", "ORG": "ORGANIZATION"},
    size_mb=433,
    license="MIT",
)


def _recognizers() -> list[Recognizer]:
    return [EnglishTitleNameRecognizer(TITLES, STRONG_TITLES)]


PACK = LanguagePack(
    code="en",
    name="English",
    context=CONTEXT,
    recognizers=_recognizers,
    ner_model=NER_MODEL,
)
