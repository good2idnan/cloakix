# Supported identifiers

| Type | Examples | Detected by |
|---|---|---|
| `PERSON` | `خالد الحربي`, `Sara Al-Qahtani` | Title rules (`الدكتور`, `Dr.`, `اسمي`…) and NER models |
| `PHONE` | `0551234567`, `+971 50 123 4567`, `01012345678`, `٠٥٥١٢٣٤٥٦٧` | Country formats: SA, AE, QA, KW, BH, OM, EG |
| `NATIONAL_ID` | Saudi ID / Iqama, Emirates ID, Qatar QID, Kuwait Civil ID, Bahrain CPR, Oman Civil No., Egyptian National ID | Format + check digit or birth-date rules + context words |
| `MRN` | `رقم الملف 778812`, `MRN: A-55821` | Context words (any format) |
| `INSURANCE_NUMBER` | `رقم التأمين 55-12345678` | Context words |
| `REFERENCE_NUMBER` | appointment, booking, invoice, claim numbers | Context words |
| `CREDIT_CARD` | `4111 1111 1111 1111` | Luhn check |
| `IBAN` | `SA…`, `AE…`, `EG…`, grouped or compact | mod-97 check + country length |
| `PASSPORT` | `A12345678` near `passport` / `جواز` | Pattern + context |
| `BANK_ACCOUNT` | number near `account` / `رقم الحساب` | Pattern + context |
| `EMAIL`, `URL`, `IP_ADDRESS`, `SOCIAL_HANDLE` | `a@b.com`, `https://…`, `10.0.0.1`, `@user` | Patterns + validation |
| `DATE` | `12/03/2026`, `5 مارس 2026`, `3 رمضان 1447 هـ` | Gregorian and Hijri patterns |
| `ADDRESS` | `ص.ب 12345`, `P.O. Box 1234`, postal codes near a keyword | Patterns + context |
| `LOCATION` | `الرياض`, `Dubai` | NER models |
| `ORGANIZATION` | hospital or company names | NER models, **kept by default** |
| `ID_NUMBER` | any other number with 6+ digits | Safety net (`catch_all_numbers`) |

## Validation rules

| Identifier | Rule |
|---|---|
| Saudi National ID / Iqama | 10 digits, starts with 1 (citizen) or 2 (resident), Luhn |
| Emirates ID | `784-YYYY-NNNNNNN-C`, Luhn |
| Egyptian National ID | 14 digits: century + valid birth date + governorate code (check digit not public) |
| Kuwait Civil ID | 12 digits: century + valid birth date |
| Qatar QID, Bahrain CPR, Oman Civil No. | No public check digit: detected next to a context word |
| Payment card | 13–19 digits, Luhn |
| IBAN | ISO 13616 length per country, mod-97 |
