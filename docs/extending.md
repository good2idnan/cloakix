# Extending Cloakix

Cloakix is organised as plug-in **packs**. The core engine never changes when you add one.

```
src/cloakix/
├── languages/   one file per language   (context words, titles, NER model)
├── regions/     one file per country    (phone formats, national IDs)
└── domains/     one file per industry   (MRN, insurance, …)
```

## Add a country

Example: Jordan. Verify every format against an official source before shipping.

1. Create `src/cloakix/regions/jo.py`:

```python
"""Jordan: national number and phone numbers."""

from __future__ import annotations

from cloakix.packs import RegionPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.phone import PhoneRule

PHONE = PhoneRule(
    country="jo",
    calling_code="962",
    national=r"7[789][0-9]{7}",  # mobile 077 / 078 / 079
)


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "jo_national_id",
            "NATIONAL_ID",
            [Pattern(r"(?<![0-9A-Za-z])[0-9]{10}(?![0-9A-Za-z])", 0.2)],
            context_key="NATIONAL_ID",  # needs a word like "الرقم الوطني" nearby
        )
    ]


PACK = RegionPack(code="jo", name="Jordan", phone_rules=[PHONE], recognizers=_recognizers)
```

2. Register it in `src/cloakix/regions/__init__.py` (and optionally add it to a group such as
   `"levant"`).
3. Add any new context words, such as `"الرقم الوطني"`, to the `NATIONAL_ID` list in
   `languages/ar.py`.
4. Add tests in `tests/test_recognizers.py` for valid **and** invalid examples.

Use `Masker(regions=["gcc", "eg", "jo"])`.

## Add a domain

Example: banking.

```python
# src/cloakix/domains/banking.py
from cloakix.packs import DomainPack
from cloakix.recognizers.base import Pattern, PatternRecognizer, Recognizer
from cloakix.recognizers.common import ID_TOKEN

CONTEXT = {
    "en": {"CUSTOMER_ID": ["customer id", "cif", "client number"]},
    "ar": {"CUSTOMER_ID": ["رقم العميل", "رقم الحساب الشخصي"]},
}


def _recognizers() -> list[Recognizer]:
    return [
        PatternRecognizer(
            "customer_id", "REFERENCE_NUMBER", [Pattern(ID_TOKEN, 0.15)],
            context_key="CUSTOMER_ID", context_boost=0.55,
        )
    ]


PACK = DomainPack(code="banking", name="Banking", context=CONTEXT, recognizers=_recognizers)
```

Register it in `src/cloakix/domains/__init__.py`. To introduce a new entity *type*, also add it
to `entities.py` and to `PRIORITY` in `merge.py`.

## Add a language

1. Create `src/cloakix/languages/<code>.py` with `CONTEXT`, title words for the name rules,
   and optionally a `NerModelSpec` pinned to a model commit hash.
2. Register it in `src/cloakix/languages/__init__.py`.

> Note: mixed text is currently split by **script** (Arabic vs Latin) in `segments.py`.
> A second Latin-script language (e.g. French) also needs language detection there, so its
> NER model receives only its own text.

## Write a custom recognizer

Any class with an `analyze(data) -> list[Detection]` method works:

```python
from cloakix.recognizers.base import AnalysisInput, Detection, Recognizer


class EmployeeIdRecognizer(Recognizer):
    name = "employee_id"

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        ...  # search data.text (normalized) or data.folded (lower-case, unified letters)
```
