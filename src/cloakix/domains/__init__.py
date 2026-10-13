"""Domain (industry) packs. To add one, create ``<code>.py`` with a ``PACK`` and register it."""

from __future__ import annotations

from cloakix.domains import healthcare
from cloakix.packs import DomainPack

DOMAINS: dict[str, DomainPack] = {
    healthcare.PACK.code: healthcare.PACK,
}

__all__ = ["DOMAINS"]
