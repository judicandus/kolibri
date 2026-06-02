#!/usr/bin/env python3
"""
Test script to process only 100 chunks and identify issues
"""

import os
import json
import httpx
import asyncio
import asyncpg
from pathlib import Path
from typing import List

# Configuration
CHUNKS_FILE = Path(__file__).parent.parent / "corpus" / "processed" / "all_chunks.json"
POSTGRES_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://kolibri_ai:KolibriAI2024Secure!@postgres-ai-service:5432/kolibri_ai"
)
ALIBABA_API_KEY = os.environ.get("ALIBABA_API_KEY", "")
ALIBABA_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
EMBEDDING_MODEL = "text-embedding-v3"
BATCH_SIZE = 10
TEST_LIMIT = 100  # Process only 100 chunks for testing


async def generate_embeddings_batch(client: httpx.AsyncClient, texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    print(f"    Calling API with {len(texts)} texts...", flush=True)
    response = await client.post(
        f"{ALIBABA_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {ALIBABA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": EMBEDDING_MODEL,
            "input": texts
        }
    )

    print(f"    API response status: {response.status_code}", flush=True)
    
    if response.status_code != 200:
        print(f"    Error response: {response.text[:500]}", flush=True)
        raise Exception(f"Embedding API error: {response.status_code}")

    data = response.json()
    embeddings = sorted(data["data"], key=lambda x: x["index"])
    print(f"    Got {len(embeddings)} embeddings", flush=True)
    return [e["embedding"] for e in embeddings]


async def main():
    print("=" * 60, flush=True)
    print("TEST: Processing only 100 chunks", flush=True)
    print("=" * 60, flush=True)

    # 1. Load chunks
    print(f"\n[1/3] Loading chunks from {CHUNKS_FILE}...", flush=True)
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        all_docs = json.load(f)

    print(f"  Loaded {len(all_docs)} chunks, using only {TEST_LIMIT}", flush=True)
    all_docs = all_docs[:TEST_LIMIT]

    # 2. Generate embeddings
    print(f"\n[2/3] Generating embeddings with {EMBEDDING_MODEL}...", flush=True)
    
    if not ALIBABA_API_KEY:
        print("ERROR: ALIBABA_API_KEY not set!", flush=True)
        return

    print(f"  API Key: {ALIBABA_API_KEY[:10]}...", flush=True)
    print(f"  Base URL: {ALIBABA_BASE_URL}", flush=True)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Process in batches
        all_embeddings = []
        total_batches = (len(all_docs) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in range(0, len(all_docs), BATCH_SIZE):
            batch = all_docs[i:i + BATCH_SIZE]
            batch_texts = [doc["text"] for doc in batch]
            batch_num = i // BATCH_SIZE + 1

            print(f"\n  Processing batch {batch_num}/{total_batches}...", flush=True)

            try:
                embeddings = await generate_embeddings_batch(client, batch_texts)
                all_embeddings.extend(embeddings)
                print(f"  ✓ Success: {len(embeddings)} embeddings", flush=True)
            except Exception as e:
                print(f"  ✗ Error: {type(e).__name__}: {e}", flush=True)
                import traceback
                traceback.print_exc()
                return

            # Small delay
            await asyncio.sleep(0.1)

        print(f"\n  Generated {len(all_embeddings)} embeddings", flush=True)

    # 3. Store in PostgreSQL
    print(f"\n[3/3] Storing in PostgreSQL...", flush=True)
    print(f"  Connection URL: {POSTGRES_URL[:50]}...", flush=True)
    
    async with asyncpg.create_pool(POSTGRES_URL, min_size=2, max_size=10) as pool:
        async with pool.acquire() as conn:
            # Clear existing data
            print("  Clearing existing data...", flush=True)
            await conn.execute("DELETE FROM rag_chunks")

            # Insert in batches
            print("  Inserting chunks...", flush=True)
            
            values = []
            for doc, emb in zip(all_docs, all_embeddings):
                emb_str = "[" + ",".join(str(x) for x in emb) + "]"
                values.append((
                    doc["text"],
                    doc.get("source", ""),
                    doc.get("category", ""),
                    emb_str
                ))

            await conn.executemany(
                """
                INSERT INTO rag_chunks (content, source, category, embedding)
                VALUES ($1, $2, $3, $4::vector)
                """,
                values
            )

            print(f"  Inserted {len(values)}/{len(all_docs)}", flush=True)

            # Verify
            count = await conn.fetchval("SELECT COUNT(*) FROM rag_chunks")
            print(f"\n  ✓ Inserted {count} chunks into rag_chunks table", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("TEST complete!", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    import sys
    import traceback
    
    try:
        print("Starting test...", flush=True)
        asyncio.run(main())
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"FATAL ERROR: {type(e).__name__}: {e}", flush=True)
        print('='*60, flush=True)
        traceback.print_exc()
        sys.exit(1)
