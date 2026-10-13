# Contributing to Cloakix

Thanks for helping! Contributions of new countries, languages and identifier formats are
especially welcome.

## Development setup

```bash
git clone <your-fork-url> cloakix
cd cloakix
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"          # add ,ner to work on the NER models
```

## Before you open a pull request

```bash
ruff check .
ruff format .
mypy
pytest                 # fast rule-based tests
pytest -m ner          # model tests (downloads ~870 MB the first time)
```

## Rules

1. **Never commit real personal data.** Tests and examples must use fictitious values.
   Generate valid check digits with the helpers in `tests/conftest.py`.
2. Every new recognizer needs tests for what it **should** find and what it **should not**
   find (false positives).
3. Keep the core (`src/cloakix/*.py`, `recognizers/`) free of third-party dependencies.
   Heavy dependencies belong in optional extras.
4. Explain the source of any ID format or checksum rule in the code comment.

## Adding a country, language or domain

See [docs/extending.md](docs/extending.md). In short: add one file under `regions/`,
`languages/` or `domains/`, register it in that package's `__init__.py`, and add tests.

## Commit messages

Use short, imperative messages, e.g. `Add Jordan national ID recognizer`.
