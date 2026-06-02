#!/usr/bin/env python3
"""
Angels Academy AI — PostgreSQL RAG Indexer
Indexes pre-processed chunks into PostgreSQL with pgvector using Qwen embeddings.
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
    "postgresql://kolibri_ai:KolibriAI2024Secure!@localhost:5432/kolibri_ai"
)
ALIBABA_API_KEY = os.environ.get("ALIBABA_API_KEY", "")
ALIBABA_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
EMBEDDING_MODEL = "text-embedding-v3"
BATCH_SIZE = 10


async def generate_embedding(client: httpx.AsyncClient, text: str) -> List[float]:
    """Generate embedding using Alibaba Qwen API."""
    response = await client.post(
        f"{ALIBABA_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {ALIBABA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": EMBEDDING_MODEL,
            "input": text
        }
    )

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", flush=True)
        raise Exception(f"Embedding API error: {response.status_code}")

    data = response.json()
    return data["data"][0]["embedding"]


async def generate_embeddings_batch(
    client: httpx.AsyncClient,
    texts: List[str]
) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    # Qwen supports batch embeddings
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

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}", flush=True)
        raise Exception(f"Embedding API error: {response.status_code}")

    data = response.json()
    # Sort by index to maintain order
    embeddings = sorted(data["data"], key=lambda x: x["index"])
    return [e["embedding"] for e in embeddings]


async def main():
    print("=" * 60, flush=True)
    print("Angels Academy AI — PostgreSQL RAG Indexer", flush=True)
    print("=" * 60, flush=True)

    # 1. Load chunks
    print(f"\n[1/3] Loading chunks from {CHUNKS_FILE}...", flush=True)
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        all_docs = json.load(f)

    print(f"  Loaded {len(all_docs)} chunks", flush=True)

    # Show category distribution
    categories = {}
    for doc in all_docs:
        cat = doc.get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print("\n  Category distribution:", flush=True)
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}", flush=True)

    # 2. Generate embeddings
    print(f"\n[2/3] Generating embeddings with {EMBEDDING_MODEL}...", flush=True)
    
    if not ALIBABA_API_KEY:
        print("ERROR: ALIBABA_API_KEY not set!", flush=True)
        return

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test API with first chunk
        print("  Testing API with first chunk...", flush=True)
        test_embedding = await generate_embedding(client, all_docs[0]["text"])
        dim = len(test_embedding)
        print(f"  Embedding dimension: {dim}", flush=True)

        # Process in batches
        all_embeddings = []
        total_batches = (len(all_docs) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in range(0, len(all_docs), BATCH_SIZE):
            batch = all_docs[i:i + BATCH_SIZE]
            batch_texts = [doc["text"] for doc in batch]
            batch_num = i // BATCH_SIZE + 1

            print(f"  Processing batch {batch_num}/{total_batches}...", end=" ", flush=True)

            try:
                embeddings = await generate_embeddings_batch(client, batch_texts)
                all_embeddings.extend(embeddings)
                print(f"✓ ({len(embeddings)} embeddings)", flush=True)
            except Exception as e:
                print(f"✗ Error: {e}", flush=True)
                # Try one by one
                for j, text in enumerate(batch_texts):
                    try:
                        emb = await generate_embedding(client, text)
                        all_embeddings.append(emb)
                    except Exception as e2:
                        print(f"    Failed chunk {i+j}: {e2}", flush=True)
                        all_embeddings.append([0.0] * dim)  # Placeholder

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)

        print(f"\n  Generated {len(all_embeddings)} embeddings", flush=True)

    # 3. Store in PostgreSQL
    print(f"\n[3/3] Storing in PostgreSQL...", flush=True)
    
    async with asyncpg.create_pool(POSTGRES_URL, min_size=2, max_size=10) as pool:
        async with pool.acquire() as conn:
            # Clear existing data
            print("  Clearing existing data...", flush=True)
            await conn.execute("DELETE FROM rag_chunks")

            # Insert in batches
            print("  Inserting chunks...", flush=True)
            insert_batch_size = 100

            for i in range(0, len(all_docs), insert_batch_size):
                batch_docs = all_docs[i:i + insert_batch_size]
                batch_embs = all_embeddings[i:i + insert_batch_size]

                # Prepare batch insert
                values = []
                for doc, emb in zip(batch_docs, batch_embs):
                    # Convert embedding to pgvector format
                    emb_str = "[" + ",".join(str(x) for x in emb) + "]"
                    values.append((
                        doc["text"],
                        doc.get("source", ""),
                        doc.get("category", ""),
                        emb_str
                    ))

                # Batch insert
                await conn.executemany(
                    """
                    INSERT INTO rag_chunks (content, source, category, embedding)
                    VALUES ($1, $2, $3, $4::vector)
                    """,
                    values
                )

                print(f"    Inserted {i + len(values)}/{len(all_docs)}", flush=True)

            # Verify
            count = await conn.fetchval("SELECT COUNT(*) FROM rag_chunks")
            print(f"\n  ✓ Inserted {count} chunks into rag_chunks table", flush=True)

            # Show sample
            print("\n  Sample chunk:", flush=True)
            sample = await conn.fetchrow("""
                SELECT content, source, category
                FROM rag_chunks
                LIMIT 1
            """)
            if sample:
                print(f"    Source: {sample['source']}", flush=True)
                print(f"    Category: {sample['category']}", flush=True)
                print(f"    Content: {sample['content'][:200]}...", flush=True)

    print("\n" + "=" * 60, flush=True)
    print("Indexing complete!", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    import sys
    import traceback
    
    try:
        print("Starting indexing process...", flush=True)
        asyncio.run(main())
    except Exception as e:
        print(f"\n{'='*60}", flush=True)
        print(f"FATAL ERROR: {type(e).__name__}: {e}", flush=True)
        print('='*60, flush=True)
        traceback.print_exc()
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nIndexing interrupted by user", flush=True)
        sys.exit(1)
