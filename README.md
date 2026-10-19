<p align="center">
  <img src="docs/assets/github.jpg" alt="Nemo" width="600" />
</p>

<p align="center">
  <em>API-first PII anonymization for English documents. Runs locally, one-way redaction, usable from REST or CLI.</em>
</p>

---

## What you get

- **REST API** — FastAPI service with `/detect`, `/anonymize`, `/health` and an interactive Swagger UI at `http://localhost:8000/docs`.
- **`anon` CLI** — detect and anonymize `.txt` / `.pdf` files straight from your terminal.
- **File workflow** — redact a document to a clean file, then use that file anywhere: paste it into a chat, load it in any agent, share it onward. PII never reaches a model.
- **Stable redaction** — PII becomes numbered placeholders (`[PERSON_1]`, `[IBAN_1]`) or realistic fakes. Redaction is one-way: redacted text is the only artifact, no mapping is kept or written.
- **Local-first privacy** — detection runs on your machine; no request ever leaves your infrastructure.
- **Docs site** — the `web/` folder ships a Next.js docs site with a RAG assistant (deployable on Vercel); the engine and your data stay on your machine.

## Requirements

- **Python 3.11+** (native install) or **Docker Desktop** (containerized install)
- ~600 MB disk for dependencies, plus ~250 MB if you enable the NER model
- No GPU required — everything runs on CPU

---

## 1. Install

### Option A — Docker (no Python needed)

```bash
git clone https://github.com/Seddzz/Nemo.git
cd Nemo
docker compose up --build
```

This starts the FastAPI engine on `:8000` (the docs site in `web/` runs separately — see below).

### Option B — pip (into a virtualenv)

```bash
git clone https://github.com/Seddzz/Nemo.git
cd Nemo
python -m venv .venv
.venv\Scripts\activate              # Windows (use `source .venv/bin/activate` on Linux/macOS)
pip install -e ".[dev]" \
  --index-url https://download.pytorch.org/whl/cpu \
  --extra-index-url https://pypi.org/simple
```

The `--index-url` pins the **CPU-only PyTorch wheel** (~200 MB instead of a multi-GB CUDA build). Drop the flags if you have a GPU and want CUDA.

### Option C — uv

```bash
git clone https://github.com/Seddzz/Nemo.git
cd Nemo
uv pip install -e ".[dev]"
```

---

## 2. Start the engine

```bash
.venv\Scripts\uvicorn anonymizer.api:app --reload --port 8000
```

Verify it is alive:

- Swagger UI: **http://localhost:8000/docs**
- Health check: `curl http://localhost:8000/health` → `{"status":"ok"}`

---

## 3. Use it

### REST API

Detect entities (regex + checksum only, fast):

```bash
curl -X POST http://localhost:8000/detect \
  -H "Content-Type: application/json" \
  -d '{"text": "Sarah Kellermann transferred EUR 4200 to IBAN DE89 3704 0044 0532 0130 00", "ner": false}'
```

Anonymize — get redacted text plus the detected entities:

```bash
curl -X POST http://localhost:8000/anonymize \
  -H "Content-Type: application/json" \
  -d '{"text": "Sarah Kellermann transferred €4,200 to DE89 3704 0044 0532 0130 00", "strategy": "placeholder", "ner": true}'
```

```json
{
  "redacted": "[PERSON_1] transferred [AMOUNT_1] to [IBAN_1]",
  "entities": [...]
}
```

Nothing is stored or kept server-side — redaction is one-way.

### Anonymize a PDF

The engine extracts the PDF text layer server-side (PyMuPDF) — upload the file directly:

```bash
curl -X POST http://localhost:8000/anonymize-file \
  -F "file=@invoice.pdf" \
  -F "strategy=placeholder"
```

```json
{
  "redacted": "[PERSON_1] transferred [AMOUNT_1] to [IBAN_1] ...",
  "entities": [...]
}
```

- `/detect-file` works identically for detection only. Plain `.txt` uploads are accepted too, up to **10 MB**.
- Scanned PDFs without a text layer return `422` — run OCR before sending them.

**Get a redacted PDF back** (PII boxed out in place, layout preserved) with `-F "output=pdf"`:

```bash
curl -X POST http://localhost:8000/anonymize-file \
  -F "file=@invoice.pdf" \
  -F "strategy=placeholder" \
  -F "output=pdf" \
  -o invoice_redacted.pdf
```

Every detected value is replaced by a drawn token (`[EMAIL_1]`, `[IBAN_1]`, …) over the exact spot the original occupied — the PII is removed from the content stream, so copy/paste cannot recover it. The response carries `X-Redacted-Entities` and `X-Missed-Entities` (a rare entity split across a page break or in a decorative font may be skipped — check this header before trusting an anonymized document).

