import sqlite3

DATABASE = "database.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # -----------------------------
    # Candidate Table
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            photo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------
    # Session Table
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Not Started',
            start_time TEXT,
            end_time TEXT,
            integrity_score INTEGER DEFAULT 100,
            FOREIGN KEY(candidate_id) REFERENCES candidates(id)
        )
    """)

    # Safe column additions for sessions table
    for col_def in [
        ("integrity_score", "INTEGER DEFAULT 100"),
        ("risk_level", "TEXT DEFAULT 'Low'"),
        ("face_presence_ratio", "REAL DEFAULT 100.0"),
        ("face_absent_duration", "INTEGER DEFAULT 0"),
        ("ai_summary", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE sessions ADD COLUMN {col_def[0]} {col_def[1]}")
        except sqlite3.OperationalError:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL,
        option4 TEXT NOT NULL,
        correct_answer TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS face_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        event_type TEXT,
        event_time TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS browser_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        event_type TEXT,
        event_time TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        event_type TEXT NOT NULL,
        description TEXT,
        image_path TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    """)
    conn.commit()
    conn.close()