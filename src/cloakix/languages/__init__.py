"""Language packs. To add a language, create ``<code>.py`` with a ``PACK`` and register it here."""

from __future__ import annotations

from cloakix.languages import ar, en
from cloakix.packs import LanguagePack

LANGUAGES: dict[str, LanguagePack] = {
    ar.PACK.code: ar.PACK,
    en.PACK.code: en.PACK,
}

__all__ = ["LANGUAGES"]
