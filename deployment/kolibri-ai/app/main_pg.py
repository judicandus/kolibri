"""
Angels Academy AI - FastAPI Application
PostgreSQL + pgvector implementation
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncpg
import httpx
import os
import json
import uuid
from datetime import datetime
from pathlib import Path

# Configuration
POSTGRES_URL = os.environ.get("DATABASE_URL", "postgresql://kolibri_ai:KolibriAI2024Secure!@postgres-ai-service:5432/kolibri_ai")
ALIBABA_API_KEY = os.environ.get("ALIBABA_API_KEY", "")
ALIBABA_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
ALIBABA_MODEL = "qwen-plus"
AUTH_PASSWORD = os.environ.get("AUTH_PASSWORD", "angels2026")
RAG_ENABLED = os.environ.get("RAG_ENABLED", "true").lower() == "true"
RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "5"))

app = FastAPI(title="Angels Academy AI")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Database pool
db_pool: asyncpg.Pool = None


@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(POSTGRES_URL, min_size=2, max_size=10)


@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()


async def get_db():
    global db_pool
    async with db_pool.acquire() as conn:
        yield conn


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class AuthRequest(BaseModel):
    password: str


def verify_auth(request: AuthRequest):
    if request.password != AUTH_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"status": "authenticated"}


async def search_rag_chunks(conn, query: str, top_k: int = RAG_TOP_K) -> List[dict]:
    """Search RAG chunks using vector similarity"""
    if not RAG_ENABLED:
        return []
    
    # Generate embedding for query
    embedding = await generate_embedding(query)
    if not embedding:
        return []
    
    # Convert list to pgvector format: [0.1, 0.2, 0.3]
    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
    
    # Search similar chunks
    results = await conn.fetch("""
        SELECT content, source, category,
               1 - (embedding <=> $1::vector) as similarity
        FROM rag_chunks
        ORDER BY embedding <=> $1::vector
        LIMIT $2
    """, embedding_str, top_k)
    
    return [
        {
            "content": row["content"],
            "source": row["source"],
            "category": row["category"],
            "similarity": float(row["similarity"])
        }
        for row in results
    ]


async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using Alibaba API"""
    if not ALIBABA_API_KEY:
        return None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{ALIBABA_BASE_URL}/embeddings",
            headers={
                "Authorization": f"Bearer {ALIBABA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "text-embedding-v3",
                "input": text
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["data"][0]["embedding"]
        else:
            print(f"Embedding API error: {response.status_code}")
            return None


async def call_qwen(messages: List[dict]) -> str:
    """Call Qwen model via Alibaba API"""
    if not ALIBABA_API_KEY:
        return "[Error: API key not configured]"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{ALIBABA_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {ALIBABA_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": ALIBABA_MODEL,
                "messages": messages,
                "max_tokens": 4096,
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            print(f"Qwen API error: {response.status_code}")
            return f"[Error: API returned {response.status_code}]"


SYSTEM_PROMPT = """You are an AI assistant for Angels Academy, a Christian educational platform.
Your knowledge is grounded in the Bible and Christian teachings.

When answering questions:
1. Reference Bible verses and passages when relevant (e.g., "John 3:16", "Psalm 23:1")
2. Draw from Christian theology and educational principles
3. Do NOT reference Ellen White, denominational statements, or other non-biblical sources
4. If asked about specific denominations or controversial topics, politely redirect to biblical teachings

Be helpful, encouraging, and focused on educational content that aligns with Christian values."""


@app.get("/health")
async def health_check():
    global db_pool
    if db_pool:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "healthy", "database": "connected", "model": ALIBABA_MODEL}
    return {"status": "healthy", "database": "disconnected", "model": ALIBABA_MODEL}


@app.post("/api/auth")
async def authenticate(request: AuthRequest):
    return verify_auth(request)


@app.post("/api/chat")
async def chat(request: ChatRequest, conn=Depends(get_db)):
    # Get or create conversation
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO conversations (id, title, created_at, updated_at)
            VALUES ($1, $2, $3, $4)
        """, conversation_id, request.message[:50], datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
    
    # Search RAG chunks
    rag_context = ""
    if RAG_ENABLED:
        chunks = await search_rag_chunks(conn, request.message)
        if chunks:
            rag_context = "Relevant context from our knowledge base:\n\n"
            for i, chunk in enumerate(chunks, 1):
                rag_context += f"[{i}] ({chunk['category']}) {chunk['content']}\n"
                if chunk['source']:
                    rag_context += f"    Source: {chunk['source']}\n\n"
    
    # Build messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if rag_context:
        messages.append({
            "role": "system",
            "content": f"{rag_context}\nUse this context to inform your response when relevant."
        })
    
    # Get conversation history
    history = await conn.fetch("""
        SELECT role, content FROM messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
        LIMIT 10
    """, conversation_id)
    
    for row in history:
        messages.append({"role": row["role"], "content": row["content"]})
    
    # Add user message
    messages.append({"role": "user", "content": request.message})
    
    # Call Qwen
    response = await call_qwen(messages)
    
    # Save messages
    await conn.execute("""
        INSERT INTO messages (id, conversation_id, role, content, rag_sources, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
    """, str(uuid.uuid4()), conversation_id, "user", request.message, 
       json.dumps(rag_context) if rag_context else None, datetime.utcnow().isoformat())
    
    await conn.execute("""
        INSERT INTO messages (id, conversation_id, role, content, created_at)
        VALUES ($1, $2, $3, $4, $5)
    """, str(uuid.uuid4()), conversation_id, "assistant", response, datetime.utcnow().isoformat())
    
    # Update conversation
    await conn.execute("""
        UPDATE conversations
        SET updated_at = $1
        WHERE id = $2
    """, datetime.utcnow().isoformat(), conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "message": response,
        "model": ALIBABA_MODEL,
        "rag_used": bool(rag_context)
    }


@app.get("/api/conversations")
async def list_conversations(conn=Depends(get_db)):
    rows = await conn.fetch("""
        SELECT id, title, created_at, updated_at
        FROM conversations
        ORDER BY updated_at DESC
    """)
    return {"conversations": [dict(row) for row in rows]}


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, conn=Depends(get_db)):
    rows = await conn.fetch("""
        SELECT id, role, content, created_at
        FROM messages
        WHERE conversation_id = $1
        ORDER BY created_at ASC
    """, conversation_id)
    
    if not rows:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"messages": [dict(row) for row in rows]}


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, conn=Depends(get_db)):
    await conn.execute("DELETE FROM messages WHERE conversation_id = $1", conversation_id)
    await conn.execute("DELETE FROM conversations WHERE id = $1", conversation_id)
    return {"status": "deleted"}


@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = Path(__file__).parent / "templates" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content="<h1>Angels Academy AI</h1><p>API is running</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
