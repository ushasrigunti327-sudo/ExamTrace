"""
Synthetic Data Generation Module for Analytics and Machine Learning.
Generates realistic multi-profile session records, logs, and behavioral data using Faker.
Profiles:
- Normal (Low Risk): High face presence (>95%), minimal/no browser violations, score 80-100.
- Moderate (Medium Risk): Moderate face presence (80-94%), some tab switches/focus losses, score 50-79.
- High Risk: Prolonged face absence (<80%), multiple faces, frequent tab switches, score <50.
"""

import random
from datetime import datetime, timedelta
from faker import Faker
from models.database import get_db_connection
from utils.scoring import evaluate_session_integrity

fake = Faker()


def ensure_sample_candidates(conn, count=5):
    """Ensure sample candidates exist in the database for session generation."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM candidates")
    candidates = cursor.fetchall()
    if not candidates:
        sample_users = [
            ("Alex Johnson", "alex.johnson@example.com", "password123", "default.png"),
            ("Priya Sharma", "priya.sharma@example.com", "password123", "default.png"),
            ("David Lee", "david.lee@example.com", "password123", "default.png"),
            ("Fatima Al-Sayed", "fatima.alsayed@example.com", "password123", "default.png"),
            ("Rahul Verma", "rahul.verma@example.com", "password123", "default.png"),
        ]
        for name, email, pwd, photo in sample_users:
            cursor.execute("""
                INSERT OR IGNORE INTO candidates (username, email, password, photo)
                VALUES (?, ?, ?, ?)
            """, (name, email, pwd, photo))
        conn.commit()
        cursor.execute("SELECT id FROM candidates")
        candidates = cursor.fetchall()
    return candidates


def generate_fake_sessions(count=30):
    """
    Generate synthetic examination sessions with realistic behavioral distributions
    and correlated face/browser log entries.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    candidates = ensure_sample_candidates(conn)
    candidate_ids = [c["id"] for c in candidates]

    profiles = ["normal", "moderate", "high_risk"]
    profile_weights = [0.60, 0.25, 0.15]

    for _ in range(count):
        candidate_id = random.choice(candidate_ids)
        profile = random.choices(profiles, weights=profile_weights, k=1)[0]

        # Exam timing (e.g. 30 minutes duration)
        start_dt = fake.date_time_between(start_date="-15d", end_date="now")
        duration_minutes = 30
        duration_seconds = duration_minutes * 60
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

        if profile == "normal":
            tab_switches = random.choices([0, 1], weights=[0.8, 0.2])[0]
            focus_losses = random.choices([0, 1], weights=[0.8, 0.2])[0]
            copy_attempts = 0
            paste_attempts = 0
            right_clicks = random.choices([0, 1], weights=[0.9, 0.1])[0]
            shortcuts = 0
            face_missing_count = random.choices([0, 1], weights=[0.85, 0.15])[0]
            multiple_face_count = 0
            face_absent_seconds = random.randint(0, 30) if face_missing_count > 0 else 0

        elif profile == "moderate":
            tab_switches = random.randint(1, 3)
            focus_losses = random.randint(1, 3)
            copy_attempts = random.choices([0, 1], weights=[0.7, 0.3])[0]
            paste_attempts = random.choices([0, 1], weights=[0.8, 0.2])[0]
            right_clicks = random.randint(0, 2)
            shortcuts = random.randint(0, 2)
            face_missing_count = random.randint(1, 3)
            multiple_face_count = random.choices([0, 1], weights=[0.8, 0.2])[0]
            face_absent_seconds = random.randint(30, 90)

        else:  # high_risk
            tab_switches = random.randint(4, 9)
            focus_losses = random.randint(3, 8)
            copy_attempts = random.randint(1, 4)
            paste_attempts = random.randint(1, 4)
            right_clicks = random.randint(1, 5)
            shortcuts = random.randint(2, 6)
            face_missing_count = random.randint(3, 8)
            multiple_face_count = random.randint(1, 4)
            face_absent_seconds = random.randint(120, 500)

        # Compute integrity metrics
        metrics = evaluate_session_integrity(
            tab_switches=tab_switches,
            focus_losses=focus_losses,
            face_missing_count=face_missing_count,
            multiple_face_count=multiple_face_count,
            right_clicks=right_clicks,
            copy_attempts=copy_attempts,
            paste_attempts=paste_attempts,
            shortcuts=shortcuts,
            duration_seconds=duration_seconds,
            face_absent_seconds=face_absent_seconds
        )

        status = "Completed" if metrics["risk_level"] != "High" or random.random() > 0.3 else "Terminated"

        # Insert session record
        cursor.execute("""
            INSERT INTO sessions (
                candidate_id, status, start_time, end_time,
                integrity_score, risk_level, face_presence_ratio,
                face_absent_duration, ai_summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            candidate_id,
            status,
            start_str,
            end_str,
            metrics["integrity_score"],
            metrics["risk_level"],
            metrics["face_presence_ratio"],
            metrics["face_absent_seconds"],
            f"Automated evaluation: {metrics['risk_level']} risk profile with score {metrics['integrity_score']}/100."
        ))
        session_id = cursor.lastrowid

        # Insert correlated browser logs
        for _ in range(tab_switches):
            offset = random.randint(60, duration_seconds - 60)
            log_time = (start_dt + timedelta(seconds=offset)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO browser_logs (session_id, event_type, event_time) VALUES (?, ?, ?)",
                           (session_id, "Tab Switch", log_time))

        for _ in range(focus_losses):
            offset = random.randint(60, duration_seconds - 60)
            log_time = (start_dt + timedelta(seconds=offset)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO browser_logs (session_id, event_type, event_time) VALUES (?, ?, ?)",
                           (session_id, "Focus Lost", log_time))

        for _ in range(copy_attempts):
            offset = random.randint(60, duration_seconds - 60)
            log_time = (start_dt + timedelta(seconds=offset)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO browser_logs (session_id, event_type, event_time) VALUES (?, ?, ?)",
                           (session_id, "Copy Attempt", log_time))

        for _ in range(right_clicks):
            offset = random.randint(60, duration_seconds - 60)
            log_time = (start_dt + timedelta(seconds=offset)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO browser_logs (session_id, event_type, event_time) VALUES (?, ?, ?)",
                           (session_id, "Right Click", log_time))

        for _ in range(shortcuts):
            offset = random.randint(60, duration_seconds - 60)
            log_time = (start_dt + timedelta(seconds=offset)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO browser_logs (session_id, event_type, event_time) VALUES (?, ?, ?)",
                           (session_id, "Keyboard Shortcut", log_time))

        # Insert correlated face logs
        for _ in range(face_missing_count):
            offset = random.randint(60, duration_seconds - 60)
            miss_time = (start_dt + timedelta(seconds=offset)).strftime("%Y-%m-%d %H:%M:%S")
            ret_time = (start_dt + timedelta(seconds=offset + 10)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO face_logs (session_id, event_type, event_time) VALUES (?, ?, ?)",
                           (session_id, "Face Missing", miss_time))
            cursor.execute("INSERT INTO face_logs (session_id, event_type, event_time) VALUES (?, ?, ?)",
                           (session_id, "Face Detected", ret_time))

        for _ in range(multiple_face_count):
            offset = random.randint(60, duration_seconds - 60)
            multi_time = (start_dt + timedelta(seconds=offset)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO face_logs (session_id, event_type, event_time) VALUES (?, ?, ?)",
                           (session_id, "Multiple Faces", multi_time))

    conn.commit()
    conn.close()
    print(f"Successfully generated {count} realistic synthetic examination sessions.")