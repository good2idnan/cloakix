# How Cloakix works

Cloakix is **not just regex**. It combines four detection methods, because each one
catches a different kind of identifier.

```
text
 │
 ├─ 1. Normalize      ٠٥٥١٢٣ → 055123, remove hidden characters and diacritics
 │                    (keeps a map back to the original character positions)
 │
 ├─ 2. Detect         a. Rules + validators   phones, IDs, cards, IBAN, email, dates
 │                    b. Context words        MRN, insurance, QID… ("رقم الملف 778812")
 │                    c. Name rules           after titles: "الدكتور خالد", "Dr. Sara"
 │                    d. NER models           names and places anywhere (optional)
 │                    e. Known values         values you pass in (patient name, MRN)
 │
 ├─ 3. Merge          resolve overlaps: highest score → type priority → longer span
 │
 └─ 4. Replace        <PERSON_1>, <PHONE_1> … (or type / redact / mask / hash)
```

## 1. Normalization

Detection runs on a normalized copy of the text:

| Input | Becomes | Why |
|---|---|---|
| `٠٥٥١٢٣٤٥٦٧` (Arabic-Indic), `۰۳۰۰` (Persian) | `0551234567`, `0300` | Rules only need ASCII digits |
| zero-width / bidi control characters | removed | They can hide inside numbers |
| tatweel `ـ`, diacritics `ـَـُـِ` | removed | `مُحَمَّـــد` = `محمد` |
| Arabic presentation forms | regular letters | NFKC normalization |

Every normalized character remembers its original position, so masking is applied to the
**original** text and the output keeps the user's formatting.

Context words and titles are matched on a *folded* view: lower-case, and `أ/إ/آ → ا`,
`ى → ي`, `ة → ه`. Arabic keywords match as substrings, so attached prefixes and suffixes
still work: `ورقم ملفي` contains `رقم` and `ملف`.

## 2. Scoring

Every detection gets a score between 0 and 1. It is masked when the score reaches the
threshold (`score_threshold=0.5` by default).

| Evidence | Effect on score |
|---|---|
| Pattern match | base score, e.g. 0.3 for "10 digits starting with 1 or 2" |
| Validator passes (Luhn, mod-97, valid birth date…) | raised, e.g. to 0.85 |
| Validator fails | dropped |
| Context word nearby (`جوال`, `MRN`, `هوية`…) | + 0.35 to 0.6 |

Examples:

| Text | Result |
|---|---|
| `جوالي 0551234567` | Saudi mobile format (0.75) + context (+0.35) → **PHONE 1.0** |
| `رقم الملف 778812` | ID token (0.15) + MRN context (+0.6) → **MRN 0.75** |
| `55123456` alone | 8-digit local format (0.45) → not a phone, but caught by the long-number safety net → **ID_NUMBER 0.5** |
| `appointment in 2026` | plain years are never IDs → nothing |

## 3. Names

- **Rules (always on):** a name that follows a title or introduction is detected without any
  model: `الدكتور`, `الممرضة`, `ابني`, `اسمي`, `Dr.`, `Mrs.`, `my name is` … A stop-word list
  avoids false hits such as `الدكتور كان ممتاز` ("the doctor was excellent").
- **NER models (optional):** find names and places anywhere, even without a title.
  - Arabic: [CAMeL-Lab/bert-base-arabic-camelbert-mix-ner](https://huggingface.co/CAMeL-Lab/bert-base-arabic-camelbert-mix-ner)
    (Apache-2.0, ~436 MB). It was trained on Arabic news text (ANERcorp), so accuracy on informal
    dialect may be lower.
  - English: [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER) (MIT, ~433 MB).

Mixed text is split into Arabic and Latin-script runs, and each model only sees its own
language.

## 4. Merging

Different recognizers may find overlapping spans (for example, the long-number safety net
and the MRN recognizer both match `778812`). Cloakix:

1. joins pieces of the same type that touch, or are separated only by a space
   (`خالد` + `الحربي` → one name);
2. keeps the best detection where spans overlap: higher score, then the type priority in
   `merge.py`, then the longer span.

## 5. Replacing

| Operator | Output | Notes |
|---|---|---|
| `tag` (default) | `<PERSON_1>` | The same value gets the same number within one text |
| `type` | `<PERSON>` | |
| `redact` | `[REDACTED]` | |
| `mask` | `******4567`, `a****@mail.com` | Keeps the last 4 characters of numbers |
| `hash` | `<PERSON_3f9a1c2b7d4e>` | HMAC-SHA256 with your secret key: the same value gives the same token across calls, which is useful for joining rows in a database |

## Privacy notes

- Results contain only the type, position and score, never the original value, so they are
  safe to log.
- Detection is recall-first: when in doubt, Cloakix masks. Expect some over-masking of long
  numbers, and test on your own data before relying on it.
