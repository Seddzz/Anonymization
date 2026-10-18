"""FastAPI service exposing detection, anonymization, and restoration."""
import os
import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel

from anonymizer.anonymize import anonymize_text
from anonymizer.detect import Entity
from anonymizer.detectors import ALL_CHECKSUM_DETECTORS, ALL_REGEX_DETECTORS, NerDetector
from anonymizer.engine import DetectionEngine
from anonymizer.exceptions import ScannedDocumentError
from anonymizer.extract import extract_pdf
from anonymizer.pdf_output import redact_pdf
from anonymizer.restore import restore_text
from anonymizer.store import MappingStore

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_UPLOAD_SUFFIXES = (".txt", ".pdf")


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


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/detect", response_model=DetectResponse)
def detect(request: DetectRequest) -> DetectResponse:
    entities = _engine_for(request.ner).detect_all(request.text)
    return DetectResponse(entities=[_to_out(entity) for entity in entities])


def _read_upload(file: UploadFile) -> tuple[str, Path | None]:
    """Extract .txt content or the PDF text layer of an uploaded document.

    Returns the document text plus the temp path for PDFs (needed for PDF
    output; callers must unlink it).
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _UPLOAD_SUFFIXES:
        raise HTTPException(
            status_code=400, detail="Unsupported file type: upload a .txt or .pdf file."
        )
    data = file.file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB upload limit.")
    if suffix == ".pdf":
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            handle.write(data)
            temp_path = Path(handle.name)
        try:
            pages = extract_pdf(temp_path)
        except ScannedDocumentError as exc:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise
        return "".join(page.text for page in pages), temp_path
    try:
        return data.decode("utf-8"), None
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text.") from exc


@app.post("/detect-file", response_model=DetectResponse)
def detect_file(
    file: Annotated[UploadFile, File()],
    ner: bool = False,
) -> DetectResponse:
    """Detect entities in an uploaded .txt or .pdf document."""
    text, temp_path = _read_upload(file)
    try:
        entities = _engine_for(ner).detect_all(text)
        return DetectResponse(entities=[_to_out(entity) for entity in entities])
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


@app.post("/anonymize-file")
def anonymize_file(
    file: Annotated[UploadFile, File()],
    strategy: Literal["placeholder", "fake"] = "placeholder",
    ner: bool = False,
    output: Literal["text", "pdf"] = "text",
) -> Response:
    """Anonymize an uploaded .txt or .pdf document.

    ``output=text`` (default) returns the usual JSON with ``redacted``,
    ``mapping_id`` and ``entities``. ``output=pdf`` streams a redacted PDF with
    the PII boxed out in place; the mapping id is carried in ``X-Mapping-Id``.
    """
    text, temp_path = _read_upload(file)
    try:
        entities = _engine_for(ner).detect_all(text)
        if output == "pdf":
            if temp_path is None:
                raise HTTPException(
                    status_code=400, detail="PDF output requires a PDF upload."
                )
            result = redact_pdf(temp_path, entities, strategy=strategy)
            mapping_id = store.save(result.mapping)
            return Response(
                content=result.pdf_bytes,
                media_type="application/pdf",
                headers={
                    "X-Mapping-Id": mapping_id,
                    "X-Redacted-Entities": str(result.applied),
                    "X-Missed-Entities": str(result.missed),
                },
            )

        redacted, mapping = anonymize_text(text, entities, strategy=strategy)
        mapping_id = store.save(mapping)
        return AnonymizeResponse(
            redacted=redacted,
            mapping_id=mapping_id,
            entities=[_to_out(entity) for entity in entities],
        )
    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


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
