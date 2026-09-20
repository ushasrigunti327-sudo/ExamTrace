from models.database import get_db_connection

def register_candidate(username, email, password, photo):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO candidates (username, email, password, photo)
        VALUES (?, ?, ?, ?)
    """, (username, email, password, photo))

    conn.commit()
    conn.close()


def email_exists(email):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates WHERE email=?", (email,))
    user = cursor.fetchone()

    conn.close()

    return user is not None


def get_candidate(email):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates WHERE email=?", (email,))
    user = cursor.fetchone()

    conn.close()

    return user