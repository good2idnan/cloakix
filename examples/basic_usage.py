"""Basic usage: mask one Arabic/English text and inspect what was found.

Run: python examples/basic_usage.py
"""

from cloakix import Masker

masker = Masker()  # Arabic + English, GCC + Egypt, healthcare; NER if installed

text = (
    "الدكتور خالد الحربي كان ممتاز بس الانتظار طويل. "
    "My mobile 0551234567, file no 778812, email khalid.h@gmail.com"
)

result = masker.mask(text)
print(result.text)

for entity in result.entities:
    print(f"{entity.type:<12} {text[entity.start : entity.end]!r:<24} score={entity.score:.2f}")
