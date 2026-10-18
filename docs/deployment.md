# Deployment

AnonShield ships as two pieces: a Next.js frontend (docs, tester, assistant) and a
FastAPI backend that runs the detection engine. They deploy separately because the
backend depends on CPU PyTorch, which does not fit inside Vercel serverless functions.

```
Browser ──► Next.js on Vercel ──► /api/chat (Groq)
                     │
                     └──► FastAPI + PyTorch in Docker (Render / Railway / Fly / HF Spaces)
```

## 1. Backend (Docker)

Build and run the CPU-only image:

```bash
docker build -t anonymizer-api .
docker run --rm -p 8000:8000 -e ANONYMIZER_CORS_ORIGINS=https://your-frontend.vercel.app anonymizer-api
```

Then host it on any container platform (Render, Railway, Fly.io, Hugging Face Spaces).
Expose port `8000` and set:

| Variable | Value |
| --- | --- |
| `ANONYMIZER_CORS_ORIGINS` | Comma-separated browser origins, e.g. `https://your-frontend.vercel.app` |

Confirm the deployment with `GET /health` and `POST /detect`.

The NER model (`dslim/bert-base-NER`) downloads on first use, so the first request that
sets `ner: true` is slower than later ones. Give the container enough memory (about 2 GB).

## 2. Frontend (Vercel)

Import the repository into Vercel and set the **root directory** to `web`.

`web/vercel.json` sets the build command to `npm run index && npm run build`, so the RAG
index is regenerated from `web/lib/rag-corpus.json` on every deploy. The committed
`web/lib/embeddings.json` is a fallback if indexing is skipped.

Environment variables (Project → Settings → Environment Variables):

| Variable | Scope | Value |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | build + runtime | Public URL of the Docker backend |
| `GROQ_API_KEY` | server only | A Groq API key for the assistant |

`GROQ_API_KEY` is read only by the `/api/chat` route. Never prefix it with
`NEXT_PUBLIC_`, and never commit it. Rotate any key that has been shared in plain text.

## 3. Wiring the two together

1. Deploy the backend first and note its URL.
2. Set `NEXT_PUBLIC_API_URL` on Vercel to that URL.
3. Set `ANONYMIZER_CORS_ORIGINS` on the backend to the Vercel domain.
4. Redeploy the frontend so the new `NEXT_PUBLIC_API_URL` is baked in.

## Local development

```bash
# Backend
.venv\Scripts\uvicorn anonymizer.api:app --reload            # http://localhost:8000

# Frontend
cd web
npm install
npm run index                                                # regenerate embeddings
npm run dev                                                  # http://localhost:3000
```

Copy `web/.env.example` to `web/.env.local` and set `GROQ_API_KEY` to enable the
assistant locally.
