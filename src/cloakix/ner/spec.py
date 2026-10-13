"""Description of a Hugging Face NER model used by a language pack."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class NerModelSpec:
    """A pinned token-classification model.

    ``revision`` is a commit hash, so every install downloads exactly the same weights.
    ``label_map`` maps the model's labels (after B-/I- merging) to Cloakix entity types;
    labels not in the map are ignored.
    """

    language: str
    model_id: str
    revision: str
    label_map: Mapping[str, str] = field(default_factory=dict)
    size_mb: int = 0
    license: str = ""
