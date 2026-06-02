#!/usr/bin/env python3
"""
Enhanced RAG pipeline with error handling and text length management
"""

import json
import subprocess
import sys
import time
from pathlib import Path
import requests

CHUNKS_FILE = Path("/tmp/all_chunks.json")
PROGRESS_FILE = Path("/tmp/rag_progress.json")
NAMESPACE = "kolibri-ai"
POSTGRES_POD = "postgres-ai-684bf6955b-pl88h"
DB_NAME = "kolibri_ai"
DB_USER = "kolibri_ai"

# Alibaba DashScope API (Singapore endpoint)
ALIBABA_API_KEY = "sk-ws-H.HRPEHI.bXmQ.MEYCIQDqkvzLHf7-M51gFuRuT5AC69mJ6NKqHAZ9nBIVOsLQ2AIhALBcnE7A913rdLCKIXCAMvvy72EVNlgMcNrKLzu0anHY"
ALIBABA_API_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/embeddings"
EMBEDDING_MODEL = "text-embedding-v3"
BATCH_SIZE = 10  # Smaller batches
MAX_TOKENS = 8000  # Max tokens per request
MAX_TEXT_LENGTH = 6000  # Max characters per text

def run_sql(sql, params=None):
    """Execute SQL in PostgreSQL pod"""
    cmd = f"kubectl exec -n {NAMESPACE} {POSTGRES_POD} -- psql -U {DB_USER} -d {DB_NAME} -t -A -c"

    if params:
        escaped_sql = sql.replace("'", "''")
        for k, v in params.items():
            if isinstance(v, str):
                escaped_v = v.replace("'", "''")
                escaped_sql = escaped_sql.replace(f":{k}", f"'{escaped_v}'")
            else:
                escaped_sql = escaped_sql.replace(f":{k}", str(v))
        full_cmd = f"{cmd} \"{escaped_sql}\""
    else:
        full_cmd = f"{cmd} \"{sql}\""

    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"SQL Error: {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip()

def truncate_text(text, max_length=MAX_TEXT_LENGTH):
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length]

def generate_embeddings(texts, retry_count=3):
    """Generate embeddings using Alibaba DashScope API with retry"""
    headers = {
        "Authorization": f"Bearer {ALIBABA_API_KEY}",
        "Content-Type": "application/json"
    }

    # Truncate texts if too long
    truncated_texts = [truncate_text(text) for text in texts]

    payload = {
        "model": EMBEDDING_MODEL,
        "input": truncated_texts,
        "encoding_format": "float"
    }

    for attempt in range(retry_count):
        try:
            response = requests.post(ALIBABA_API_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 400:
                error_detail = response.json()
                print(f"API Error 400: {json.dumps(error_detail, indent=2)}", file=sys.stderr)
                return None
            
            response.raise_for_status()
            data = response.json()
            return [item['embedding'] for item in data['data']]
            
        except requests.exceptions.RequestException as e:
            if attempt < retry_count - 1:
                print(f"Attempt {attempt + 1} failed, retrying...", file=sys.stderr)
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Embedding API error after {retry_count} attempts: {e}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return None

def load_progress():
    """Load progress from file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"last_processed": 0, "total_inserted": 0}

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def main():
    print("=" * 60)
    print("Enhanced RAG Pipeline (Generate + Insert)")
    print("=" * 60)

    # Load chunks
    print(f"\n[1/3] Loading chunks from {CHUNKS_FILE}...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks)} chunks")

    # Show sample chunk
    print(f"\n  Sample chunk (first 200 chars):")
    print(f"  {chunks[0].get('text', '')[:200]}...")

    # Load progress
    progress = load_progress()
    start_idx = progress["last_processed"]
    print(f"\n[2/3] Resuming from chunk {start_idx}")

    # Test connection
    print(f"\n[3/3] Testing PostgreSQL connection...")
    result = run_sql("SELECT 1")
    if result == "1":
        print("  ✓ Connected to PostgreSQL")
    else:
        print("  ✗ Connection failed")
        return

    # Process chunks
    total_inserted = progress["total_inserted"]
    failed_chunks = []

    for i in range(start_idx, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\nProcessing batch {batch_num}/{total_batches} (chunks {i}-{i+len(batch)-1})...")

        # Extract texts
        texts = [chunk.get('text', '') for chunk in batch]

        # Generate embeddings
        print(f"  Generating embeddings...")
        embeddings = generate_embeddings(texts)

        if embeddings is None:
            print(f"  ✗ Failed to generate embeddings, skipping batch")
            failed_chunks.extend(range(i, i + len(batch)))
            continue

        print(f"  ✓ Generated {len(embeddings)} embeddings")

        # Insert into database
        print(f"  Inserting into database...")
        batch_inserted = 0

        for chunk, embedding in zip(batch, embeddings):
            sql = """
                INSERT INTO rag_chunks (content, embedding, category, source)
                VALUES (:content, :embedding, :category, :source)
            """

            embedding_str = "[" + ",".join(map(str, embedding)) + "]"

            params = {
                "content": chunk.get('text', ''),
                "embedding": embedding_str,
                "category": chunk.get('category', ''),
                "source": chunk.get('source', '')
            }

            result = run_sql(sql, params)
            if result is not None:
                batch_inserted += 1

        total_inserted += batch_inserted
        print(f"  ✓ Inserted {batch_inserted}/{len(batch)} chunks (total: {total_inserted})")

        # Save progress
        progress["last_processed"] = i + len(batch)
        progress["total_inserted"] = total_inserted
        save_progress(progress)

        # Rate limiting
        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 60)
    print(f"Pipeline Complete!")
    print(f"  Total chunks processed: {len(chunks)}")
    print(f"  Successfully inserted: {total_inserted}")
    print(f"  Failed chunks: {len(failed_chunks)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
