"""How a detected identifier is replaced.

=========  ==========================================  =============================
Operator   Output                                      Use when
=========  ==========================================  =============================
``tag``    ``<PERSON_1>``, ``<PHONE_2>`` (default)     LLM prompts, analytics
``type``   ``<PERSON>``                                you only need the type
``redact`` ``[REDACTED]``                              public release
``mask``   ``*******4567``, ``a****@mail.com``         showing data to staff
``hash``   ``<PERSON_3f9a1c2b7d4e>`` (needs a key)     same token across calls/DB rows
=========  ==========================================  =============================
"""

from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Mapping

from cloakix.normalize import fold, normalize

OPERATORS = ("tag", "type", "redact", "mask", "hash")

_NUMBER_LIKE = frozenset(
    [
        "PHONE",
        "CREDIT_CARD",
        "IBAN",
        "NATIONAL_ID",
        "PASSPORT",
        "MRN",
        "INSURANCE_NUMBER",
        "REFERENCE_NUMBER",
        "BANK_ACCOUNT",
        "ID_NUMBER",
        "IP_ADDRESS",
    ]
)


def identity(entity_type: str, value: str) -> str:
    """Canonical form, so "055 123 4567" and "0551234567" count as the same value."""
    folded = fold(normalize(value).text)
    if entity_type in _NUMBER_LIKE:
        return re.sub(r"[^0-9a-z]", "", folded)
    return " ".join(folded.split())


def _partial_mask(entity_type: str, value: str) -> str:
    if entity_type == "EMAIL" and "@" in value:
        local, _, domain = value.partition("@")
        return local[:1] + "*" * max(len(local) - 1, 3) + "@" + domain
    if entity_type in _NUMBER_LIKE:
        visible = 4
        alnum_positions = [i for i, c in enumerate(value) if c.isalnum()]
        keep = set(alnum_positions[-visible:]) if len(alnum_positions) > visible + 2 else set()
        return "".join(c if (not c.isalnum() or i in keep) else "*" for i, c in enumerate(value))
    return "".join("*" if not c.isspace() else c for c in value)


class Replacer:
    """Produces replacements for one masking call (keeps ``tag`` numbering consistent)."""

    def __init__(
        self,
        default: str = "tag",
        per_type: Mapping[str, str] | None = None,
        hash_key: bytes | None = None,
    ) -> None:
        self.default = default
        self.per_type = dict(per_type or {})
        self.hash_key = hash_key
        for op in [default, *self.per_type.values()]:
            if op not in OPERATORS:
                raise ValueError(f"Unknown operator {op!r}. Available: {', '.join(OPERATORS)}")
            if op == "hash" and not hash_key:
                raise ValueError("The 'hash' operator needs a secret key (hash_key=...)")
        self._numbers: dict[str, dict[str, int]] = {}

    def __call__(self, entity_type: str, value: str) -> str:
        op = self.per_type.get(entity_type, self.default)
        if op == "tag":
            seen = self._numbers.setdefault(entity_type, {})
            number = seen.setdefault(identity(entity_type, value), len(seen) + 1)
            return f"<{entity_type}_{number}>"
        if op == "type":
            return f"<{entity_type}>"
        if op == "redact":
            return "[REDACTED]"
        if op == "mask":
            return _partial_mask(entity_type, value)
        assert self.hash_key is not None
        message = f"{entity_type}:{identity(entity_type, value)}".encode()
        digest = hmac.new(self.hash_key, message, hashlib.sha256).hexdigest()[:12]
        return f"<{entity_type}_{digest}>"
