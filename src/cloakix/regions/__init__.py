"""Region (country) packs. To add a country, create ``<code>.py`` with a ``PACK`` and register it.

Groups such as ``"gcc"`` expand to several countries.
"""

from __future__ import annotations

from collections.abc import Iterable

from cloakix.packs import RegionPack
from cloakix.regions import ae, bh, eg, kw, om, qa, sa

REGIONS: dict[str, RegionPack] = {
    p.code: p for p in [sa.PACK, ae.PACK, qa.PACK, kw.PACK, bh.PACK, om.PACK, eg.PACK]
}

REGION_GROUPS: dict[str, list[str]] = {
    "gcc": ["sa", "ae", "qa", "kw", "bh", "om"],
}


def resolve_regions(codes: Iterable[str]) -> list[RegionPack]:
    """Expand groups and return region packs in a stable order, without duplicates."""
    result: list[str] = []
    for code in codes:
        code = code.lower()
        expanded = REGION_GROUPS.get(code, [code])
        for c in expanded:
            if c not in REGIONS:
                known = sorted([*REGIONS, *REGION_GROUPS])
                raise ValueError(f"Unknown region {c!r}. Available: {', '.join(known)}")
            if c not in result:
                result.append(c)
    return [REGIONS[c] for c in result]


__all__ = ["REGIONS", "REGION_GROUPS", "resolve_regions"]
