"""Cloakix: detect and mask personal identifiers in Arabic and English text.

>>> from cloakix import Masker
>>> masker = Masker()
>>> masker.mask("اسمي أحمد العتيبي، جوالي 0551234567").text
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from cloakix.entities import ENTITIES
from cloakix.masker import Masker
from cloakix.types import Entity, MaskResult

try:
    __version__ = version("cloakix")
except PackageNotFoundError:  # pragma: no cover - running from a source checkout
    __version__ = "0.0.0"

__all__ = ["ENTITIES", "Entity", "MaskResult", "Masker", "__version__"]
