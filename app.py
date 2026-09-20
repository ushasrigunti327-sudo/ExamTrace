import os
import sys
import socket
import subprocess
from flask import Flask, render_template
from models.database import create_tables
from routes.auth import auth

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Create Database Tables
create_tables()

# Register Blueprint
app.register_blueprint(auth)


def ensure_streamlit_running():
    """Ensure Streamlit dashboard process is active on port 8501."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        res = sock.connect_ex(('127.0.0.1', 8501))
        sock.close()
        if res != 0:
            print("[INFO] Starting Streamlit Invigilator Dashboard on port 8501...")
            cmd = [
                sys.executable, "-m", "streamlit", "run", "streamlit_dashboard.py",
                "--server.port=8501", "--server.headless=true"
            ]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("[WARNING] Could not auto-start Streamlit:", e)


# Check Streamlit on app startup
ensure_streamlit_running()


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
