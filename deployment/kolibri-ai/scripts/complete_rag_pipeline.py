#!/usr/bin/env python3
"""
Complete RAG pipeline: Generate embeddings and insert into PostgreSQL
Processes in small batches with progress tracking
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
BATCH_SIZE = 20  # Small batches to avoid rate limits

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

def generate_embeddings(texts):
    """Generate embeddings using Alibaba DashScope API"""
    headers = {
        "Authorization": f"Bearer {ALIBABA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": EMBEDDING_MODEL,
        "input": texts,
        "encoding_format": "float"
    }
    
    try:
        response = requests.post(ALIBABA_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return [item['embedding'] for item in data['data']]
    except Exception as e:
        print(f"Embedding API error: {e}", file=sys.stderr)
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
    print("Complete RAG Pipeline (Generate + Insert)")
    print("=" * 60)
    
    # Load chunks
    print(f"\n[1/3] Loading chunks from {CHUNKS_FILE}...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks)} chunks")
    
    # Load progress
    progress = load_progress()
    start_idx = progress["last_processed"]
    print(f"\n[2/3] Resuming from chunk {start_idx}")
    
    # Test connection
    print(f"\n[3/3] Testing PostgreSQL connection...")
    result = run_sql("SELECT 1")
    if result != "1":
        print(f"  ✗ Connection failed: {result}")
        return
    print("  ✓ Connected")
    
    # Process chunks in batches
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    inserted = progress["total_inserted"]
    
    print(f"\nProcessing {len(chunks) - start_idx} remaining chunks in batches of {BATCH_SIZE}...")
    
    for batch_start in range(start_idx, len(chunks), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(chunks))
        batch = chunks[batch_start:batch_end]
        batch_num = (batch_start // BATCH_SIZE) + 1
        
        try:
            # Extract texts for embedding
            texts = [chunk.get('text', chunk.get('content', '')) for chunk in batch]
            
            # Generate embeddings
            print(f"  Batch {batch_num}/{total_batches} (chunks {batch_start}-{batch_end-1})...", end=" ")
            embeddings = generate_embeddings(texts)
            
            if embeddings is None:
                print("✗ Failed to generate embeddings")
                progress["last_processed"] = batch_start
                progress["total_inserted"] = inserted
                save_progress(progress)
                time.sleep(5)  # Wait before retry
                continue
            
            # Insert each chunk with its embedding
            for i, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                sql = """
                    INSERT INTO rag_chunks 
                    (content, source, category, embedding)
                    VALUES (:content, :source, :category, :embedding::vector)
                """
                
                params = {
                    "content": chunk.get('text', chunk.get('content', '')),
                    "source": chunk.get('source', ''),
                    "category": chunk.get('category', ''),
                    "embedding": f"[{','.join(map(str, embedding))}]"
                }
                
                result = run_sql(sql, params)
                if result is not None:
                    inserted += 1
            
            print(f"✓ ({inserted} total)")
            
            # Save progress
            progress["last_processed"] = batch_end
            progress["total_inserted"] = inserted
            save_progress(progress)
            
            # Small delay to avoid rate limits
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print(f"\n\n  Interrupted! Saving progress at chunk {batch_start}...")
            progress["last_processed"] = batch_start
            progress["total_inserted"] = inserted
            save_progress(progress)
            break
        except Exception as e:
            print(f"  ✗ Error: {e}")
            progress["last_processed"] = batch_start
            progress["total_inserted"] = inserted
            save_progress(progress)
            time.sleep(5)
            continue
    
    print("\n" + "=" * 60)
    print(f"✓ Complete! Inserted {inserted} chunks")
    print("=" * 60)

if __name__ == "__main__":
    main()
