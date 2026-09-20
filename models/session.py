from models.database import get_db_connection
from datetime import datetime


def create_exam_session(candidate_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sessions(candidate_id, status, start_time)
        VALUES (?, ?, ?)
    """, (
        candidate_id,
        "Active",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id


def update_exam_session(
    candidate_id,
    status="Completed",
    integrity_score=100,
    risk_level="Low",
    face_presence_ratio=100.0,
    face_absent_duration=0,
    ai_summary=""
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET
            status = ?,
            end_time = ?,
            integrity_score = ?,
            risk_level = ?,
            face_presence_ratio = ?,
            face_absent_duration = ?,
            ai_summary = ?
        WHERE id = (
            SELECT id
            FROM sessions
            WHERE candidate_id = ?
            AND status = 'Active'
            ORDER BY id DESC
            LIMIT 1
        )
    """, (
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        integrity_score,
        risk_level,
        face_presence_ratio,
        face_absent_duration,
        ai_summary,
        candidate_id
    ))

    conn.commit()
    conn.close()


def finalize_session(
    session_id,
    integrity_score=100,
    risk_level="Low",
    face_presence_ratio=100.0,
    face_absent_duration=0,
    ai_summary="",
    status="Completed"
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET
            status = ?,
            end_time = ?,
            integrity_score = ?,
            risk_level = ?,
            face_presence_ratio = ?,
            face_absent_duration = ?,
            ai_summary = ?
        WHERE id = ?
    """, (
        status,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        integrity_score,
        risk_level,
        face_presence_ratio,
        face_absent_duration,
        ai_summary,
        session_id
    ))

    conn.commit()
    conn.close()


def get_session_by_id(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sessions
        WHERE id = ?
    """, (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_session_start_time(candidate_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT start_time FROM sessions
        WHERE candidate_id = ? AND status = 'Active'
        ORDER BY id DESC LIMIT 1
    """, (candidate_id,))

    row = cursor.fetchone()
    conn.close()

    return row["start_time"] if row else None


def get_candidate_sessions(candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM sessions
        WHERE candidate_id = ?
        ORDER BY id DESC
    """, (candidate_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows