"""Combine detections from all recognizers into one non-overlapping list."""

from __future__ import annotations

from collections.abc import Iterable

from cloakix.recognizers.base import Detection

# When two different types overlap with the same score, the earlier type wins.
PRIORITY: list[str] = [
    "CREDIT_CARD",
    "IBAN",
    "NATIONAL_ID",
    "EMAIL",
    "URL",
    "IP_ADDRESS",
    "PHONE",
    "PASSPORT",
    "MRN",
    "INSURANCE_NUMBER",
    "REFERENCE_NUMBER",
    "BANK_ACCOUNT",
    "DATE",
    "ADDRESS",
    "SOCIAL_HANDLE",
    "PERSON",
    "LOCATION",
    "ORGANIZATION",
    "ID_NUMBER",
]
_RANK = {name: i for i, name in enumerate(PRIORITY)}

# Word-like types whose neighbouring pieces ("خالد" + "الحربي") form one entity.
_JOIN_ACROSS_SPACES = frozenset(["PERSON", "LOCATION", "ORGANIZATION", "ADDRESS"])


def _rank(entity_type: str) -> int:
    return _RANK.get(entity_type, len(PRIORITY))


def _merge_same_type(detections: list[Detection], text: str) -> list[Detection]:
    merged: list[Detection] = []
    for d in sorted(detections, key=lambda d: (d.type, d.start, -d.end)):
        if merged and merged[-1].type == d.type:
            last = merged[-1]
            gap = text[last.end : d.start] if d.start > last.end else ""
            touching = d.start <= last.end or (
                d.type in _JOIN_ACROSS_SPACES and len(gap) <= 2 and not gap.strip()
            )
            if touching:
                best = last if last.score >= d.score else d
                merged[-1] = Detection(
                    d.type,
                    last.start,
                    max(last.end, d.end),
                    max(last.score, d.score),
                    best.recognizer,
                )
                continue
        merged.append(d)
    return merged


def resolve(detections: Iterable[Detection], text: str) -> list[Detection]:
    """Merge same-type pieces, then keep the best detection wherever spans overlap.

    "Best" means highest score, then type priority (``PRIORITY``), then longer span.
    """
    candidates = _merge_same_type(list(detections), text)
    candidates.sort(key=lambda d: (-d.score, _rank(d.type), -(d.end - d.start), d.start))
    chosen: list[Detection] = []
    for d in candidates:
        if all(d.end <= c.start or d.start >= c.end for c in chosen):
            chosen.append(d)
    return sorted(chosen, key=lambda d: d.start)
