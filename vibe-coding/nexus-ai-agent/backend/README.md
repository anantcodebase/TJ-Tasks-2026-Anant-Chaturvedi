# NEXUS Agent Backend

FastAPI backend for the NEXUS AI dashboard.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API listens on `http://localhost:8000`.

## Gemini

Gemini is the default provider. Set `GEMINI_API_KEY` in the backend `.env` file. The model defaults to `gemini-3.8-flash` and can be changed with `GEMINI_MODEL`.

The API key is server-side only and must never be exposed through a `NEXT_PUBLIC_*` variable or frontend source.

## NVIDIA hosted API provider

NVIDIA is available through the same `LLMClient` provider abstraction. Set `AI_PROVIDER=nvidia`, keep `NVIDIA_API_KEY` server-side in the backend `.env`, and use `NVIDIA_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b`. The adapter uses NVIDIA’s OpenAI-compatible `POST /v1/chat/completions` endpoint and native function calling for the structured NEXUS plan.

## Optional Ollama provider

The existing Ollama client remains available for local/offline development. Set `AI_PROVIDER=ollama` to use it, with the existing `OLLAMA_*` settings.

## Endpoints

`GET /health`

`GET /api/analytics?metric=engagement`

`POST /api/chat`

The chat contract remains unchanged: the frontend sends the current message, bounded conversation history, and current UI context to the FastAPI agent.

Provider failures return a non-2xx response with a typed `error` object. The optional deterministic recovery planner is disabled by default (`ALLOW_FALLBACK=false`); enable it only when the UI is intended to disclose local recovery rather than provider output.
