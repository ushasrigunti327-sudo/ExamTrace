from models.database import get_db_connection
from datetime import datetime


def log_event(session_id, event_type):

    if session_id is None:
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO face_logs(
            session_id,
            event_type,
            event_time
        )
        VALUES(?,?,?)
    """, (
        session_id,
        event_type,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()