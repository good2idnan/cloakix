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
    ``ner_ignore`` lists words the NER model sometimes mistakes for names or places
    (e.g. "ER", "Iqama", "الملك"); a model detection made only of these words is dropped.
    """

    code: str
    name: str
    context: ContextTerms
    recognizers: Callable[[], list[Recognizer]] = _no_recognizers
    ner_model: NerModelSpec | None = None
    ner_ignore: Sequence[str] = ()


@dataclass(frozen=True)
class RegionPack:
    """Identifier formats and city names for one country.

    ``cities`` may mix Arabic and English spellings. Avoid names that are also common
    words (e.g. "العين" = "the eye"), which would be masked everywhere.
    """

    code: str
    name: str
    phone_rules: Sequence[PhoneRule] = ()
    recognizers: Callable[[], list[Recognizer]] = _no_recognizers
    cities: Sequence[str] = ()


@dataclass(frozen=True)
class DomainPack:
    """Identifiers and context words for one industry, per language."""

    code: str
    name: str
    context: Mapping[str, ContextTerms] = field(default_factory=dict)
    recognizers: Callable[[], list[Recognizer]] = _no_recognizers
