"""REST API around ``Masker``. Run with ``cloakix serve`` or ``uvicorn cloakix.api.app:app``.

Configuration (environment variables):

==============================  ==========================================  ================
Variable                        Meaning                                     Default
==============================  ==========================================  ================
``CLOAKIX_LANGUAGES``           comma-separated language packs              ``ar,en``
``CLOAKIX_REGIONS``             comma-separated regions / groups            ``gcc,eg``
``CLOAKIX_DOMAINS``             comma-separated domains                     ``healthcare``
``CLOAKIX_NER``                 ``auto``, ``true`` or ``false``             ``auto``
``CLOAKIX_OPERATOR``            default operator                            ``tag``
``CLOAKIX_API_KEY``             if set, required in the ``X-API-Key`` header (none)
``CLOAKIX_MAX_TEXT_LENGTH``     maximum characters per text                 ``20000``
``CLOAKIX_MAX_BATCH_SIZE``      maximum texts per batch request             ``100``
``CLOAKIX_MAX_KNOWN_VALUES``    maximum known values per request            ``200``
``CLOAKIX_MAX_BATCH_CHARS``     maximum total characters per batch          ``100000``
==============================  ==========================================  ================

Request texts are never logged.
"""

# No ``from __future__ import annotations`` here: FastAPI must resolve the request models
# defined inside ``create_app`` at runtime.
import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Literal

try:
    from fastapi import Depends, FastAPI, Header, HTTPException, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field, field_validator
except ImportError as exc:  # pragma: no cover - depends on environment
    raise ImportError('The API needs extra packages: pip install "cloakix[api]"') from exc

from cloakix import __version__
from cloakix.entities import ENTITIES
from cloakix.masker import Masker

Operator = Literal["tag", "type", "redact", "mask"]


def _env_list(name: str, default: str) -> list[str]:
    return [v.strip() for v in os.environ.get(name, default).split(",") if v.strip()]


def masker_from_env() -> Masker:
    ner_setting = os.environ.get("CLOAKIX_NER", "auto").lower()
    ner = None if ner_setting == "auto" else ner_setting in ("1", "true", "yes")
    return Masker(
        languages=_env_list("CLOAKIX_LANGUAGES", "ar,en"),
        regions=_env_list("CLOAKIX_REGIONS", "gcc,eg"),
        domains=_env_list("CLOAKIX_DOMAINS", "healthcare"),
        ner=ner,
        operator=os.environ.get("CLOAKIX_OPERATOR", "tag"),
    )


class EntityOut(BaseModel):
    type: str = Field(examples=["PHONE"])
    start: int = Field(description="Start offset in the original text")
    end: int = Field(description="End offset (exclusive) in the original text")
    score: float = Field(ge=0, le=1)
    recognizer: str


class MaskResponse(BaseModel):
    masked_text: str
    entities: list[EntityOut]


class AnalyzeResponse(BaseModel):
    entities: list[EntityOut]


class BatchResponse(BaseModel):
    results: list[MaskResponse]


class EntityInfoOut(BaseModel):
    name: str
    description: str
    masked_by_default: bool


