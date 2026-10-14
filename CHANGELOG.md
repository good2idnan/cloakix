# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- README rewritten for general use (support, banking, government, HR, healthcare) with a
  recorded GIF demo, an "Under the hood" section and performance numbers.
- Usage, API and identifier details moved to `docs/usage.md`, `docs/api.md` and `docs/entities.md`.

## [0.1.0] - 2026-10-13

### Added
- `Masker` with `mask()`, `analyze()` and `mask_batch()` for Arabic, English and mixed text.
- Text normalization: Arabic-Indic/Persian digits, hidden Unicode characters, diacritics,
  with offsets mapped back to the original text.
- Region packs for Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman and Egypt:
  phone numbers and national IDs (with check-digit or structure validation).
- Healthcare domain pack: MRN and insurance numbers detected from context words.
- General recognizers: email, URL, IP, payment card (Luhn), IBAN (mod-97), passport,
  bank account, reference numbers, P.O. Box, social handles, Gregorian and Hijri dates,
  and a catch-all for long numbers.
- Rule-based name detection after titles and introductions (Arabic and English).
- Optional NER models (CAMeLBERT-Mix NER for Arabic, BERT-base NER for English),
  pinned to exact revisions.
- Known-values masking (pass a patient's name/MRN from your database).
- Operators: `tag`, `type`, `redact`, `mask`, `hash` (HMAC-SHA256).
- REST API (`/v1/mask`, `/v1/mask/batch`, `/v1/analyze`, `/v1/entities`, `/health`)
  with optional API key, CLI and Dockerfile.
