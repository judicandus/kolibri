#!/usr/bin/env python3
"""
Generate embeddings and insert into PostgreSQL incrementally
Processes in small batches to avoid losing progress on errors
"""

import httpx
import psycopg2
import json
from pathlib import Path
import time

# Configuration
CHUNKS_FILE = Path(__file__).parent.parent / "corpus" / "processed" / "all_chunks.json"
PROGRESS_FILE = Path(__file__).parent.parent / "data" / "embedding_progress.json"
POSTGRES_URL = "postgresql://kolibri_ai:KolibriAI2024Secure!@localhost:5432/kolibri_ai"
ALIBABA_API_KEY = "sk-ws-H.HRPEHI.bXmQ.MEYCIQDqkvzLHf7-M51gFuRuT5AC69mJ6NKqHAZ9nBIVOsLQ2AIhALBcnE7A913rdLCKIXCAMvvy72EVNlgMcNrKLzu0anHY"
ALIBABA_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
EMBEDDING_MODEL = "text-embedding-v3"
BATCH_SIZE = 10

def load_progress():
    """Load progress from file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"last_processed": 0, "total_inserted": 0}

def save_progress(progress):
    """Save progress to file"""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def generate_embeddings_batch(client, texts):
    """Generate embeddings for a batch of texts"""
    response = client.post(
        f"{ALIBABA_BASE_URL}/embeddings",
        headers={
            "Authorization": f"Bearer {ALIBABA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": EMBEDDING_MODEL,
            "input": texts
        },
        timeout=60.0
    )
    
    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text[:200]}")
    
    data = response.json()
    return data['data'][0]['embedding']

def main():
    print("=" * 60)
    print("Incremental Embedding Generator and Inserter")
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
    
    # Connect to PostgreSQL
    print(f"\n[3/3] Connecting to PostgreSQL...")
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    print("  ✓ Connected")
    
    # Process chunks in batches
    client = httpx.Client()
    total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    inserted = progress["total_inserted"]
    
    print(f"\nProcessing {len(chunks) - start_idx} remaining chunks...")
    
    for i in range(start_idx, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        try:
            print(f"  Batch {batch_num}/{total_batches} (chunks {i}-{i+len(batch)-1})...", end=" ")
            
            # Generate embeddings
            for j, chunk in enumerate(batch):
                try:
                    embedding = generate_embeddings_batch(client, [chunk['content']])
                    
                    # Insert into database
                    cursor.execute("""
                        INSERT INTO rag_chunks 
                        (chunk_id, source_type, source_path, content, category, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s::vector)
                        ON CONFLICT (chunk_id, source_type) 
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            category = EXCLUDED.category,
                            embedding = EXCLUDED.embedding
                    """, (
                        chunk.get('chunk_id', f'chunk_{i+j}'),
                        chunk.get('source_type', 'unknown'),
                        chunk.get('source_path', ''),
                        chunk['content'],
                        chunk.get('category', ''),
                        embedding
                    ))
                    
                    inserted += 1
                    
                except Exception as e:
                    print(f"\n    ✗ Error on chunk {i+j}: {e}")
                    continue
            
            conn.commit()
            print(f"✓ ({inserted} total)")
            
            # Save progress
            progress["last_processed"] = i + len(batch)
            progress["total_inserted"] = inserted
            save_progress(progress)
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n\n  Interrupted! Saving progress...")
            progress["last_processed"] = i
            progress["total_inserted"] = inserted
            save_progress(progress)
            break
        except Exception as e:
            print(f"\n  ✗ Batch error: {e}")
            conn.rollback()
            progress["last_processed"] = i
            progress["total_inserted"] = inserted
            save_progress(progress)
            continue
    
    cursor.close()
    conn.close()
    client.close()
    
    print("\n" + "=" * 60)
    print(f"✓ Complete! Inserted {inserted} chunks")
    print("=" * 60)

if __name__ == "__main__":
    main()