Prefer no curl? Run the CLI inside the container against a mounted folder:

```bash
docker compose run --rm -v "${PWD}:/data" api anon anonymize /data/invoice.pdf --strategy placeholder -o /data/invoice_redacted.txt
```

The redacted file lands back in your current folder with no extras to manage.

## CLI — the one terminal home

Run `anon` (or the `nemo` alias) with **no arguments** to open the interactive console:

```
██      ██  ██████████  ██      ██    ██████  
██      ██  ██████████  ██      ██    ██████  
████    ██  ██          ████  ████  ██      ██
████    ██  ██          ████  ████  ██      ██
██  ██  ██  ████████    ██  ██  ██  ██      ██
██  ██  ██  ████████    ██  ██  ██  ██      ██
██    ████  ██          ██      ██  ██      ██
██    ████  ██          ██      ██  ██      ██
██      ██  ██████████  ██      ██    ██████  
██      ██  ██████████  ██      ██    ██████  

 nemo v0.1.0 · one-way redaction · local

 Available Tools
   detect:    regex + checksum layers (+ optional NER)
   anonymize: placeholder | fake strategies
   inputs:    .txt and .pdf — pdf keeps its original layout
   engine:    uvicorn anonymizer.api:app --port 8000 (REST)

  1) Anonymize a document    3) Engine quickstart
  2) Detect entities         4) Exit
```

- **Anonymize** walks you through: path → NER? → strategy → output name. A PDF input produces a redacted `.pdf` with placeholders stamped in place (layout preserved).
- **Engine quickstart** prints copy-paste startup commands if you also want the REST API.
- Existing venvs need one `pip install -e . --no-deps` to pick up the `nemo` alias.

Scripted usage (same engine):

```bash
# detect (regex + checksum always on; add --ner for the transformer pass)
anon detect invoice.pdf

# anonymize: redacted output; PDF in -> PDF out
anon anonymize invoice.pdf -o invoice_redacted.pdf
```

Redaction is one-way: the redacted file is the only artifact — nothing else to keep, expire or protect.

### Using redacted files with agents

The CLI is the gateway: redact first, hand out the clean file only. The agent never sees the original document — its context only ever contains the redacted text.

---

## How detection works

Three detector layers, deterministic priority on overlap (`checksum > regex > ner`):

1. **Regex detectors** — emails, phone numbers, IBANs, dates, ZIPs, amounts, etc.
2. **Checksum-validated detectors** — Luhn (credit cards), IBAN mod-97, SSN: high-precision, near-zero false positives.
3. **Optional NER** — `dslim/bert-base-NER` via transformers for names, organizations, locations. Off by default because it downloads the model on first use and is capitalization-sensitive (see [`docs/ner-limitations.md`](docs/ner-limitations.md)).

Redaction strategies: `placeholder` (stable `[LABEL_N]` tokens — consistent per value) or `fake` (realistic Faker surrogates for documents you want to stay readable).

## Tests & evaluation

```bash
ruff check .
pytest
python -m eval.run -n 200 --seed 0     # synthetic benchmark: precision / recall / F1
```

On the 200-document synthetic benchmark the pipeline scores **F1 = 1.000** for regex + checksum detectors.

---

## Roadmap — decisions to make to scale this

**Model layer**

- Swap `bert-base-NER` for a **GLiNER-style zero-shot model** to fix lowercase sensitivity and add new entity types without retraining — or fine-tune a DistilBERT-class model on documents representative of your corpus.
- Add a **gazetteer / fuzzy-match pass** for customer-specific names (LLM-agnostic, instant to update).
- Quantize or export the NER model to **ONNX Runtime** (~2–5× CPU inference speedup, smaller memory footprint).
- Consider **multilingual** models if documents stop being English-only.

**Service architecture**

- Add **auth** (API keys / JWT) + rate limiting per client before any shared deployment, plus TLS at the ingress.
- Split the NER pass into a **separate worker/pod**: it holds a large resident model; regex-only requests should not pay for it.
- Long documents: define **chunking + overlap policy** so NER doesn't miss entities split across chunk boundaries.

**Ops & packaging**

- Publish to **PyPI** and ship the container image to **GHCR** so users get `pip install` / `docker pull` instead of cloning.
- Reuse container layers: keep the base image slim (CPU wheels only) to keep pull times low.
- Add observability (request metrics, detection latency, entity-type counts) — Prometheus/Grafana friendly.
- CI is already running ruff + pytest on push; add a release workflow that bumps the version, builds the image and regenerates the eval report per release.
