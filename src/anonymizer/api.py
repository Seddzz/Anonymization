"""FastAPI service exposing detection, anonymization, and restoration."""
import os
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from anonymizer.anonymize import anonymize_text
from anonymizer.detect import Entity
from anonymizer.detectors import ALL_CHECKSUM_DETECTORS, ALL_REGEX_DETECTORS, NerDetector
from anonymizer.engine import DetectionEngine
from anonymizer.restore import restore_text
from anonymizer.store import MappingStore


def _cors_origins() -> list[str]:
    raw = os.getenv("ANONYMIZER_CORS_ORIGINS", "http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app = FastAPI(title="Anonymizer API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = DetectionEngine()
store = MappingStore()

_ner_detector: NerDetector | None = None
_ner_engine: DetectionEngine | None = None


def _engine_for(use_ner: bool) -> DetectionEngine:
    """Return a cached engine, lazily building the NER one on first use."""
    global _ner_detector, _ner_engine
    if not use_ner:
        return engine
    if _ner_engine is None:
        _ner_detector = NerDetector()
        _ner_engine = DetectionEngine(
            [*ALL_REGEX_DETECTORS, *ALL_CHECKSUM_DETECTORS, _ner_detector]
        )
    return _ner_engine


class DetectRequest(BaseModel):
    text: str
    ner: bool = False


class EntityOut(BaseModel):
    label: str
    start: int
    end: int
    text: str
    score: float
    source: str


class DetectResponse(BaseModel):
    entities: list[EntityOut]


class AnonymizeRequest(BaseModel):
    text: str
    strategy: Literal["placeholder", "fake"] = "placeholder"
    ner: bool = False


class AnonymizeResponse(BaseModel):
    redacted: str
    mapping_id: str
    entities: list[EntityOut]


class RestoreRequest(BaseModel):
    mapping_id: str
    redacted: str


class RestoreResponse(BaseModel):
    text: str


class HealthResponse(BaseModel):
    status: str


def _to_out(entity: Entity) -> EntityOut:
    return EntityOut(
        label=entity.label,
        start=entity.start,
        end=entity.end,
        text=entity.text,
        score=entity.score,
        source=entity.source,
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/detect", response_model=DetectResponse)
def detect(request: DetectRequest) -> DetectResponse:
    entities = _engine_for(request.ner).detect_all(request.text)
    return DetectResponse(entities=[_to_out(entity) for entity in entities])


@app.post("/anonymize", response_model=AnonymizeResponse)
def anonymize(request: AnonymizeRequest) -> AnonymizeResponse:
    entities = _engine_for(request.ner).detect_all(request.text)
    redacted, mapping = anonymize_text(request.text, entities, strategy=request.strategy)
    mapping_id = store.save(mapping)
    return AnonymizeResponse(
        redacted=redacted,
        mapping_id=mapping_id,
        entities=[_to_out(entity) for entity in entities],
    )


@app.post("/restore", response_model=RestoreResponse)
def restore(request: RestoreRequest) -> RestoreResponse:
    mapping = store.get(request.mapping_id)
    if mapping is None:
        raise HTTPException(status_code=404, detail="mapping not found or expired")
    return RestoreResponse(text=restore_text(request.redacted, mapping))
