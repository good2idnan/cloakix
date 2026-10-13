"""Plug-in packs: languages, regions (countries) and domains (industries).

Adding a country, language or industry means adding one pack file and registering it;
the core engine does not change.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field

from cloakix.ner.spec import NerModelSpec
from cloakix.recognizers.base import Recognizer
from cloakix.recognizers.phone import PhoneRule

ContextTerms = Mapping[str, Sequence[str]]


def _no_recognizers() -> list[Recognizer]:
    return []


@dataclass(frozen=True)
class LanguagePack:
    """Words and models for one language.

    ``context`` maps a context key (e.g. ``"PHONE"``, ``"MRN"``) to words that, when found
    near a candidate value, raise its score.
    """

    code: str
    name: str
    context: ContextTerms
    recognizers: Callable[[], list[Recognizer]] = _no_recognizers
    ner_model: NerModelSpec | None = None


@dataclass(frozen=True)
class RegionPack:
    """Identifier formats for one country."""

    code: str
    name: str
    phone_rules: Sequence[PhoneRule] = ()
    recognizers: Callable[[], list[Recognizer]] = _no_recognizers


@dataclass(frozen=True)
class DomainPack:
    """Identifiers and context words for one industry, per language."""

    code: str
    name: str
    context: Mapping[str, ContextTerms] = field(default_factory=dict)
    recognizers: Callable[[], list[Recognizer]] = _no_recognizers
