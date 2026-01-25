"""
Database module for storing RunArtifacts.
Uses PostgreSQL only (via psycopg2).
"""

import os
import json
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set!")

print(f"✅ Using PostgreSQL database")


def get_connection():
    """Get PostgreSQL connection."""
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn


def init_db():
    """Initialize the database with required tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS run_artifacts (
            id SERIAL PRIMARY KEY,
            run_id TEXT UNIQUE NOT NULL,
            user_id TEXT,
            input_grade INTEGER NOT NULL,
            input_topic TEXT NOT NULL,
            attempts_json TEXT NOT NULL,
            final_status TEXT,
            final_content_json TEXT,
            final_tags_json TEXT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_id ON run_artifacts(user_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_run_id ON run_artifacts(run_id)
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Database initialized")


def save_run_artifact(artifact: dict, user_id: str = None) -> str:
    """Save a RunArtifact to the database."""
    run_id = artifact.get('run_id')
    input_data = artifact.get('input', {})
    final_data = artifact.get('final', {})
    timestamps = artifact.get('timestamps', {})
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO run_artifacts (
            run_id, user_id, input_grade, input_topic,
            attempts_json, final_status, final_content_json,
            final_tags_json, started_at, finished_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (run_id) DO UPDATE SET
            attempts_json = EXCLUDED.attempts_json,
            final_status = EXCLUDED.final_status,
            final_content_json = EXCLUDED.final_content_json,
            final_tags_json = EXCLUDED.final_tags_json,
            finished_at = EXCLUDED.finished_at
    ''', (
        run_id,
        user_id,
        input_data.get('grade'),
        input_data.get('topic'),
        json.dumps(artifact.get('attempts', [])),
        final_data.get('status') if final_data else None,
        json.dumps(final_data.get('content')) if final_data and final_data.get('content') else None,
        json.dumps(final_data.get('tags')) if final_data and final_data.get('tags') else None,
        timestamps.get('started_at'),
        timestamps.get('finished_at')
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"💾 Saved run artifact: {run_id}")
    return run_id


def get_run_artifact(run_id: str) -> Optional[dict]:
    """Retrieve a RunArtifact by run_id."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute('''
        SELECT run_id, user_id, input_grade, input_topic,
               attempts_json, final_status, final_content_json,
               final_tags_json, started_at, finished_at
        FROM run_artifacts WHERE run_id = %s
    ''', (run_id,))
    
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not row:
        return None
    return _row_to_artifact(row)


def get_history(user_id: str = None, limit: int = 50) -> List[dict]:
    """Retrieve run history, optionally filtered by user_id."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if user_id:
        cursor.execute('''
            SELECT run_id, user_id, input_grade, input_topic,
                   attempts_json, final_status, final_content_json,
                   final_tags_json, started_at, finished_at
            FROM run_artifacts 
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        ''', (user_id, limit))
    else:
        cursor.execute('''
            SELECT run_id, user_id, input_grade, input_topic,
                   attempts_json, final_status, final_content_json,
                   final_tags_json, started_at, finished_at
            FROM run_artifacts 
            ORDER BY created_at DESC
            LIMIT %s
        ''', (limit,))
    
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [_row_to_artifact(row) for row in rows]


def _row_to_artifact(row: dict) -> dict:
    """Convert a PostgreSQL dict row to a RunArtifact dictionary."""
    return {
        'run_id': row['run_id'],
        'user_id': row['user_id'],
        'input': {
            'grade': row['input_grade'],
            'topic': row['input_topic']
        },
        'attempts': json.loads(row['attempts_json']) if row['attempts_json'] else [],
        'final': {
            'status': row['final_status'],
            'content': json.loads(row['final_content_json']) if row['final_content_json'] else None,
            'tags': json.loads(row['final_tags_json']) if row['final_tags_json'] else None
        } if row['final_status'] else None,
        'timestamps': {
            'started_at': row['started_at'],
            'finished_at': row['finished_at']
        }
    }


# Track if database has been initialized
_db_initialized = False

def ensure_db_initialized():
    """Ensure database is initialized (call this before any DB operation)."""
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True
