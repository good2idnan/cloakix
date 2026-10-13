"""NER recognizer backed by a Hugging Face token-classification model.

Requires the optional extra: ``pip install "cloakix[ner]"``.
The model is downloaded from the Hugging Face Hub on first use and cached locally
(``~/.cache/huggingface``). Set ``HF_HUB_OFFLINE=1`` to run fully offline after that.
"""

from __future__ import annotations

import threading
from typing import Any

from cloakix.ner.spec import NerModelSpec
from cloakix.recognizers.base import AnalysisInput, Detection, Recognizer

INSTALL_HINT = 'NER models need extra packages: pip install "cloakix[ner]"'


def _chunks(text: str, max_chars: int) -> list[tuple[int, str]]:
    """Split text at whitespace into pieces of at most ``max_chars`` (with offsets)."""
    pieces = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            cut = text.rfind(" ", start, end)
            if cut > start:
                end = cut
        pieces.append((start, text[start:end]))
        start = end
    return pieces


def _expand_to_word(text: str, start: int, end: int) -> tuple[int, int]:
    while start > 0 and text[start - 1].isalnum():
        start -= 1
    while end < len(text) and text[end].isalnum():
        end += 1
    return start, end


class TransformersNerRecognizer(Recognizer):
    def __init__(
        self, spec: NerModelSpec, device: int | str | None = None, max_chars: int = 1000
    ) -> None:
        self.spec = spec
        self.name = f"ner_{spec.language}"
        self.device = -1 if device is None else device
        self.max_chars = max_chars
        self._pipe: Any = None
        self._lock = threading.Lock()

    def load(self) -> None:
        """Download (if needed) and load the model. Called lazily on first use."""
        if self._pipe is not None:
            return
        try:
            from transformers import pipeline
            from transformers.utils import logging as hf_logging
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise ImportError(INSTALL_HINT) from exc
        # The NER checkpoints ship an unused pooler layer; hide the harmless load report
        # and the weight-loading progress bars, then restore the caller's settings.
        verbosity = hf_logging.get_verbosity()
        progress = hf_logging.is_progress_bar_enabled()
        hf_logging.set_verbosity_error()
        hf_logging.disable_progress_bar()
        try:
            self._pipe = pipeline(
                "token-classification",
                model=self.spec.model_id,
                revision=self.spec.revision,
                aggregation_strategy="simple",
                device=self.device,
            )
        finally:
            hf_logging.set_verbosity(verbosity)
            if progress:
                hf_logging.enable_progress_bar()

    def analyze(self, data: AnalysisInput) -> list[Detection]:
        segments = [s for s in data.segments if s[2] == self.spec.language]
        if not segments:
            return []
        self.load()
        out = []
        for seg_start, seg_end, _ in segments:
            for offset, chunk in _chunks(data.text[seg_start:seg_end], self.max_chars):
                with self._lock:  # tokenizers are not safe for concurrent calls
                    predictions = self._pipe(chunk)
                base = seg_start + offset
                for p in predictions:
                    entity_type = self.spec.label_map.get(str(p["entity_group"]))
                    if entity_type is None or p["start"] is None:
                        continue
                    start, end = _expand_to_word(data.text, base + p["start"], base + p["end"])
                    out.append(Detection(entity_type, start, end, float(p["score"]), self.name))
        return out
