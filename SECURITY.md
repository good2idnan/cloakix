# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security problems, and never include real
personal data in a report. Use GitHub's private vulnerability reporting
("Security" tab → "Report a vulnerability") with:

- a description of the problem and its impact;
- steps to reproduce, using fictitious data only;
- the Cloakix version.

We aim to reply within 5 working days.

## A missed identifier is a security issue

If Cloakix fails to mask an identifier format that it claims to support, report it privately
as above. Replace real values with fictitious ones that have the same format.

## Using Cloakix safely

- Cloakix reduces the risk of exposing identifiers. It does **not** guarantee that every
  identifier is found. For high-risk releases, add human review.
- Masked text that you can link back to a person (for example with the `hash` operator and
  its key) is **pseudonymized**, not anonymized, under GDPR, Saudi PDPL and similar laws.
- Run the API inside your own network, set `CLOAKIX_API_KEY`, and do not log request bodies.
- Keep `CLOAKIX_HASH_KEY` in a secrets manager; anyone with the key can link hashed tokens.
