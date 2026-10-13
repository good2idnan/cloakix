# REST API

## Run

```bash
docker build -t cloakix .
docker run -p 8000:8000 -e CLOAKIX_API_KEY=change-me cloakix
```

Or without Docker: `pip install -e ".[ner,api]"`, then `cloakix serve --host 0.0.0.0 --port 8000`.
Interactive docs are served at `http://localhost:8000/docs`.

## Endpoints

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/v1/mask` | `{"text", "operator"?, "known"?}` | `masked_text` + `entities` |
| `POST` | `/v1/mask/batch` | `{"texts": [...], "operator"?}` (≤ 100) | `results[]` |
| `POST` | `/v1/analyze` | `{"text", "known"?}` | `entities` only |
| `GET` | `/v1/entities` | | supported types |
| `GET` | `/health` | | `{"status": "ok"}` |

## Example

```http
POST /v1/mask
Content-Type: application/json
X-API-Key: change-me

{"text": "اسمي أحمد، جوالي 0551234567"}
```

```json
{
  "masked_text": "اسمي <PERSON_1>، جوالي <PHONE_1>",
  "entities": [
    {"type": "PERSON", "start": 5,  "end": 9,  "score": 0.9719, "recognizer": "ner_ar"},
    {"type": "PHONE",  "start": 17, "end": 27, "score": 1.0,    "recognizer": "phone_sa"}
  ]
}
```

`start`/`end` are character offsets into the text you sent. Original values are never returned
or logged.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `CLOAKIX_LANGUAGES` | `ar,en` | Language packs |
| `CLOAKIX_REGIONS` | `gcc,eg` | Regions |
| `CLOAKIX_DOMAINS` | `healthcare` | Domains |
| `CLOAKIX_NER` | `auto` | `auto`, `true` or `false` |
| `CLOAKIX_OPERATOR` | `tag` | Default operator |
| `CLOAKIX_API_KEY` | *(none)* | If set, required in the `X-API-Key` header |
| `CLOAKIX_MAX_TEXT_LENGTH` | `20000` | Maximum characters per text |
| `CLOAKIX_MAX_BATCH_SIZE` | `100` | Maximum texts per batch |

Run the API inside your own network. Put a TLS-terminating proxy in front of it if it is
reachable from other machines.
