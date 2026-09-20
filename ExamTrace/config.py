import os

class Config:
    SECRET_KEY = "examguard_secret_key"
    DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")
    EVIDENCE_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "evidence")
    REPORTS_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "reports")

    # Proctoring thresholds
    MAX_TAB_SWITCHES = 3
    MAX_FOCUS_LOSSES = 4
    FACE_ABSENCE_PROLONGED_SECONDS = 120  # 2 minutes continuous absence threshold

    # Event penalty weights (deducted from base 100)
    PENALTY_TAB_SWITCH = 5
    PENALTY_FOCUS_LOSS = 3
    PENALTY_COPY = 5
    PENALTY_PASTE = 5
    PENALTY_RIGHT_CLICK = 2
    PENALTY_SHORTCUT = 3
    PENALTY_FACE_MISSING = 5
    PENALTY_MULTIPLE_FACES = 10

    # Risk level classification thresholds
    # Score >= RISK_LOW_THRESHOLD -> LOW
    # Score >= RISK_MEDIUM_THRESHOLD -> MEDIUM
    # Score < RISK_MEDIUM_THRESHOLD -> HIGH
    RISK_LOW_THRESHOLD = 80
    RISK_MEDIUM_THRESHOLD = 50

    # AI Model
    GEMINI_MODEL = "gemini-3.6-flash"

    # Admin / Invigilator Credentials
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@examguard.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    # Streamlit Invigilator Dashboard URL
    STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")