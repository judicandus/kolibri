"""
Angels Academy AI Assistant — FastAPI Backend (Simplified)
Single-model architecture using Alibaba DashScope Qwen3.7-max
RAG retrieval with PostgreSQL pgvector (migrated from Qdrant)
"""

import os
import json
import uuid
import time
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import asyncpg
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Configuration ---
ALIBABA_API_KEY = os.environ.get("ALIBABA_API_KEY", "")
ALIBABA_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
ALIBABA_MODEL = "qwen-plus"  # Qwen-Plus model
ALIBABA_EMBEDDING_MODEL = "text-embedding-v3"
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "angels2026")
AUTH_COOKIE_NAME = "angels_ai_session"
DATA_DIR = Path(os.environ.get("DATA_DIR", Path(__file__).parent.parent / "data"))
DB_PATH = DATA_DIR / "conversations.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://kolibri_ai:KolibriAI2024Secure!@postgres-ai-service.kolibri-ai.svc.cluster.local:5432/kolibri_ai")

# RAG Configuration (PostgreSQL pgvector)
RAG_ENABLED = os.environ.get("RAG_ENABLED", "true").lower() == "true"
MIN_RELEVANCE_SCORE = 0.3
TOP_K = 5

# System Prompt - Bible-only references
SYSTEM_PROMPT = """You are the Angels Academy Assistant, a patient and encouraging teaching assistant for English teachers in the Angels Academy program by the Angels for Education foundation.

Your role:
- Help teachers improve their English language skills
- Assist with lesson preparation and activity ideas
- Explain vocabulary, grammar, and sentence construction
- Answer questions about Bible passages from a Christian perspective
- Adapt explanations to the teacher's local context

Language behavior:
- Respond in the same language the teacher writes in
- When explaining English concepts, use the teacher's language for explanations and provide English examples
- You support English, French, Arabic, Burmese, Thai, Portuguese, and Spanish

Biblical guidelines:
- Use the Bible as your primary reference source
- When citing sources, reference Bible books, chapters, and verses (e.g., "According to John 3:16..." or "In Psalm 23...")
- You may draw on Christian theological knowledge to explain concepts, but always ground your answers in Scripture
- Do NOT cite Ellen White, denominational statements, or other non-biblical sources
- When asked about denominational differences, politely explain that you focus on biblical teaching and suggest the teacher consult their pastor for denominational questions

Scope:
- Help with: English language, lesson preparation, activity ideas, vocabulary, grammar, Bible passage understanding, contextual adaptation of lessons
- Do NOT: Generate complete lesson plans from scratch, give medical/legal advice, discuss politics, or engage with non-Christian theological debates
- When asked to write a full lesson plan, instead offer specific activity ideas and vocabulary suggestions

Keep responses clear, practical, and concise. Use simple language since the teachers are still learning English themselves."""

# --- Database ---
def init_db():
    """Initialize SQLite database (will be migrated to PostgreSQL)"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            rag_sources TEXT,
            created_at TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# --- RAG with PostgreSQL pgvector ---
async def search_rag(query: str) -> list:
    """
    Search the RAG corpus for relevant context using PostgreSQL pgvector.
    Returns list of relevant chunks with similarity scores.
    Only includes Bible sources (category = 'bible').
    """
    if not RAG_ENABLED:
        return []

    try:
        # Generate embedding for the query
        query_embedding = await generate_embedding(query)
        if not query_embedding:
            return []

        # Convert embedding list to pgvector string format
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        # Search for similar chunks in PostgreSQL
        conn = await asyncpg.connect(DATABASE_URL)
        try:
            # Use cosine similarity (1 - cosine_distance)
            # Filter only Bible sources
            results = await conn.fetch(
                """
                SELECT 
                    content,
                    source,
                    category,
                    1 - (embedding <=> $1::vector) AS similarity
                FROM rag_chunks
                WHERE category = 'bible'
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                embedding_str,
                TOP_K
            )

            # Filter by minimum similarity and format results
            rag_sources = []
            for row in results:
                if row['similarity'] >= MIN_RELEVANCE_SCORE:
                    rag_sources.append({
                        'source': row['source'],
                        'category': row['category'],
                        'text': row['content'],
                        'score': float(row['similarity'])
                    })

            return rag_sources
        finally:
            await conn.close()

    except Exception as e:
        print(f"RAG search error: {e}")
        return []


