"""Catalog of the identifier types Cloakix can detect."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntityInfo:
    name: str
    description: str
    masked_by_default: bool = True


ENTITIES: dict[str, EntityInfo] = {
    e.name: e
    for e in [
        EntityInfo("PERSON", "Person name: patient, relative, doctor, staff"),
        EntityInfo("PHONE", "Mobile or landline number (GCC, Egypt, international)"),
        EntityInfo("EMAIL", "Email address"),
        EntityInfo("NATIONAL_ID", "National ID / Iqama / Emirates ID / QID / Civil ID / CPR"),
        EntityInfo("PASSPORT", "Passport number"),
        EntityInfo("MRN", "Medical record number / hospital file number"),
        EntityInfo("INSURANCE_NUMBER", "Insurance card, policy or member number"),
        EntityInfo("REFERENCE_NUMBER", "Appointment, booking, invoice, claim or ticket number"),
        EntityInfo("ID_NUMBER", "Any other long number (catch-all safety net)"),
        EntityInfo("CREDIT_CARD", "Payment card number (Luhn-validated)"),
        EntityInfo("IBAN", "International bank account number (mod-97 validated)"),
        EntityInfo("BANK_ACCOUNT", "Bank account number (context-based)"),
        EntityInfo("IP_ADDRESS", "IPv4 or IPv6 address"),
        EntityInfo("URL", "Web address"),
        EntityInfo("SOCIAL_HANDLE", "Social media handle such as @username"),
        EntityInfo("DATE", "Calendar date (Gregorian or Hijri)"),
        EntityInfo("ADDRESS", "Postal address details such as P.O. Box"),
        EntityInfo("LOCATION", "City, district or place name (NER model)"),
        EntityInfo(
            "ORGANIZATION",
            "Organization or hospital name (NER model); kept by default",
            masked_by_default=False,
        ),
    ]
}

DEFAULT_MASKED: frozenset[str] = frozenset(
    name for name, info in ENTITIES.items() if info.masked_by_default
)
