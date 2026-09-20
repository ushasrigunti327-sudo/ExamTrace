import sqlite3
from datetime import datetime
from models.database import get_db_connection


def save_evidence(session_id, event_type, image_path, description=""):
    """
    Save an evidence record linked to a session.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evidence (session_id, event_type, description, image_path, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (
        session_id,
        event_type,
        description,
        image_path,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    evidence_id = cursor.lastrowid
    conn.close()
    return evidence_id


def get_session_evidence(session_id):
    """
    Retrieve all evidence records for a specific session.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM evidence
        WHERE session_id = ?
        ORDER BY id ASC
    """, (session_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# Backward-compatibility alias
get_evidence_for_session = get_session_evidence
