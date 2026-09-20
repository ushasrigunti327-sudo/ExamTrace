from datetime import datetime
from models.database import get_db_connection


def log_browser_event(session_id, event):

    conn = get_db_connection()

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO browser_logs(

        session_id,
        event_type,
        event_time

    )

    VALUES(?,?,?)

    """,(

        session_id,
        event,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ))

    conn.commit()

    conn.close()