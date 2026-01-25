"""
Database module for storing RunArtifacts.

Supports both SQLite (local development) and PostgreSQL (Vercel production).
Uses DATABASE_URL environment variable to detect which database to use.
"""

import os
import json
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse


# Check for PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")

if DATABASE_URL:
    # PostgreSQL mode
    import psycopg2
    from psycopg2.extras import RealDictCursor
    USE_POSTGRES = True
    print("✅ Using PostgreSQL database")
else:
    # SQLite mode (local development)
    import sqlite3
    USE_POSTGRES = False
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'run_history.db')
    print("✅ Using SQLite database (local)")


def get_postgres_connection():
    """Get PostgreSQL connection."""
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn


def get_sqlite_connection():
    """Get SQLite connection."""
    return sqlite3.connect(DATABASE_PATH)


def init_db():
    """Initialize the database with required tables."""
    if USE_POSTGRES:
        conn = get_postgres_connection()
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
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS run_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_id ON run_artifacts(user_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_run_id ON run_artifacts(run_id)
        ''')
        
        conn.commit()
        conn.close()
    
    print("✅ Database initialized")


def save_run_artifact(artifact: dict, user_id: str = None) -> str:
    """Save a RunArtifact to the database."""
    run_id = artifact.get('run_id')
    input_data = artifact.get('input', {})
    final_data = artifact.get('final', {})
    timestamps = artifact.get('timestamps', {})
    
    params = (
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
    )
    
    if USE_POSTGRES:
        conn = get_postgres_connection()
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
        ''', params)
        
        conn.commit()
        cursor.close()
        conn.close()
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO run_artifacts (
                run_id, user_id, input_grade, input_topic,
                attempts_json, final_status, final_content_json,
                final_tags_json, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', params)
        
        conn.commit()
        conn.close()
    
    print(f"💾 Saved run artifact: {run_id}")
    return run_id


def get_run_artifact(run_id: str) -> Optional[dict]:
    """Retrieve a RunArtifact by run_id."""
    if USE_POSTGRES:
        conn = get_postgres_connection()
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
        return _dict_to_artifact(row)
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT run_id, user_id, input_grade, input_topic,
                   attempts_json, final_status, final_content_json,
                   final_tags_json, started_at, finished_at
            FROM run_artifacts WHERE run_id = ?
        ''', (run_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        return _row_to_artifact(row)


def get_history(user_id: str = None, limit: int = 50) -> List[dict]:
    """Retrieve run history, optionally filtered by user_id."""
    if USE_POSTGRES:
        conn = get_postgres_connection()
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
        
        return [_dict_to_artifact(row) for row in rows]
    else:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT run_id, user_id, input_grade, input_topic,
                       attempts_json, final_status, final_content_json,
                       final_tags_json, started_at, finished_at
                FROM run_artifacts 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        else:
            cursor.execute('''
                SELECT run_id, user_id, input_grade, input_topic,
                       attempts_json, final_status, final_content_json,
                       final_tags_json, started_at, finished_at
                FROM run_artifacts 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [_row_to_artifact(row) for row in rows]


def _row_to_artifact(row) -> dict:
    """Convert a SQLite row tuple to a RunArtifact dictionary."""
    return {
        'run_id': row[0],
        'user_id': row[1],
        'input': {
            'grade': row[2],
            'topic': row[3]
        },
        'attempts': json.loads(row[4]) if row[4] else [],
        'final': {
            'status': row[5],
            'content': json.loads(row[6]) if row[6] else None,
            'tags': json.loads(row[7]) if row[7] else None
        } if row[5] else None,
        'timestamps': {
            'started_at': row[8],
            'finished_at': row[9]
        }
    }


def _dict_to_artifact(row: dict) -> dict:
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


# Initialize database on import
init_db()
