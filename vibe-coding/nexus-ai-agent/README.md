# NEXUS AI

NEXUS AI is a dark, technical AI companion web experience built with **Next.js App Router, React, Tailwind CSS, Lucide, and Framer Motion**, with an existing **FastAPI/Ollama agent backend**.

The project is primarily designed to run with **Ollama** for local AI inference, while the backend also supports **Google Gemini API** and **NVIDIA** as alternative providers.

## Features

- Dark, technical AI companion interface
- Next.js App Router frontend
- React-based UI
- Tailwind CSS styling
- Framer Motion animations
- Lucide icons
- FastAPI agent backend
- Ollama support for local AI inference
- Gemini API support
- NVIDIA provider support
- Frontend chat preview can render without the backend
- Live agent responses connect through `NEXT_PUBLIC_API_BASE_URL`
- Sitemap, robots, and `llms.txt` support
- Custom favicon and social assets
- Route metadata and canonical/social URL support

## Tech Stack

### Frontend
- Next.js
- React
- Tailwind CSS
- Lucide
- Framer Motion

### Backend
- Python
- FastAPI
- Ollama
- Gemini API support
- NVIDIA provider support

## Testing Video

[Watch the website testing video on Google Drive](https://drive.google.com/file/d/13xybV_o-BucPVI8ksCTjYlVH34feo43V/view?usp=drive_link)

## Requirements

Make sure you have the following installed:

- Node.js
- npm
- Python 3.12
- Ollama

## Installation & Setup

### 1. Install frontend dependencies

From the project root:

```bash
npm install
```

### 2. Set up the backend

```bash
cd backend
```

Create a Python 3.12 virtual environment:

```bash
python3.12 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install pytest:

```bash
pip install pytest
```

### 3. Run backend tests

```bash
python -m pytest -q
```

### 4. Start the FastAPI backend

```bash
uvicorn app.main:app --reload --port 8000
```

Keep this terminal running.

### 5. Start the frontend

Open a **second terminal**, return to the project root, and run:

```bash
npm run dev
```

## Environment Configuration

Copy the frontend environment example:

```bash
cp .env.local.example .env.local
```

The frontend uses:

```text
NEXT_PUBLIC_API_BASE_URL
```

to connect to the agent backend.

For production, set:

```text
NEXT_PUBLIC_SITE_URL
```

to the real custom domain so canonical URLs, social metadata, and sitemap URLs use the final site.

The backend also uses an environment file for its AI/provider configuration.

## AI Providers

NEXUS is built around **Ollama** for local AI inference, while the backend also supports:

| Provider | Purpose |
|---|---|
| Ollama | Local AI inference |
| Google Gemini | API-based AI provider |
| NVIDIA | API-based AI provider |

The frontend can render its chat preview without the backend. Live agent responses require the backend to be running and the API base URL to be configured correctly.

## QA

### Frontend

From the project root:

```bash
npm run lint
```

### Backend

From the `backend` directory:

```bash
python -m pytest -q
```

## Production Notes

The application uses:

```text
productionBrowserSourceMaps: false
```

It also includes:

- Custom favicon and social assets
- Route metadata
- `sitemap.xml`
- `robots.txt`
- `llms.txt`

Before deploying, make sure `NEXT_PUBLIC_SITE_URL` points to the final production domain.

## Project Workflow

```text
Project Root
│
├── npm install
│
├── Backend
│   ├── Create Python 3.12 virtual environment
│   ├── Install requirements
│   ├── Run pytest
│   └── Start FastAPI on port 8000
│
└── Frontend
    └── npm run dev
```

Run the backend and frontend in separate terminals during development.

## License

Add the project's license information here if a specific license is being used.