async def generate_embedding(text: str) -> list:
    """
    Generate embedding for a single text using Alibaba DashScope API.
    Returns embedding vector or None on error.
    """
    if not ALIBABA_API_KEY:
        return None

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{ALIBABA_BASE_URL}/embeddings",
                headers={
                    "Authorization": f"Bearer {ALIBABA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": ALIBABA_EMBEDDING_MODEL,
                    "input": text,
                    "encoding_format": "float"
                }
            )

            if resp.status_code == 200:
                data = resp.json()
                return data['data'][0]['embedding']
            else:
                print(f"Embedding API error: {resp.status_code}")
                return None

    except Exception as e:
        print(f"Embedding generation error: {e}")
        return None


def build_rag_context(sources: list) -> str:
    """Build context string from RAG sources."""
    if not sources:
        return ""

    context_parts = ["[Reference Materials]"]
    for i, s in enumerate(sources, 1):
        context_parts.append(f"\n--- Source {i}: {s['source']} ---\n{s['text']}")
    context_parts.append("\n[End of Reference Materials]\n")
    return "\n".join(context_parts)


# --- Alibaba DashScope API ---
async def call_alibaba_qwen(messages: list) -> str:
    """
    Call Alibaba DashScope API for Qwen3.7-max model.
    Uses OpenAI-compatible endpoint.
    """
    if not ALIBABA_API_KEY:
        return "[Error: ALIBABA_API_KEY not configured]"

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{ALIBABA_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {ALIBABA_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": ALIBABA_MODEL,
                "messages": messages,
                "max_tokens": 8192,
                "temperature": 0.7,
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


# --- App lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Angels Academy AI (Simplified)...")
    init_db()
    
    if ALIBABA_API_KEY:
        print(f"LLM: Configured for Alibaba DashScope ({ALIBABA_MODEL})")
    else:
        print("LLM: WARNING - ALIBABA_API_KEY not set!")
    
    if RAG_ENABLED:
        print("RAG: Enabled (PostgreSQL pgvector)")
    else:
        print("RAG: Disabled (will be enabled after PostgreSQL setup)")
    
    yield
    print("Shutting down Angels Academy AI...")


# --- FastAPI App ---
app = FastAPI(title="Angels Academy AI (Simplified)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Static files
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Auth ---
def check_auth(request: Request) -> bool:
    # Check cookie (standalone mode)
    session = request.cookies.get(AUTH_COOKIE_NAME)
    if session == "authenticated":
        return True
    # Check Authorization header (iframe/token-based auth)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and auth_header[7:] == "authenticated":
        return True
    return False


# --- API Models ---
class LoginRequest(BaseModel):
    password: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


# --- Routes ---
@app.post("/api/login")
async def login(req: LoginRequest, response: Response):
    if req.password == AUTH_PASSWORD:
        response.set_cookie(
            AUTH_COOKIE_NAME, "authenticated", httponly=True,
            max_age=86400 * 30, samesite="none", secure=True,
        )
        return {"status": "ok", "token": "authenticated"}
    raise HTTPException(status_code=401, detail="Invalid password")


@app.post("/api/logout")
async def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE_NAME)
    return {"status": "ok"}


@app.get("/api/auth/check")
async def auth_check(request: Request):
    return {"authenticated": check_auth(request)}


@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    return {"status": "healthy", "service": "kolibri-ai"}


@app.get("/api/models")
async def list_models(request: Request):
    """Simplified - returns single model info"""
    if not check_auth(request):
        raise HTTPException(status_code=401)
    return {
        "model": ALIBABA_MODEL,
        "provider": "Alibaba DashScope",
        "rag_enabled": RAG_ENABLED
    }


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    if not check_auth(request):
        raise HTTPException(status_code=401)

    db = get_db()
    try:
        # Get or create conversation
        conv_id = req.conversation_id
        if not conv_id:
            conv_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            title = req.message[:50] + ("..." if len(req.message) > 50 else "")
            db.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conv_id, title, now, now),
            )
        else:
            # Check if conversation exists, create if not
            existing = db.execute(
                "SELECT id FROM conversations WHERE id = ?",
                (conv_id,),
            ).fetchone()
            if not existing:
                now = datetime.now(timezone.utc).isoformat()
                title = req.message[:50] + ("..." if len(req.message) > 50 else "")
                db.execute(
                    "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (conv_id, title, now, now),
                )

        # Save user message
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "INSERT INTO messages (id, conversation_id, role, content, rag_sources, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, conv_id, "user", req.message, "[]", now),
        )

        # Get conversation history
        rows = db.execute(
            "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conv_id,),
        ).fetchall()

        # Search RAG for relevant context
        rag_sources = await search_rag(req.message)
        rag_context = build_rag_context(rag_sources)

        # Build messages for LLM
        system_content = SYSTEM_PROMPT
        if rag_context:
            system_content += "\n\n" + rag_context

        messages = [{"role": "system", "content": system_content}]

        # Add conversation history (last 20 messages)
        for row in rows[-20:]:
            messages.append({"role": row["role"], "content": row["content"]})

        # Call LLM
        start_time = time.time()
        try:
            response_text = await call_alibaba_qwen(messages)
        except Exception as e:
            response_text = f"[Error calling model: {str(e)}]"
        elapsed = round(time.time() - start_time, 2)

        # Save assistant message
        asst_msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        db.execute(
            "INSERT INTO messages (id, conversation_id, role, content, rag_sources, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (asst_msg_id, conv_id, "assistant", response_text, json.dumps(rag_sources), now),
        )

        # Update conversation
        db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conv_id),
        )
        db.commit()

        return {
            "conversation_id": conv_id,
            "message": response_text,
            "model": ALIBABA_MODEL,
            "rag_sources": rag_sources,
            "elapsed_seconds": elapsed,
        }

    finally:
        db.close()


