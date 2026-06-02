-- Kolibri AI PostgreSQL Schema
-- Includes pgvector extension for RAG

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,
    content TEXT,
    rag_sources TEXT,
    created_at TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Index for faster message queries
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
ON messages(conversation_id);

-- RAG chunks table with pgvector
CREATE TABLE IF NOT EXISTS rag_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source TEXT,
    category TEXT,
    embedding vector(1024)  -- Qwen embedding dimension
);

-- Index for vector similarity search
CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding 
ON rag_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for category filtering
CREATE INDEX IF NOT EXISTS idx_rag_chunks_category
ON rag_chunks(category);
