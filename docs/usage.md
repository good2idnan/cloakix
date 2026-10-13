# Usage

## Install

```bash
git clone https://github.com/good2idnan/cloakix.git
cd cloakix
pip install -e ".[ner,api]"
```

| Extra | Adds |
|---|---|
| *(none)* | Rules, validators and operators. No third-party dependencies |
| `ner` | Arabic and English name/place models (PyTorch + Transformers, ~870 MB of models downloaded on first use) |
| `api` | REST API (FastAPI + Uvicorn) |

## Mask text

```python
from cloakix import Masker

masker = Masker()  # Arabic + English, GCC + Egypt, healthcare
result = masker.mask("اسمي أحمد العتيبي، جوالي ٠٥٥١٢٣٤٥٦٧، رقم الملف 778812")

result.text       # 'اسمي <PERSON_1>، جوالي <PHONE_1>، رقم الملف <MRN_1>'
result.entities   # [Entity(type='PERSON', start=5, end=17, score=0.99, recognizer='ner_ar'), ...]
```

- `masker.analyze(text)` returns the entities without changing the text.
- `masker.mask_batch(texts)` masks a list of texts.
- Entities hold only the type, position and score, never the original value, so they are safe
  to log.

## Mask values you already know

When a text is linked to a record, pass the values you know. They are masked wherever they
appear, in any format:

```python
masker.mask(
    "سلمان يقول التعامل ممتاز، اتصلوا عليه 055 999 8877",
    known={"PERSON": ["سلمان الدوسري"], "PHONE": ["0559998877"]},
).text
# '<PERSON_1> يقول التعامل ممتاز، اتصلوا عليه <PHONE_1>'
```

## Operators

```python
Masker(operator="tag")                       # <PHONE_1>   (default; same value -> same number)
Masker(operator="type")                      # <PHONE>
Masker(operator="redact")                    # [REDACTED]
Masker(operator="mask")                      # ******4567
Masker(operator="hash", hash_key="secret")   # <PHONE_a005edc353e6>  stable across calls
Masker(operators={"EMAIL": "mask"})          # per-type override
masker.mask(text, operator="redact")         # per-call override
```

Use `hash` when the same person must get the same token in different rows, for example
comments stored in a database. Keep the key secret (`CLOAKIX_HASH_KEY`): anyone who has it can
link tokens to values they already know.

## Options

| Option | Default | Meaning |
|---|---|---|
| `languages` | `("ar", "en")` | Language packs |
| `regions` | `("gcc", "eg")` | Countries or groups: `gcc`, `sa`, `ae`, `qa`, `kw`, `bh`, `om`, `eg` |
| `domains` | `("healthcare",)` | Industry packs |
| `ner` | `None` | `None` = use models if installed, `False` = rules only, `True` = require models |
| `entities` | all but `ORGANIZATION` | Types to mask |
| `keep` | `()` | Types to leave unmasked, e.g. `["LOCATION", "DATE"]` |
| `operator` / `operators` | `"tag"` / `{}` | Replacement style (see above) |
| `score_threshold` | `0.5` | Minimum confidence to mask |
| `catch_all_numbers` | `True` | Mask any other number with 6+ digits as `ID_NUMBER` |
| `device` | CPU | Torch device for the models (`0` or `"cuda"` for GPU) |

## Command line

```bash
cloakix mask "Dr. Sara called from +971 50 123 4567"
cloakix mask --json < comment.txt
cloakix mask --no-ner --operator redact "..."
cloakix entities
cloakix download-models
cloakix serve --port 8000
```

## Models and offline use

| Language | Model | License | Size |
|---|---|---|---|
| Arabic | [CAMeL-Lab/bert-base-arabic-camelbert-mix-ner](https://huggingface.co/CAMeL-Lab/bert-base-arabic-camelbert-mix-ner) | Apache-2.0 | ~436 MB |
| English | [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER) | MIT | ~433 MB |

- Models are pinned to an exact commit, downloaded on first use and cached in
  `~/.cache/huggingface`.
- For servers without internet, run `cloakix download-models` once (or use the Docker image),
  then set `HF_HUB_OFFLINE=1`.
- Without models, names are found only after titles and introductions (`الدكتور`, `Dr.`,
  `اسمي` …).