@app.get("/api/conversations")
async def list_conversations(request: Request):
    if not check_auth(request):
        raise HTTPException(status_code=401)

    db = get_db()
    rows = db.execute(
        "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT 100"
    ).fetchall()
    db.close()

    return {"conversations": [dict(r) for r in rows]}


@app.get("/api/conversations/{conv_id}")
async def get_conversation(conv_id: str, request: Request):
    if not check_auth(request):
        raise HTTPException(status_code=401)

    db = get_db()
    conv = db.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    if not conv:
        db.close()
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.execute(
        "SELECT id, role, content, rag_sources, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at",
        (conv_id,),
    ).fetchall()
    db.close()

    return {
        "conversation": dict(conv),
        "messages": [dict(m) for m in messages],
    }


@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: str, request: Request):
    if not check_auth(request):
        raise HTTPException(status_code=401)

    db = get_db()
    db.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    db.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    db.commit()
    db.close()
    return {"status": "deleted"}


@app.get("/api/export")
async def export_data(request: Request):
    if not check_auth(request):
        raise HTTPException(status_code=401)

    db = get_db()
    conversations = db.execute("SELECT * FROM conversations ORDER BY created_at").fetchall()

    export = []
    for conv in conversations:
        messages = db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conv["id"],),
        ).fetchall()
        export.append({
            "conversation": dict(conv),
            "messages": [dict(m) for m in messages],
        })
    db.close()

    return JSONResponse(
        content={"exported_at": datetime.now(timezone.utc).isoformat(), "conversations": export},
        headers={"Content-Disposition": "attachment; filename=angels_ai_export.json"},
    )


# --- HTML page (SPA) ---
@app.get("/")
async def index(request: Request):
    html_path = Path(__file__).parent / "templates" / "index.html"
    return HTMLResponse(html_path.read_text())