def create_app(masker: Masker | None = None) -> FastAPI:
    """Build the FastAPI app. Pass a ``Masker`` to override environment configuration."""
    max_len = int(os.environ.get("CLOAKIX_MAX_TEXT_LENGTH", "20000"))
    max_batch = int(os.environ.get("CLOAKIX_MAX_BATCH_SIZE", "100"))
    max_known = int(os.environ.get("CLOAKIX_MAX_KNOWN_VALUES", "200"))
    max_batch_chars = int(os.environ.get("CLOAKIX_MAX_BATCH_CHARS", "100000"))
    api_key = os.environ.get("CLOAKIX_API_KEY")

    KnownValue = Annotated[str, Field(min_length=1, max_length=200)]

    class KnownMixin(BaseModel):
        known: dict[str, list[KnownValue]] | None = Field(
            default=None,
            description='Values you already know, e.g. {"PERSON": ["Ahmed Ali"]}',
        )

        @field_validator("known")
        @classmethod
        def _limit_known(cls, value: dict[str, list[str]] | None) -> dict[str, list[str]] | None:
            if value is None:
                return value
            unknown = sorted({k.upper() for k in value} - set(ENTITIES))
            if unknown:
                raise ValueError(f"unknown identifier types: {', '.join(unknown)}")
            if sum(len(v) for v in value.values()) > max_known:
                raise ValueError(f"at most {max_known} known values per request")
            return value

    class MaskRequest(KnownMixin):
        text: str = Field(max_length=max_len, examples=["اسمي أحمد، جوالي 0551234567"])
        operator: Operator | None = Field(default=None, description="Override the default")

    class AnalyzeRequest(KnownMixin):
        text: str = Field(max_length=max_len)

    class BatchRequest(BaseModel):
        texts: list[Annotated[str, Field(max_length=max_len)]] = Field(max_length=max_batch)
        operator: Operator | None = None

        @field_validator("texts")
        @classmethod
        def _limit_total(cls, value: list[str]) -> list[str]:
            # The NER models cost roughly 1 s per 4,000 characters on a CPU; cap the batch
            # so one request cannot occupy the server for minutes.
            if sum(len(t) for t in value) > max_batch_chars:
                raise ValueError(f"at most {max_batch_chars} characters per batch")
            return value

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Load models once at startup, not on every request.
        app.state.masker = (masker or masker_from_env()).load()
        yield

    app = FastAPI(
        title="Cloakix API",
        version=__version__,
        description="Detect and mask personal identifiers in Arabic and English text.",
        lifespan=lifespan,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # FastAPI's default 422 body includes the submitted input, which may contain the very
        # personal data this service exists to protect. Return only where and why it failed.
        detail = [
            {"loc": list(e.get("loc", ())), "msg": e.get("msg", ""), "type": e.get("type", "")}
            for e in exc.errors()
        ]
        return JSONResponse(status_code=422, content={"detail": detail})

    def check_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
        # Compare bytes: compare_digest raises on non-ASCII str, which would surface as a 500.
        if api_key and not (
            x_api_key and secrets.compare_digest(x_api_key.encode("utf-8"), api_key.encode("utf-8"))
        ):
            raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")

    def get_masker(request: Request) -> Masker:
        masker_: Masker = request.app.state.masker
        return masker_

    secured = [Depends(check_key)]

    @app.get("/health", tags=["service"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/v1/entities", response_model=list[EntityInfoOut], tags=["service"])
    def entities() -> list[EntityInfoOut]:
        return [
            EntityInfoOut(
                name=e.name, description=e.description, masked_by_default=e.masked_by_default
            )
            for e in ENTITIES.values()
        ]

    @app.post("/v1/mask", response_model=MaskResponse, dependencies=secured, tags=["mask"])
    def mask(body: MaskRequest, m: Annotated[Masker, Depends(get_masker)]) -> MaskResponse:
        result = m.mask(body.text, known=body.known, operator=body.operator)
        return MaskResponse.model_validate(result.to_dict())

    @app.post("/v1/mask/batch", response_model=BatchResponse, dependencies=secured, tags=["mask"])
    def mask_batch(body: BatchRequest, m: Annotated[Masker, Depends(get_masker)]) -> BatchResponse:
        results = m.mask_batch(body.texts, operator=body.operator)
        return BatchResponse(results=[MaskResponse.model_validate(r.to_dict()) for r in results])

    @app.post("/v1/analyze", response_model=AnalyzeResponse, dependencies=secured, tags=["mask"])
    def analyze(body: AnalyzeRequest, m: Annotated[Masker, Depends(get_masker)]) -> AnalyzeResponse:
        found = m.analyze(body.text, known=body.known)
        return AnalyzeResponse(entities=[EntityOut(**e.to_dict()) for e in found])

    return app


app = create_app()
