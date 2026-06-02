#!/usr/bin/env python3
"""
Insert pre-generated chunks into PostgreSQL RAG database
"""

import psycopg2
from pathlib import Path
import json

# Configuration
CHUNKS_FILE = Path(__file__).parent.parent / "corpus" / "processed" / "all_chunks.json"
POSTGRES_URL = "postgresql://kolibri_ai:KolibriAI2024Secure!@localhost:5432/kolibri_ai"

def main():
    print("=" * 60)
    print("Inserting chunks into PostgreSQL")
    print("=" * 60)
    
    # Load chunks
    print(f"\n[1/3] Loading chunks from {CHUNKS_FILE}...")
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks)} chunks")
    
    # Connect to PostgreSQL
    print(f"\n[2/3] Connecting to PostgreSQL...")
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    print("  ✓ Connected")
    
    # Insert chunks
    print(f"\n[3/3] Inserting chunks into database...")
    batch_size = 100
    inserted = 0
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        for chunk in batch:
            try:
                # Check if chunk already exists
                cursor.execute("""
                    SELECT id FROM rag_chunks 
                    WHERE chunk_id = %s AND source_type = %s
                """, (chunk.get('chunk_id', ''), chunk.get('source_type', '')))
                
                if cursor.fetchone():
                    # Update existing
                    cursor.execute("""
                        UPDATE rag_chunks 
                        SET content = %s, source_path = %s, category = %s, 
                            embedding = %s::vector
                        WHERE chunk_id = %s AND source_type = %s
                    """, (
                        chunk['content'],
                        chunk.get('source_path', ''),
                        chunk.get('category', ''),
                        chunk['embedding'],
                        chunk.get('chunk_id', ''),
                        chunk.get('source_type', '')
                    ))
                else:
                    # Insert new
                    cursor.execute("""
                        INSERT INTO rag_chunks 
                        (chunk_id, source_type, source_path, content, category, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s::vector)
                    """, (
                        chunk.get('chunk_id', ''),
                        chunk.get('source_type', ''),
                        chunk.get('source_path', ''),
                        chunk['content'],
                        chunk.get('category', ''),
                        chunk['embedding']
                    ))
                
                inserted += 1
                
            except Exception as e:
                print(f"  ✗ Error inserting chunk: {e}")
                continue
        
        conn.commit()
        print(f"  ✓ Inserted {inserted}/{len(chunks)} chunks")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✓ Complete! Inserted {inserted} chunks")
    print("=" * 60)

if __name__ == "__main__":
    main()
