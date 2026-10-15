# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
uses [Semantic Versioning](https://semver.org/).

## [0.1.2] - 2026-10-15

### Security
- Hostile inputs such as `1-1-1-…` or `a/a/a/…` (20,000 characters) took 5–7 s because of
  quadratic regex backtracking; they now take about 0.1 s. Overlap resolution is also
  O(n log n), so texts with thousands of identifiers stay fast.
- API validation errors (HTTP 422) no longer echo the submitted text, which could contain
  personal data.
- API `known` values are limited (200 values, 200 characters each, real identifier types
  only); known values are matched in one pass per type.
- Loading a model no longer starts a background download of an unmerged, auto-converted
  weights file from the Hugging Face Hub; only the pinned revision is downloaded.
- A non-ASCII `X-API-Key` header now returns 401 instead of a server error.
- Words longer than 64 characters (URLs, long IDs, hostile input) are no longer sent to the
  NER models, which took ~10 s for a 20,000-character run; the rules still check them.
- Batch requests are limited to 100,000 characters in total (`CLOAKIX_MAX_BATCH_CHARS`).

### Added
- `licenses/` folder with the full license texts of the two NER models; the Docker image,
  which includes the models, now ships these texts.

## [0.1.1] - 2026-10-14

### Added
- City gazetteer for the GCC and Egypt (Arabic and English spellings, attached Arabic prefixes
  such as `بجدة` / `للرياض`), so cities the NER model misses are still masked as `LOCATION`.
- Emirates IDs written in the dashed format are masked even when the check digit is mistyped.

### Fixed
- NER false positives: labels and common words such as `Iqama`, `ER`, `Emirates`, `الملك` or
  `مستشفى` are no longer masked on their own. The ID or name next to them still is.
- Hijri dates: the tatweel in `هـ` is now masked with the date instead of being left behind.
- Hijri years (13xx/14xx) next to a keyword are no longer taken as reference numbers.

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
