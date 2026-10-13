<div align="center">

# Cloakix

**Detect and mask personal identifiers in Arabic and English text.**<br>
Built for the Gulf and Egypt: healthcare, customer feedback and general text.

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](CHANGELOG.md)

</div>

---

Cloakix finds names, phone numbers, national IDs, medical record numbers and other identifiers,
and replaces them **before** text is sent to an LLM, stored in a database or shared.

```text
Input   الدكتور خالد الحربي كان ممتاز بس الانتظار طويل. My mobile 0551234567, file no 778812, email khalid.h@gmail.com
Output  الدكتور <PERSON_1> كان ممتاز بس الانتظار طويل. My mobile <PHONE_1>, file no <MRN_1>, email <EMAIL_1>
```

## Why Cloakix

- **Arabic first:** handles Arabic-Indic digits (`٠٥٥١٢٣`), hidden Unicode characters,
  diacritics, attached prefixes (`للدكتور`, `ورقم ملفي`) and mixed Arabic/English text.
- **Regional identifiers:** Saudi ID and Iqama, Emirates ID, Qatar QID, Kuwait Civil ID,
  Bahrain CPR, Oman Civil No., Egyptian National ID, plus GCC and Egyptian phone formats.
  Values are validated with check digits or birth-date rules where possible.
- **Healthcare-aware:** finds MRNs and insurance numbers from context words such as `MRN` or
  `رقم الملف`, because MRN formats differ from hospital to hospital.
- **More than regex:** combines rules, check digits, context words, title-based name rules and
  optional AI (NER) models.
- **Private by design:** runs on your own servers with no external calls, and results never
  contain the original values.
- **Extensible:** add a country, language or industry by adding a single file.

## Install

```bash
git clone https://github.com/good2idnan/cloakix.git
cd cloakix
pip install -e ".[ner,api]"
```

| Extra | Adds | Size |
|---|---|---|
| *(none)* | Rules, validators, operators. No third-party dependencies | tiny |
| `ner` | Arabic and English name/place models (PyTorch + Transformers) | ~870 MB of models, downloaded on first use |
| `api` | REST API (FastAPI + Uvicorn) | small |

## Quick start

```python
from cloakix import Masker

masker = Masker()  # Arabic + English, GCC + Egypt, healthcare

result = masker.mask("اسمي أحمد العتيبي، جوالي ٠٥٥١٢٣٤٥٦٧، رقم الملف 778812")
print(result.text)
# اسمي <PERSON_1>، جوالي <PHONE_1>، رقم الملف <MRN_1>

for e in result.entities:
    print(e.type, e.start, e.end, round(e.score, 2))
```

More examples, all produced by the code in [`examples/`](examples):

```text
شكرا للدكتورة نورة على الاهتمام، ورقم ملفي 4471029
→ شكرا للدكتورة <PERSON_1> على الاهتمام، ورقم ملفي <MRN_1>

زرت المستشفى مع أخي فهد السبيعي في الرياض والخدمة كانت سيئة
→ زرت المستشفى مع أخي <PERSON_1> في <LOCATION_1> والخدمة كانت سيئة

موبايلي 01012345678 والرقم القومي 29001010112345، محدش رد عليا
→ موبايلي <PHONE_1> والرقم القومي <NATIONAL_ID_1>، محدش رد عليا

Great care from Dr. Sara Al-Qahtani. Call me on +971 50 123 4567
→ Great care from Dr. <PERSON_1>. Call me on <PHONE_1>
```

### Mask values you already know

When a comment is linked to a patient record, pass their details. They are masked wherever
they appear, in any format:

```python
masker.mask(
    "سلمان يقول التعامل ممتاز، اتصلوا عليه 055 999 8877",
    known={"PERSON": ["سلمان الدوسري"], "PHONE": ["0559998877"]},
).text
# <PERSON_1> يقول التعامل ممتاز، اتصلوا عليه <PHONE_1>
```

### Choose how values are replaced

```python
Masker(operator="tag")                         # <PHONE_1>          (default)
Masker(operator="type")                        # <PHONE>
Masker(operator="redact")                      # [REDACTED]
Masker(operator="mask")                        # ******4567
Masker(operator="hash", hash_key="secret")     # <PHONE_a005edc353e6>  same value, same token
Masker(operators={"EMAIL": "mask"})            # per-type override
Masker(keep=["LOCATION", "DATE"])              # leave some types unmasked
```

## REST API

```bash
cloakix serve --port 8000          # or: docker build -t cloakix . && docker run -p 8000:8000 cloakix
```

```http
POST /v1/mask
Content-Type: application/json

{"text": "اسمي أحمد، جوالي 0551234567"}
```

```json
{
  "masked_text": "اسمي <PERSON_1>، جوالي <PHONE_1>",
  "entities": [
    {"type": "PERSON", "start": 5,  "end": 9,  "score": 0.9719, "recognizer": "ner_ar"},
    {"type": "PHONE",  "start": 17, "end": 27, "score": 1.0, "recognizer": "phone_sa"}
  ]
}
```

| Endpoint | Purpose |
|---|---|
| `POST /v1/mask` | Mask one text (`text`, optional `operator`, optional `known`) |
| `POST /v1/mask/batch` | Mask up to 100 texts |
| `POST /v1/analyze` | Find identifiers without changing the text |
| `GET /v1/entities` | List supported identifier types |
| `GET /health` | Health check |

