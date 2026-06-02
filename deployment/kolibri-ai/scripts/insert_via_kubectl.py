#!/usr/bin/env python3
"""
Insert embeddings into PostgreSQL using kubectl exec
"""

import json
import subprocess
import sys
from pathlib import Path

CHUNKS_FILE = Path("/tmp/all_chunks.json")
PROGRESS_FILE = Path("/tmp/embedding_progress.json")
NAMESPACE = "kolibri-ai"
POSTGRES_POD = "postgres-ai-684bf6955b-pl88h"
DB_NAME = "kolibri_ai"
DB_USER = "kolibri_ai"

def run_sql(sql, params=None):
    """Execute SQL in PostgreSQL pod"""
    cmd = f"kubectl exec -n {NAMESPACE} {POSTGRES_POD} -- psql -U {DB_USER} -d {DB_NAME} -t -A -c"
    
    if params:
        # Escape single quotes in parameters
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

def load_progress():
    """Load progress from file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"last_processed": 0, "total_inserted": 0}

def save_progress(progress):
    """Save progress to file"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def main():
    print("=" * 60)
    print("Embedding Inserter (kubectl exec mode)")
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
    
    # Insert chunks
    print(f"\nProcessing {len(chunks) - start_idx} remaining chunks...")
    inserted = progress["total_inserted"]
    
    for i in range(start_idx, len(chunks)):
        chunk = chunks[i]
        
        try:
            # Insert chunk with embedding
            sql = """
                INSERT INTO rag_chunks 
                (content, source, category, embedding)
                VALUES (:content, :source, :category, :embedding::vector)
            """
            
            params = {
                "content": chunk.get('text', chunk.get('content', '')),
                "source": chunk.get('source', ''),
                "category": chunk.get('category', ''),
                "embedding": f"[{','.join(map(str, chunk.get('embedding', [])))}]"
            }
            
            run_sql(sql, params)
            inserted += 1
            
            # Print progress every 100 chunks
            if (i + 1) % 100 == 0:
                print(f"  ✓ Processed {i + 1}/{len(chunks)} chunks ({inserted} inserted)")
                progress["last_processed"] = i + 1
                progress["total_inserted"] = inserted
                save_progress(progress)
                
        except KeyboardInterrupt:
            print(f"\n\n  Interrupted! Saving progress at chunk {i}...")
            progress["last_processed"] = i
            progress["total_inserted"] = inserted
            save_progress(progress)
            break
        except Exception as e:
            print(f"  ✗ Error on chunk {i}: {e}")
            progress["last_processed"] = i
            progress["total_inserted"] = inserted
            save_progress(progress)
            continue
    
    print("\n" + "=" * 60)
    print(f"✓ Complete! Inserted {inserted} chunks")
    print("=" * 60)

if __name__ == "__main__":
    main()
