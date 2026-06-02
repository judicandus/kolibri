# Angels Academy AI — Complete System Specification

> AI teaching assistant for the Angels for Education foundation, deployed via Kolibri to teach English to teachers in underserved communities across Chad, Myanmar, Thailand, and Brazil.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Infrastructure & Networking](#infrastructure--networking)
3. [Project Structure](#project-structure)
4. [Backend (FastAPI)](#backend-fastapi)
5. [Frontend (SPA)](#frontend-spa)
6. [RAG Corpus](#rag-corpus)
7. [Model Configuration](#model-configuration)
8. [Authentication](#authentication)
9. [Kolibri Integration](#kolibri-integration)
10. [Deployment](#deployment)
11. [Development Workflow](#development-workflow)
12. [Scripts Reference](#scripts-reference)
13. [Testing](#testing)
14. [Database](#database)
15. [Environment Variables](#environment-variables)
16. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  Users access: https://app.angelsforedu.org/ai                   │
│  (Kolibri frontend embeds AI as iframe)                          │
│                                                                  │
│  ┌─────────────────────────┐    ┌──────────────────────────┐     │
│  │ power.local (gateway)   │    │ jarvis (GPU compute)     │     │
│  │ 192.168.1.172           │    │ 192.168.1.133            │     │
│  │                         │    │                          │     │
│  │ Traefik (host network)  │    │ Ollama :11434 (Docker)   │     │
│  │   ↓                     │    │   Local tier:            │     │
│  │ angels-ai container     │    │   - qwen3.5:4b (Africa)  │     │
│  │   FastAPI :8000→:8100   │───▶│   - sailor2:8b (SEA)     │     │
│  │   SentenceTransformer   │    │                          │     │
│  │                         │    │                          │     │
│  │                         │───▶│ Qdrant :6333             │     │
│  │                         │    │   collection:            │     │
│  │        ┌────────────────┤    │   "angels_academy"       │     │
│  │        │ Cloud tier:    │    │   19,838 vectors         │     │
│  │        │ OpenRouter API │    │                          │     │
│  │        │ qwen3.5-122b   │    │                          │     │
│  │        └────────────────┤    │                          │     │
│  └─────────────────────────┘    └──────────────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

The system uses a hybrid local + cloud architecture:

- **power.local (192.168.1.172)** — Gateway/web server. Runs Traefik reverse proxy (host network) and the `angels-ai` Docker container. Handles HTTPS termination, serves the FastAPI app, and loads the embedding model for RAG queries. Also routes cloud-tier requests to OpenRouter.
- **jarvis (192.168.1.133)** — GPU compute server with RTX 5090 (32 GB VRAM). Runs Ollama (local LLM inference) as a Docker container on port 11434 and Qdrant (vector DB) on port 6333.
- **OpenRouter (cloud)** — Hosts the premium Qwen3.5-122B-A10B model via pay-per-token API. Used for the Cloud tier when higher quality is needed.

---

## Infrastructure & Networking

### Servers

| Role | Hostname | IP | Key Services |
|---|---|---|---|
| Gateway | power.local | 192.168.1.172 | Traefik, angels-ai container |
| GPU Compute | jarvis | 192.168.1.133 | Ollama (:11434), Qdrant (:6333) |

### DNS & URLs

- **AI standalone**: `https://ai.angelsforedu.org` — direct access to the AI chat interface
- **Kolibri (production)**: `https://app.angelsforedu.org/ai` — AI embedded as iframe inside Kolibri
- **Kolibri main app**: `https://app.angelsforedu.org`

### Ports

- `8000` — FastAPI inside the container
- `8100` — Host-mapped port on power.local (8100→8000)
- `11434` — Ollama API on jarvis
- `6333` — Qdrant HTTP API on jarvis
- `443/80` — Traefik entrypoints on power.local

### SSH Access

```bash
ssh power.local    # Gateway server
ssh jarvis         # GPU server (or use IP 192.168.1.133)
```

Project on power.local: `/media/storage/docker_starters/kolibri_ai/`
Project on local dev machine: `/home/judicandus/kolibri_ai/`

---

## Project Structure

```
kolibri_ai/
├── app/
│   ├── main.py                  # FastAPI backend (all routes, LLM calls, RAG)
│   ├── templates/
│   │   └── index.html           # SPA frontend (single HTML file)
│   └── static/                  # Static assets (if any)
├── corpus/
│   ├── raw/                     # Source files (ePubs, PDFs, Bible text, website)
│   │   ├── egw/                 # EGW ePub fallbacks
│   │   ├── teaching_materials/  # ESL teaching materials (ages 3-18)
│   │   ├── angels_website_en.txt  # Angels for Education website (English)
│   │   ├── angels_website_fr.txt  # Angels for Education website (French)
│   │   ├── angels_website_es.txt  # Angels for Education website (Spanish)
│   │   ├── angels_website_pt.txt  # Angels for Education website (Portuguese)
│   │   ├── angels_website_ar.txt  # Angels for Education website (Arabic)
│   │   ├── 28_fundamental_beliefs.pdf
│   │   └── kjv_bible.txt
│   ├── egw_api/                 # EGW API downloads (multilingual .txt + manifest.json)
│   └── processed/
│       └── all_chunks.json      # All chunks as JSON (generated by index_corpus.py)
├── data/
│   └── conversations.db         # SQLite database (conversations + messages)
├── scripts/
│   ├── index_corpus.py          # RAG indexer: chunks → embeddings → Qdrant
│   └── download_egw_api.py      # EGW Writings API downloader (OAuth2)
├── tests/
│   ├── run_tests.py             # Test runner v1 (620 test cases)
│   ├── run_tests_v2.py          # Test runner v2 (1727 test cases, 11 models)
│   ├── generate_report.py       # PDF report generator v1
│   ├── generate_report_v2.py    # PDF summary report v2
│   ├── generate_full_catalog.py # Full test catalog PDF v1
│   ├── generate_full_catalog_v2.py # Full catalog PDF v2 (1727 responses)
│   ├── generate_corpus_report.py # Corpus analysis PDF
│   ├── results/                 # v1 test results JSON + PDFs
│   └── results_v2/              # v2 test results JSON + PDFs
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env                         # Secrets (gitignored, chmod 600)
└── README.md                    # This file
```

---

## Backend (FastAPI)

**File**: `app/main.py`

### API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/login` | No | Password login, returns token + sets cookie |
| `POST` | `/api/logout` | No | Clears auth cookie |
| `GET` | `/api/auth/check` | No | Returns `{authenticated: bool}` |
| `GET` | `/api/models` | Yes | Returns available model tiers and models |
| `POST` | `/api/chat` | Yes | Send message, get LLM response with RAG |
| `GET` | `/api/conversations` | Yes | List conversations (last 100, newest first) |
| `GET` | `/api/conversations/{id}` | Yes | Get conversation with all messages |
| `DELETE` | `/api/conversations/{id}` | Yes | Delete conversation and its messages |
| `GET` | `/api/export` | Yes | Export all conversations as JSON download |
| `GET` | `/` | No | Serves the SPA (index.html) |

### Chat Flow (`POST /api/chat`)

Request body:
```json
{
  "message": "What does atonement mean?",
  "model_tier": "local",
  "model_name": "qwen3.5:4b",
  "conversation_id": null
}
```

Processing steps:
1. Create or retrieve conversation
2. Save user message to SQLite
3. Load conversation history (last 20 messages)
4. **RAG search**: embed query with `intfloat/multilingual-e5-large`, search Qdrant top-5, filter by score > 0.3
5. Build system prompt + RAG context + conversation history
6. Call LLM (Ollama for local tier, OpenRouter for cloud tier) with `temperature=0.7`, `max_tokens=8192`, `timeout=300s`
7. Save assistant message with RAG sources
8. Return response with `elapsed_seconds`

### System Prompt

The system prompt defines the assistant's role as an English teaching assistant grounded in Seventh-day Adventist theology. Key behaviors:
- Responds in the user's language
- Supports: English, French, Arabic, Burmese, Thai, Portuguese, Spanish
- Cites sources from the RAG corpus
- Refuses non-Adventist theological debates, medical/legal advice, politics
- Does NOT generate full lesson plans (offers activities/vocabulary instead)

---

## Frontend (SPA)

**File**: `app/templates/index.html`

Single-page application served by FastAPI. Key features:

- **Token-based auth**: Uses `localStorage` token + `Authorization: Bearer` headers via `authFetch()` wrapper. This was specifically designed to work inside cross-origin iframes where third-party cookies are blocked.
- **Markdown rendering**: Uses `marked.js` v15 (CDN) with CSS styling for headings, lists, blockquotes, tables. Falls back to regex-based rendering if CDN fails.
- **Model selector**: Sidebar with tier/model dropdowns
- **Conversation history**: Sidebar list with new/delete/switch capabilities
- **Responsive layout**: Designed to embed seamlessly inside Kolibri's nav frame

### CSS Alignment for Kolibri Embedding

The `.main-header` spacer div pushes the topbar down to align with Kolibri's sidebar navigation. The header has no `border-bottom` and uses `padding: 23px` for pixel-perfect alignment with the Kolibri nav bar.

---

## RAG Corpus

### Embedding Model

- **Model**: `intfloat/multilingual-e5-large`
- **Dimension**: 1024
- **Distance**: Cosine
- **Prefix convention**: `"passage: "` for documents, `"query: "` for search queries

### Qdrant Collection

- **Name**: `angels_academy`
- **Points**: 19,838
- **Host**: jarvis (192.168.1.133:6333)

### Corpus Contents

The corpus consists of five main sources:

1. **EGW Writings (API)** — 44 books across 5 languages (en/fr/es/pt/ar), downloaded via the EGW Writings API. ~40M characters total. Stored as plain text in `corpus/egw_api/` with a `manifest.json` index.

2. **KJV Bible** — Full King James Version, chunked at 400 words with 80-word overlap. Source: Project Gutenberg text in `corpus/raw/kjv_bible.txt`.

3. **28 Fundamental Beliefs** — SDA doctrinal document, PDF extracted and chunked. Source: `corpus/raw/28_fundamental_beliefs.pdf`.

4. **Angels for Education Website** — 13 pages scraped from `angelsforglobaleducation.org`, covering the foundation's mission, programs, team, and impact. Organized into structured documents and translated into 5 languages (en/fr/es/pt/ar) via Gemini. Chunked at 300 words with 60-word overlap. Stored as `corpus/raw/angels_website_{lang}.txt`. Category: `organization`.

5. **ESL Teaching Materials** — Comprehensive English teaching resources for ages 3-18. Includes lesson plans, vocabulary lists, grammar exercises, TPR activities, and assessment techniques organized by age group: pre-primary (3-6), primary (7-12), secondary (13-18), plus a grammar reference. Stored in `corpus/raw/teaching_materials/`. Categories: `teaching_esl`, `teaching_grammar`.

### Target Books (10 titles)

| Code | Title |
|---|---|
| SC | Steps to Christ |
| PP | Patriarchs and Prophets |
| GC | The Great Controversy |
| DA | The Desire of Ages |
| COL | Christ's Object Lessons |
| MH | The Ministry of Healing |
| Ed | Education |
| CT | Counsels to Parents, Teachers, and Students |
| AA | The Acts of the Apostles |
| PK | Prophets and Kings |

### Chunking Parameters

- **Chunk size**: 500 words (400 for Bible, 300 for website)
- **Overlap**: 100 words (80 for Bible, 60 for website)
- **Minimum relevance score**: 0.3 (for RAG retrieval)
- **Top-K**: 5 results per query

### Chunk Metadata Schema

Each chunk stored in Qdrant carries this payload:
```json
{
  "text": "chunk content...",
  "source": "Ellen G. White — Steps to Christ (French)",
  "category": "egw|bible|doctrine|organization",
  "book": "Steps to Christ",
  "chapter": "",
  "language": "fr",
  "chunk_index": 42
}
```

### Rebuilding the Corpus

```bash
# From the dev machine, activate venv first:
source /tmp/kolibri-ai-env/bin/activate

# 1. (Optional) Re-download EGW books from API
cd /home/judicandus/kolibri_ai
python scripts/download_egw_api.py

# 2. Re-index everything into Qdrant
#    This will: process all sources → embed → recreate Qdrant collection
#    Requires Qdrant running on jarvis (192.168.1.133:6333)
QDRANT_URL=http://192.168.1.133:6333 python scripts/index_corpus.py
```

**Important**: The indexer runs on the dev machine (jarvis) where the GPU is available for fast embedding. It connects to Qdrant remotely. After re-indexing, restart the `angels-ai` container so it picks up the new collection stats.

---

## Model Configuration

### Tiers

| Tier | Label | Models | Backend | Region / Use Case |
|---|---|---|---|---|
| `local` | 🖥️ Local (Jetson) | qwen3.5:4b, sailor2:8b | Ollama | Africa & Americas (FR/AR/EN), South-East Asia (MY/TH/EN) |
| `cloud` | ☁️ Cloud (Premium) | qwen/qwen3.5-122b-a10b | OpenRouter | Africa & Americas (FR/AR/EN) — premium quality |

**Model details:**

- **qwen3.5:4b** — Qwen 3.5 4B (Feb 2026). 201 languages. Best for French, Arabic, English, Portuguese, Spanish. Runs on Jetson Orin Nano at ~15 tok/s.
- **sailor2:8b** — Sailor2 8B by Sea AI Lab. Purpose-built for SEA languages with dedicated Burmese (23.5B tokens) and Thai (92B tokens) training data. Best multilingual model for SEA under 10B. Runs on Jetson at ~8 tok/s.
- **qwen/qwen3.5-122b-a10b** — Qwen 3.5 122B-A10B (Feb 2026). 122B total, 10B active (MoE). 201 languages. Significantly better than local models — MMLU-Pro 86.7, GPQA 86.6. Hosted via OpenRouter (pay-per-token, ~$0.26/M input, ~$2.08/M output).

### Ollama Parameters (Local Tier)

- `temperature`: 0.7
- `num_predict`: 8192 tokens (max response length)
- `stream`: false
- `timeout`: 300 seconds

### OpenRouter Parameters (Cloud Tier)

- `temperature`: 0.7
- `max_tokens`: 8192
- `timeout`: 300 seconds
- API: OpenAI-compatible (`https://openrouter.ai/api/v1/chat/completions`)
- Auth: Bearer token via `OPENROUTER_API_KEY` env var

### Managing Models on Ollama

Ollama runs as a Docker container on jarvis. Use `docker exec` to manage models:

```bash
# SSH to jarvis (GPU server)
ssh jarvis

# List pulled models
docker exec ollama ollama list

# Pull production models
docker exec ollama ollama pull qwen3.5:4b
docker exec ollama ollama pull sailor2:8b

# Remove a model
docker exec ollama ollama rm llama3.2:1b
```

To add or remove a model tier, edit the `MODEL_TIERS` dict in `app/main.py` (around line 39). The frontend dynamically reads tiers from the `/api/models` endpoint.

---

## Authentication

### Mechanism

Dual auth for compatibility with both standalone and iframe modes:

1. **Cookie auth** (standalone): `POST /api/login` sets `angels_ai_session=authenticated` cookie (SameSite=None, Secure, HttpOnly, 30-day expiry)
2. **Token auth** (iframe): Login returns `{"token": "authenticated"}`, frontend stores in `localStorage`, sends as `Authorization: Bearer authenticated` header via `authFetch()` wrapper

The token-based approach was implemented because cross-origin iframes (Kolibri at `app.angelsforedu.org` embedding AI at `ai.angelsforedu.org`) block third-party cookies in modern browsers.

### Password

Default: `angels2026` (set via `AUTH_PASSWORD` env var or `.env` file)

### Auth Check

All protected endpoints call `check_auth(request)` which checks cookie first, then Bearer token header.

---

## Kolibri Integration

The AI is embedded inside the Kolibri learning platform as an iframe.

### Kolibri Side

- **Route**: `/ai` in the Kolibri frontend
- **Component**: `AiPage.vue` (custom Kolibri plugin page)
- **URL**: The iframe `src` points to `https://ai.angelsforedu.org`
- **Kolibri instance**: `https://app.angelsforedu.org`

### Cross-Origin Considerations

- CORS is set to `allow_origins=["*"]` in FastAPI middleware
- Auth uses token (not cookies) to avoid third-party cookie issues
- The frontend's `.main-header` spacer div aligns the AI interface with Kolibri's navigation bar

---

## Deployment

### Docker Compose

The app runs as a single Docker container (`angels-ai`) on power.local, behind Traefik.

**Key docker-compose.yml settings**:
- Image built from local `Dockerfile`
- Port mapping: `8100:8000`
- Volume: `./data:/app/data` (persists SQLite DB)
- Traefik labels route `ai.angelsforedu.org` with HTTPS (Let's Encrypt via `myresolver`)
- Environment variables for Ollama/Qdrant URLs, API keys, auth password

### Dockerfile

- Base: `python:3.11-slim`
- Installs `poppler-utils` (for PDF extraction via `pdftotext`)
- Copies `app/`, `corpus/`, `scripts/` into container
- **Pre-downloads embedding model at build time** (`intfloat/multilingual-e5-large`) so startup is fast
- Runs: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Deploy Command

From the local dev machine:

```bash
# 1. Copy project to power.local
scp -r /home/judicandus/kolibri_ai/* power.local:/media/storage/docker_starters/kolibri_ai/

# 2. SSH to power.local and rebuild
ssh power.local
cd /media/storage/docker_starters/kolibri_ai
docker compose up -d --build
```

### Viewing Logs

```bash
ssh power.local
docker logs -f angels-ai
```

---

## Development Workflow

### Local Setup

```bash
# Create virtual environment
python3 -m venv /tmp/kolibri-ai-env
source /tmp/kolibri-ai-env/bin/activate

# Install dependencies
pip install -r /home/judicandus/kolibri_ai/requirements.txt
```

### Running Locally

```bash
source /tmp/kolibri-ai-env/bin/activate
cd /home/judicandus/kolibri_ai

# Set environment (Ollama and Qdrant on jarvis)
export OLLAMA_BASE_URL=http://192.168.1.133:11434
export QDRANT_URL=http://192.168.1.133:6333

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Edit → Deploy Cycle

1. Edit files locally in `/home/judicandus/kolibri_ai/`
2. Test locally if possible
3. `scp` to power.local
4. `docker compose up -d --build` on power.local

---

## Scripts Reference

### `scripts/index_corpus.py`

RAG corpus indexer. Processes all source documents, generates embeddings, and stores in Qdrant.

**Pipeline**:
1. Process 28 Fundamental Beliefs (PDF → text → chunks)
2. Process KJV Bible (text → chunks at 400/80)
3. Process EGW ePubs (fallback, skipped if API version exists)
4. Process EGW API books (multilingual, from `corpus/egw_api/manifest.json`)
5. Process Angels for Education website (5 languages, chunks at 300/60)
6. Process ESL teaching materials (4 files, chunks at 300/60)
7. Save all chunks to `corpus/processed/all_chunks.json`
8. Generate embeddings with `intfloat/multilingual-e5-large` (batch_size=32)
9. Recreate Qdrant collection and upload vectors (batch_size=100)

**Usage**:
```bash
QDRANT_URL=http://192.168.1.133:6333 python scripts/index_corpus.py
```

### `scripts/download_egw_api.py`

Downloads EGW books from the official EGW Writings API in multiple languages.

**Pipeline**:
1. Authenticate via OAuth2 (`client_credentials` grant) at `https://cpanel.egwwritings.org/connect/token`
2. Download 10 English books, extract translation IDs from paragraph cross-references
3. Download translated versions (fr, es, pt, ar; my/th rarely available)
4. Extract text from ZIP → JSON → plain text, save as `{CODE}_{lang}.txt`
5. Write `manifest.json` with metadata

**Requires**: `EGW_CLIENT_ID` and `EGW_CLIENT_SECRET` in `.env`

**API base**: `https://a.egwwritings.org`

**Usage**:
```bash
cd /home/judicandus/kolibri_ai
python scripts/download_egw_api.py
```

---

## Testing

### Test Suite v2 (current)

**File**: `tests/run_tests_v2.py`

- **1,727 total test cases** across 11 models, 7 languages, 36 scenarios, 8 categories
- Categories: Vocabulary (A), Lesson Prep (B), Theological (C), Guardrails (D), Multilingual (E), Reading Comprehension (F), Child Safety (G), ESL Methodology (H)
- Built-in resume support (saves incrementally to JSON)
- Uses Bearer token auth for API calls

### Running Tests

```bash
cd /home/judicandus/kolibri_ai

# Run v2 test suite against local server
API_BASE=http://localhost:8100 python tests/run_tests_v2.py

# Run against production
API_BASE=https://ai.angelsforedu.org python tests/run_tests_v2.py
```

### Test Results Summary (v2 — March 2026)

| Tier | Overall | Accuracy | Safety | Usefulness |
|---|---|---|---|---|
| Small (0.8-2B) | 3.11 / 5 | 1.48 | 3.81 | 2.90 |
| Medium (4-12B) | 3.93 / 5 | 2.48 | 3.90 | 3.82 |
| Large (14-35B) | 4.00 / 5 | 2.72 | 3.93 | 3.89 |

Top models: qwen3.5:35b-a3b (4.22), qwen3.5:9b (4.13), qwen3.5:4b (3.99).
Burmese remains the weakest language (3.34/5 usefulness).
Guardrails safety: 3.09/5 — needs improvement.

### Report Generation

```bash
python tests/generate_report_v2.py          # Summary report PDF (editorial team)
python tests/generate_full_catalog_v2.py     # Full catalog PDF (all 1727 Q&A)
python tests/generate_corpus_report.py       # Corpus analysis PDF
```

---

## Database

**File**: `data/conversations.db` (SQLite)

### Schema

**conversations**
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | UUID |
| title | TEXT | First ~50 chars of first message |
| created_at | TEXT | ISO 8601 UTC |
| updated_at | TEXT | ISO 8601 UTC |

**messages**
| Column | Type | Description |
|---|---|---|
| id | TEXT PK | UUID |
| conversation_id | TEXT FK | References conversations.id |
| role | TEXT | "user" or "assistant" |
| content | TEXT | Message text |
| model_tier | TEXT | e.g. "medium" |
| model_name | TEXT | e.g. "qwen2.5:7b" |
| rag_sources | TEXT | JSON array of RAG sources used |
| created_at | TEXT | ISO 8601 UTC |

### Direct DB Access (Production)

```bash
ssh power.local
docker exec -it angels-ai python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/conversations.db')
conn.row_factory = sqlite3.Row
# Example: count conversations
print(conn.execute('SELECT COUNT(*) FROM conversations').fetchone()[0])
conn.close()
"
```

### Clearing All Conversations

```bash
ssh power.local
docker exec -it angels-ai python3 -c "
import sqlite3
conn = sqlite3.connect('/app/data/conversations.db')
conn.execute('DELETE FROM messages')
conn.execute('DELETE FROM conversations')
conn.commit()
print('Cleared')
conn.close()
"
```

---

## Environment Variables

### Required (in `.env` on power.local)

```
OLLAMA_BASE_URL=http://192.168.1.133:11434
QDRANT_URL=http://192.168.1.133:6333
AUTH_PASSWORD=angels2026
```

### Cloud LLM Backend (OpenRouter)

```
OPENROUTER_API_KEY=sk-or-v1-...
```

### Optional (currently unused)

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### EGW API (for corpus downloads only, not needed at runtime)

```
EGW_CLIENT_ID=...
EGW_CLIENT_SECRET=...
```

The `.env` file is at the project root, `chmod 600`, and gitignored.

---

## Troubleshooting

### Container won't start

```bash
ssh power.local
docker logs angels-ai
# Common issues: Qdrant unreachable, Ollama unreachable, port conflict
```

### RAG not returning results

1. Check Qdrant is running: `curl http://192.168.1.133:6333/collections/angels_academy`
2. Check collection has points (should be 19,813)
3. Check the embedding model loaded in container logs (`RAG: Ready`)
4. If collection is missing, re-run `scripts/index_corpus.py`

### LLM responses empty or erroring

1. Check Ollama is running: `curl http://192.168.1.133:11434/api/tags`
2. Verify model is pulled: `ssh jarvis` then `docker exec ollama ollama list`
3. Check timeout — large models may need the full 300s

### Auth not working in iframe

- Token auth should be used (not cookies) for cross-origin iframe embedding
- Check browser console for CORS errors
- Verify `authFetch()` is sending `Authorization: Bearer authenticated` header

### Embedding model slow to load

The Dockerfile pre-downloads `intfloat/multilingual-e5-large` at build time. If the image was built without this step, first startup will take several minutes while it downloads ~2.2 GB.