Interactive docs are served at `/docs`. Configure the server with environment variables:
`CLOAKIX_LANGUAGES`, `CLOAKIX_REGIONS`, `CLOAKIX_DOMAINS`, `CLOAKIX_NER`, `CLOAKIX_OPERATOR`,
`CLOAKIX_API_KEY` (requires an `X-API-Key` header), `CLOAKIX_MAX_TEXT_LENGTH`.
Request texts are never logged.

## Command line

```bash
cloakix mask "Dr. Sara called from +971 50 123 4567"
cloakix mask --json < comment.txt
cloakix entities
cloakix download-models        # pre-download models for offline servers
```

## What it detects

| Type | Examples | How |
|---|---|---|
| `PERSON` | `خالد الحربي`, `Sara Al-Qahtani` | Title rules + NER model |
| `PHONE` | `0551234567`, `+971 50 123 4567`, `01012345678`, `٠٥٥…` | Country formats (SA, AE, QA, KW, BH, OM, EG) |
| `NATIONAL_ID` | Saudi ID/Iqama, Emirates ID, QID, Civil ID, CPR, Egyptian NID | Format + check digit / birth date + context |
| `MRN` | `رقم الملف 778812`, `MRN: A-55821` | Context words |
| `INSURANCE_NUMBER` | `رقم التأمين 55-12345678` | Context words |
| `REFERENCE_NUMBER` | appointment, booking, invoice, claim numbers | Context words |
| `CREDIT_CARD` | `4111 1111 1111 1111` | Luhn check |
| `IBAN` | `SA.. ....`, `AE..`, `EG..` | mod-97 check |
| `EMAIL`, `URL`, `IP_ADDRESS`, `SOCIAL_HANDLE` | `a@b.com`, `@user` | Patterns |
| `DATE` | `12/03/2026`, `5 مارس 2026`, `3 رمضان 1447 هـ` | Gregorian + Hijri patterns |
| `PASSPORT`, `BANK_ACCOUNT`, `ADDRESS` (P.O. Box) | | Patterns + context |
| `LOCATION` | `الرياض`, `Dubai` | NER model |
| `ORGANIZATION` | hospital or company names | NER model, **kept by default** |
| `ID_NUMBER` | any other number with 6+ digits | Safety net |

## How it works

```
Normalize ─► Detect (rules · check digits · context words · name rules · NER · known values)
          ─► Merge overlaps ─► Replace (<PERSON_1>, <PHONE_1> …)
```

Each detection gets a score from 0 to 1, built from its pattern, its validator and any nearby
context words. It is masked when the score reaches 0.5. Read
[docs/how-it-works.md](docs/how-it-works.md) for details.

## Models and offline use

| Language | Model | License | Size |
|---|---|---|---|
| Arabic | [CAMeL-Lab/bert-base-arabic-camelbert-mix-ner](https://huggingface.co/CAMeL-Lab/bert-base-arabic-camelbert-mix-ner) | Apache-2.0 | ~436 MB |
| English | [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER) | MIT | ~433 MB |

- Models are **not** stored in this repository. They are downloaded from the Hugging Face Hub
  on first use, pinned to an exact commit, and cached in `~/.cache/huggingface`.
- For servers without internet, run `cloakix download-models` once (or use the Docker image,
  which includes them), then set `HF_HUB_OFFLINE=1`.
- On a laptop CPU, a typical comment takes about 25–150 ms. No GPU is needed.
- Without the `ner` extra, Cloakix runs on rules only. Names are then found only after titles
  (`الدكتور`, `Dr.`, `اسمي` …).

## Limitations

Cloakix reduces risk but **does not guarantee** that every identifier is found.

- **Test it on a sample of your own data** before relying on it, and add human review for
  public releases.
- The Arabic NER model was trained on formal news Arabic, so it may miss some names written
  in informal Gulf or Egyptian dialect.
- Qatar, Bahrain and Oman IDs have no public check digit. They are only detected next to a
  context word, or by the long-number safety net.
- The safety net masks **any** number with 6 or more digits (including amounts written without
  separators). Turn it off with `catch_all_numbers=False`.
- Masked text that can be linked back to a person (for example with `hash`) is
  *pseudonymized*, not anonymized, under GDPR, Saudi PDPL and similar laws.

## Roadmap

- [ ] Evaluation benchmark: precision and recall per identifier type on annotated Arabic and
      English text
- [ ] Fine-tuned Arabic NER for Gulf and Egyptian dialects
- [ ] Realistic fake replacements (surrogates)
- [ ] Reversible masking with an encrypted vault, for LLM round-trips
- [ ] More countries (Jordan, Iraq, Pakistan …) and languages (Urdu)
- [ ] Structured inputs (JSON, FHIR, HL7) and PDF/OCR
- [ ] PyPI release

## Contributing

Contributions are welcome, especially new countries, languages and identifier formats.
See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/extending.md](docs/extending.md).
Please **never include real personal data** in issues, tests or pull requests.

## Security

Report vulnerabilities and missed identifiers privately. See [SECURITY.md](SECURITY.md).

## License

[Apache License 2.0](LICENSE). The NER models are downloaded separately and keep their own
licenses (see [NOTICE](NOTICE)).

## Acknowledgements

- [CAMeL Lab, NYU Abu Dhabi](https://camel.abudhabi.nyu.edu/) for CAMeLBERT.
- [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER) for English NER.
- The recognizer → merge → operator design is inspired by
  [Microsoft Presidio](https://github.com/data-privacy-stack/presidio).
