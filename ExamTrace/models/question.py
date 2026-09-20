from models.database import get_db_connection


def get_random_questions(limit=10):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM questions
        ORDER BY RANDOM()
        LIMIT ?
    """, (limit,))

    questions = cursor.fetchall()

    conn.close()

    return questions