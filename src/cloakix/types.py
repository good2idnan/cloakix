"""Core data types returned by Cloakix."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Entity:
    """An identifier found in the text.

    ``start`` and ``end`` are character offsets into the **original** input text.
    The original value is deliberately not stored, so results can be logged or
    returned by an API without leaking the identifier itself.
    """

    type: str
    start: int
    end: int
    score: float
    recognizer: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["score"] = round(self.score, 4)
        return data


@dataclass(frozen=True)
class MaskResult:
    """The masked text plus the identifiers that were replaced."""

    text: str
    entities: list[Entity] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"masked_text": self.text, "entities": [e.to_dict() for e in self.entities]}
