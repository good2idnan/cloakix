"""The public entry point: ``Masker.mask(text)``."""

from __future__ import annotations

import importlib.util
import logging
import os
from collections.abc import Iterable, Mapping, Sequence

from cloakix.domains import DOMAINS
from cloakix.entities import DEFAULT_MASKED, ENTITIES
from cloakix.languages import LANGUAGES
from cloakix.merge import resolve
from cloakix.normalize import fold, normalize
from cloakix.operators import Replacer
from cloakix.packs import DomainPack, LanguagePack
from cloakix.recognizers import common
from cloakix.recognizers.base import AnalysisInput, ContextMatcher, Recognizer
from cloakix.recognizers.known import KnownValuesRecognizer
from cloakix.recognizers.phone import PhoneRecognizer
from cloakix.regions import resolve_regions
from cloakix.segments import script_segments
from cloakix.types import Entity, MaskResult

logger = logging.getLogger("cloakix")

KnownValues = Mapping[str, Iterable[str]]


def _pick(registry: Mapping[str, object], codes: Iterable[str], kind: str) -> list[str]:
    picked = []
    for code in codes:
        code = code.lower()
        if code not in registry:
            raise ValueError(f"Unknown {kind} {code!r}. Available: {', '.join(sorted(registry))}")
        picked.append(code)
    return picked


