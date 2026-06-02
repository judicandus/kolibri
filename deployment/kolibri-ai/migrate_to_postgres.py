#!/usr/bin/env python3
"""
Migration script: SQLite → PostgreSQL for Kolibri AI
Migrates conversations and messages tables
"""

import os
import json
import sqlite3
import asyncio
import asyncpg
from pathlib import Path

# Configuration
SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "/app/data/conversations.db")
POSTGRES_URL = os.environ.get("DATABASE_URL", "postgresql://kolibri_ai:KolibriAI2024Secure!@postgres-ai-service:5432/kolibri_ai")


async def create_postgres_tables(conn):
    """Create PostgreSQL tables with same schema as SQLite"""
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    
    await conn.execute("""
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
    
    # Create index for faster queries
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
        ON messages(conversation_id)
    """)
    
    print("✓ PostgreSQL tables created")


async def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    # Check if SQLite database exists
    if not Path(SQLITE_DB_PATH).exists():
        print(f"✗ SQLite database not found at {SQLITE_DB_PATH}")
        return
    
    print(f"Connecting to SQLite: {SQLITE_DB_PATH}")
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    
    print(f"Connecting to PostgreSQL: {POSTGRES_URL}")
    pg_conn = await asyncpg.connect(POSTGRES_URL)
    
    try:
        # Create tables
        await create_postgres_tables(pg_conn)
        
        # Migrate conversations
        print("\nMigrating conversations...")
        conversations = sqlite_conn.execute("SELECT * FROM conversations").fetchall()
        print(f"  Found {len(conversations)} conversations")
        
        for conv in conversations:
            await pg_conn.execute(
                """
                INSERT INTO conversations (id, title, created_at, updated_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
                """,
                conv['id'], conv['title'], conv['created_at'], conv['updated_at']
            )
        print(f"  ✓ Migrated {len(conversations)} conversations")
        
        # Migrate messages
        print("\nMigrating messages...")
        messages = sqlite_conn.execute("SELECT * FROM messages").fetchall()
        print(f"  Found {len(messages)} messages")
        
        for msg in messages:
            await pg_conn.execute(
                """
                INSERT INTO messages (id, conversation_id, role, content, rag_sources, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO NOTHING
                """,
                msg['id'], msg['conversation_id'], msg['role'], 
                msg['content'], msg['rag_sources'], msg['created_at']
            )
        print(f"  ✓ Migrated {len(messages)} messages")
        
        print("\n✓ Migration completed successfully!")
        
    finally:
        sqlite_conn.close()
        await pg_conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Kolibri AI: SQLite → PostgreSQL Migration")
    print("=" * 60)
    asyncio.run(migrate_data())
