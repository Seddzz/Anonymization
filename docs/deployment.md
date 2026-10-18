# Deployment

Nemo is local-first: the engine runs on your machine (Python, the CLI console, or
Docker), while the Next.js docs site — documentation and the Groq-backed assistant —
deploys to Vercel. The site never sends text to the engine and never sees your
documents.

```
Browser ──► Next.js on Vercel ──► /api/chat ──► Groq
Terminal ──► CLI console ──► detection engine (local)
```

## 1. Engine

Run it whichever way suits your workflow — no public host required:

```bash
# Python (editable install)
.venv\Scripts\uvicorn anonymizer.api:app --reload        # http://localhost:8000/docs

# or Docker (rebuilds on start)
docker compose up --build                                # API on :8000

# or skip the server entirely: the terminal console
anon                                                     # or: nemo
```

If you self-host the API on a container platform (Render, Railway, Fly.io, Hugging
Face Spaces), the NER model (`dslim/bert-base-NER`) downloads on first use, so give
the container about 2 GB of memory.

## 2. Frontend (Vercel)

Import the repository into Vercel and set the **root directory** to `web`.

`web/vercel.json` sets the build command to `npm run index && npm run build`, so the
RAG index is regenerated from `web/lib/rag-corpus.json` on every deploy. The committed
`web/lib/embeddings.json` is a fallback if indexing is skipped.

Environment variables (Project → Settings → Environment Variables):

| Variable | Scope | Value |
| --- | --- | --- |
| `GROQ_API_KEY` | server only | A Groq API key for the assistant |

`GROQ_API_KEY` is read only by the `/api/chat` route. Never prefix it with
`NEXT_PUBLIC_`, and never commit it. Rotate any key that has been shared in plain text.

## Local development

```bash
# Engine
.venv\Scripts\uvicorn anonymizer.api:app --reload        # http://localhost:8000

# Docs site
cd web
npm install
npm run index                                            # regenerate embeddings
npm run dev                                              # http://localhost:3000
```

Copy `web/.env.example` to `web/.env.local` and set `GROQ_API_KEY` to enable the
assistant locally.
