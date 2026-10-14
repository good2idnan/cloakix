"""Text normalization that keeps a map back to the original character offsets.

Detection runs on the normalized text; masking is applied to the original text.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

# Arabic-Indic (٠-٩), Extended Arabic-Indic / Persian (۰-۹) and fullwidth digits -> ASCII.
_DIGITS: dict[int, str] = {}
for _i in range(10):
    _DIGITS[0x0660 + _i] = str(_i)
    _DIGITS[0x06F0 + _i] = str(_i)
    _DIGITS[0xFF10 + _i] = str(_i)

# Invisible characters that can hide inside identifiers.
_REMOVE: frozenset[int] = frozenset(
    [
        0x00AD,  # soft hyphen
        0x061C,  # Arabic letter mark
        0x0640,  # tatweel (kashida)
        0x200B,
        0x200C,
        0x200D,
        0x200E,
        0x200F,  # zero-width + LTR/RTL marks
        0x202A,
        0x202B,
        0x202C,
        0x202D,
        0x202E,  # bidi embeddings / overrides
        0x2060,
        0x2066,
        0x2067,
        0x2068,
        0x2069,  # word joiner + bidi isolates
        0xFEFF,  # zero-width no-break space / BOM
    ]
)


def _is_arabic_diacritic(cp: int) -> bool:
    return 0x064B <= cp <= 0x065F or cp == 0x0670


def _is_removed(ch: str) -> bool:
    cp = ord(ch)
    return cp in _REMOVE or _is_arabic_diacritic(cp)


@dataclass(frozen=True)
class NormalizedText:
    """Normalized text plus, for every normalized character, its index in the original."""

    original: str
    text: str
    index_map: tuple[int, ...]

    def to_original(self, start: int, end: int) -> tuple[int, int]:
        """Convert a ``[start, end)`` span in normalized text to the original text.

        Invisible characters right after the span (tatweel, diacritics, zero-width marks)
        are included, so masking ``هـ`` does not leave a stray ``ـ`` behind.
        """
        if not self.index_map or start >= end:
            return start, end
        orig_start, orig_end = self.index_map[start], self.index_map[end - 1] + 1
        while orig_end < len(self.original) and _is_removed(self.original[orig_end]):
            orig_end += 1
        return orig_start, orig_end


def normalize(text: str) -> NormalizedText:
    """Return a detection-friendly view of ``text``.

    - Arabic-Indic, Persian and fullwidth digits become ASCII digits.
    - Zero-width, bidi-control characters, tatweel and Arabic diacritics are removed.
    - Other non-ASCII characters get NFKC compatibility normalization
      (e.g. Arabic presentation forms become regular letters).
    """
    chars: list[str] = []
    index_map: list[int] = []
    for i, ch in enumerate(text):
        cp = ord(ch)
        if cp in _REMOVE or _is_arabic_diacritic(cp):
            continue
        mapped = _DIGITS.get(cp)
        if mapped is None:
            mapped = ch if cp < 0x80 else unicodedata.normalize("NFKC", ch)
        for out in mapped:
            chars.append(out)
            index_map.append(i)
    return NormalizedText(original=text, text="".join(chars), index_map=tuple(index_map))


_ARABIC_FOLD = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"})


def fold(text: str) -> str:
    """Case- and spelling-insensitive view for keyword matching.

    The result always has the same length as the input, so offsets stay valid.
    """
    out = []
    for ch in text:
        low = ch.lower()
        out.append(low if len(low) == 1 else ch)
    return "".join(out).translate(_ARABIC_FOLD)
