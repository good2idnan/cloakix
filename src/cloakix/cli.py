"""Command line interface.

Commands: ``cloakix mask``, ``cloakix serve``, ``cloakix download-models``, ``cloakix entities``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from cloakix import __version__
from cloakix.entities import ENTITIES
from cloakix.operators import OPERATORS


def _utf8_stdout() -> None:
    # Windows consoles default to a legacy code page that cannot print Arabic.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


def _cmd_mask(args: argparse.Namespace) -> int:
    from cloakix.masker import Masker

    text = args.text if args.text is not None else sys.stdin.read()
    masker = Masker(
        languages=_split(args.languages),
        regions=_split(args.regions),
        domains=_split(args.domains),
        ner=False if args.no_ner else None,
        operator=args.operator,
    )
    result = masker.mask(text)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(result.text)
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print('The API needs extra packages: pip install "cloakix[api]"', file=sys.stderr)
        return 1
    uvicorn.run("cloakix.api.app:app", host=args.host, port=args.port, workers=args.workers)
    return 0


def _cmd_download(args: argparse.Namespace) -> int:
    from cloakix.languages import LANGUAGES
    from cloakix.ner.transformers_ner import TransformersNerRecognizer

    for code in _split(args.languages):
        spec = LANGUAGES[code].ner_model
        if spec is None:
            continue
        print(f"Downloading {spec.model_id} (~{spec.size_mb} MB) ...")
        TransformersNerRecognizer(spec).load()
    print("Models are cached. Set HF_HUB_OFFLINE=1 to run without internet.")
    return 0


def _cmd_entities(_: argparse.Namespace) -> int:
    for e in ENTITIES.values():
        default = "masked" if e.masked_by_default else "kept"
        print(f"{e.name:<18} {default:<7} {e.description}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cloakix", description="Detect and mask personal identifiers in Arabic and English."
    )
    parser.add_argument("--version", action="version", version=f"cloakix {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("mask", help="mask text given as argument or on stdin")
    p.add_argument("text", nargs="?", help="text to mask (reads stdin when omitted)")
    p.add_argument("--languages", default="ar,en")
    p.add_argument("--regions", default="gcc,eg")
    p.add_argument("--domains", default="healthcare")
    p.add_argument("--operator", default="tag", choices=[o for o in OPERATORS if o != "hash"])
    p.add_argument("--no-ner", action="store_true", help="rules only, no NER models")
    p.add_argument("--json", action="store_true", help="print masked text and entities as JSON")
    p.set_defaults(func=_cmd_mask)

    p = sub.add_parser("serve", help="run the REST API")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--workers", type=int, default=1)
    p.set_defaults(func=_cmd_serve)

    p = sub.add_parser("download-models", help="download NER models for offline use")
    p.add_argument("--languages", default="ar,en")
    p.set_defaults(func=_cmd_download)

    p = sub.add_parser("entities", help="list supported identifier types")
    p.set_defaults(func=_cmd_entities)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _utf8_stdout()
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