class Masker:
    """Detect and mask personal identifiers in Arabic and English text.

    Example:
        >>> masker = Masker(ner=False)
        >>> masker.mask("جوالي 0551234567").text
        'جوالي <PHONE_1>'

    Args:
        languages: language packs to load (``"ar"``, ``"en"``).
        regions: countries or groups (``"gcc"``, ``"sa"``, ``"ae"``, ``"qa"``, ``"kw"``,
            ``"bh"``, ``"om"``, ``"eg"``).
        domains: industry packs (``"healthcare"``).
        ner: use the NER models for names and places. ``None`` (default) uses them when
            ``cloakix[ner]`` is installed; ``False`` runs rules only.
        entities: entity types to mask (default: all except ``ORGANIZATION``).
        keep: entity types to leave unmasked, e.g. ``["LOCATION", "DATE"]``.
        operator: default replacement: ``tag``, ``type``, ``redact``, ``mask`` or ``hash``.
        operators: per-type operator overrides, e.g. ``{"PHONE": "mask"}``.
        score_threshold: minimum confidence (0-1) for a detection to be masked.
        catch_all_numbers: also mask any other number with 6+ digits as ``ID_NUMBER``.
        hash_key: secret for the ``hash`` operator (or env var ``CLOAKIX_HASH_KEY``).
        device: torch device for NER models (``-1``/``"cpu"``, ``0``/``"cuda"``).
    """

    def __init__(
        self,
        languages: Sequence[str] = ("ar", "en"),
        regions: Sequence[str] = ("gcc", "eg"),
        domains: Sequence[str] = ("healthcare",),
        *,
        ner: bool | None = None,
        entities: Iterable[str] | None = None,
        keep: Iterable[str] = (),
        operator: str = "tag",
        operators: Mapping[str, str] | None = None,
        score_threshold: float = 0.5,
        catch_all_numbers: bool = True,
        hash_key: str | bytes | None = None,
        device: int | str | None = None,
    ) -> None:
        self.languages: list[LanguagePack] = [
            LANGUAGES[c] for c in _pick(LANGUAGES, languages, "language")
        ]
        self.regions = resolve_regions(regions)
        self.domains: list[DomainPack] = [DOMAINS[c] for c in _pick(DOMAINS, domains, "domain")]

        wanted = {e.upper() for e in entities} if entities is not None else set(DEFAULT_MASKED)
        unknown = (wanted | {k.upper() for k in keep}) - set(ENTITIES)
        if unknown:
            raise ValueError(f"Unknown entity types: {', '.join(sorted(unknown))}")
        self.entities: frozenset[str] = frozenset(wanted - {k.upper() for k in keep})

        key = hash_key if hash_key is not None else os.environ.get("CLOAKIX_HASH_KEY")
        self._hash_key = key.encode() if isinstance(key, str) else key
        self._operator = operator
        self._operators = {k.upper(): v for k, v in (operators or {}).items()}
        Replacer(operator, self._operators, self._hash_key)  # validate early

        self.score_threshold = score_threshold
        self._context = self._build_context()
        self._recognizers = self._build_recognizers(catch_all_numbers)
        self._ner = self._build_ner(ner, device)

    # -- construction -----------------------------------------------------------------------

    def _build_context(self) -> ContextMatcher:
        terms: dict[str, list[str]] = {}
        for lang in self.languages:
            for key, words in lang.context.items():
                terms.setdefault(key, []).extend(words)
        lang_codes = {lang.code for lang in self.languages}
        for domain in self.domains:
            for lang_code, context in domain.context.items():
                if lang_code in lang_codes:
                    for key, words in context.items():
                        terms.setdefault(key, []).extend(words)
        return ContextMatcher(terms)

    def _build_recognizers(self, catch_all_numbers: bool) -> list[Recognizer]:
        recognizers: list[Recognizer] = common.default_recognizers(catch_all_numbers)
        phone_rules = [rule for region in self.regions for rule in region.phone_rules]
        recognizers.append(PhoneRecognizer(phone_rules))
        for region in self.regions:
            recognizers.extend(region.recognizers())
        for domain in self.domains:
            recognizers.extend(domain.recognizers())
        for lang in self.languages:
            recognizers.extend(lang.recognizers())
        return recognizers

    def _build_ner(self, ner: bool | None, device: int | str | None) -> list[Recognizer]:
        if ner is False:
            return []
        if importlib.util.find_spec("transformers") is None:
            if ner:
                from cloakix.ner.transformers_ner import INSTALL_HINT

                raise ImportError(INSTALL_HINT)
            logger.warning("NER disabled (%s). Using rules only.", "transformers not installed")
            return []
        from cloakix.ner.transformers_ner import TransformersNerRecognizer

        return [
            TransformersNerRecognizer(lang.ner_model, device=device)
            for lang in self.languages
            if lang.ner_model is not None
        ]

    # -- public API -------------------------------------------------------------------------

    @property
    def ner_enabled(self) -> bool:
        return bool(self._ner)

    def load(self) -> Masker:
        """Load NER models now instead of on the first call (useful at server start)."""
        for recognizer in self._ner:
            load = getattr(recognizer, "load", None)
            if load is not None:
                load()
        return self

    def analyze(self, text: str, *, known: KnownValues | None = None) -> list[Entity]:
        """Find identifiers without changing the text.

        Args:
            text: input text (Arabic, English or mixed).
            known: values you already know, e.g. ``{"PERSON": ["Ahmed Ali"], "MRN": ["778812"]}``.
                They are always masked wherever they appear.
        """
        if not text:
            return []
        norm = normalize(text)
        data = AnalysisInput(
            text=norm.text,
            folded=fold(norm.text),
            context=self._context,
            segments=script_segments(norm.text),
        )
        recognizers = [*self._recognizers, *self._ner]
        if known:
            recognizers.append(KnownValuesRecognizer(known))
        detections = [
            d
            for r in recognizers
            for d in r.analyze(data)
            if d.score >= self.score_threshold
            and (d.type in self.entities or d.recognizer == KnownValuesRecognizer.name)
        ]
        entities = []
        for d in resolve(detections, norm.text):
            start, end = norm.to_original(d.start, d.end)
            entities.append(Entity(d.type, start, end, d.score, d.recognizer))
        return entities

    def mask(
        self,
        text: str,
        *,
        known: KnownValues | None = None,
        operator: str | None = None,
    ) -> MaskResult:
        """Return ``text`` with every detected identifier replaced.

        Args:
            text: input text (Arabic, English or mixed).
            known: values you already know (see :meth:`analyze`).
            operator: override the default operator for this call.
        """
        entities = self.analyze(text, known=known)
        replace = Replacer(operator or self._operator, self._operators, self._hash_key)
        parts: list[str] = []
        last = 0
        for e in entities:
            parts.append(text[last : e.start])
            parts.append(replace(e.type, text[e.start : e.end]))
            last = e.end
        parts.append(text[last:])
        return MaskResult(text="".join(parts), entities=entities)

    def mask_batch(
        self,
        texts: Iterable[str],
        *,
        operator: str | None = None,
    ) -> list[MaskResult]:
        """Mask many texts. Tag numbers restart for every text."""
        return [self.mask(t, operator=operator) for t in texts]
