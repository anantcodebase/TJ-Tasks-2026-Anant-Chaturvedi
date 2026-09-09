# NEXUS AI

NEXUS is a dark, technical AI companion web experience built with Next.js App Router, React, Tailwind CSS, Lucide, Framer Motion, and the existing FastAPI/Ollama agent backend.

## Run

Install dependencies:

```bash
npm install
```

For the optional agent backend:

```bash
cp .env.local.example .env.local
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Then, from the project root:

```bash
npm run dev
```

The frontend can still render its chat preview without the backend; live agent responses use `NEXT_PUBLIC_API_BASE_URL`.

## Production domain

Set `NEXT_PUBLIC_SITE_URL` to the real custom domain before deployment so canonical/social/sitemap URLs point at the final site.

## QA

```bash
npm run lint
cd backend && python -m pytest -q
```

The frontend uses `productionBrowserSourceMaps: false`, has custom favicon/social assets, route metadata, `sitemap.xml`, `robots.txt`, and `llms.txt` support.
