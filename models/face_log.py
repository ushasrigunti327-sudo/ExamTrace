from models.database import get_db_connection
from datetime import datetime

from models.database import get_db_connection
from datetime import datetime


def save_face_log(session_id, event):

    conn = get_db_connection()
    cursor = conn.cursor()

    # Prevent duplicate consecutive logs
    cursor.execute("""
        SELECT event_type
        FROM face_logs
        WHERE session_id=?
        ORDER BY id DESC
        LIMIT 1
    """, (session_id,))

    last = cursor.fetchone()

    if last and last["event_type"] == event:
        conn.close()
        return

    cursor.execute("""
        INSERT INTO face_logs(
            session_id,
            event_type,
            event_time
        )
        VALUES(?,?,?)
    """, (
        session_id,
        event,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

def get_session_logs(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM face_logs
        WHERE session_id = ?
        ORDER BY id DESC
    """, (session_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows