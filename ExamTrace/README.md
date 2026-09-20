# 🛡️ ExamTrace — Online Exam Monitoring & Integrity Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.2%2B-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.7%2B-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2%2B-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.2%2B-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Database](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)

> **A full-stack, AI-driven proctoring and integrity analytics platform combining OpenCV computer vision, browser event interception, rule-based risk evaluation, LangChain Google Gemini summarization, and unsupervised machine learning clustering for fair and evidence-backed online assessments.**

---

## 📑 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Configuration & Environment Variables](#-configuration--environment-variables)
- [Running the Platform](#-running-the-platform)
- [User Credentials & Portals](#-user-credentials--portals)
- [Proctoring Rules & Scoring Engine](#-proctoring-rules--scoring-engine)
- [Testing & Verification](#-testing--verification)
- [Project Documentation](#-project-documentation)

---

## 📌 Overview

Traditional online examination systems often struggle to balance candidate trust with academic rigor. **ExamTrace** bridges this gap by providing an unobtrusive, transparent, and evidence-centric exam monitoring solution:

- **Evidence-Based, Not Punitive**: Rather than terminating an exam on first infraction, ExamTrace continuously tracks presence and behavioral signals, logs timestamped evidence frames, and calculates an objective **Integrity Score (0–100)**.
- **AI-Powered Proctoring Insights**: Leverages **LangChain Core** and **Google Gemini** to generate factual, natural-language executive summaries of candidate sessions with built-in offline fallback.
- **Cohort-Level Data Science**: Invigilators gain deep visibility through **K-Means Behavioral Clustering**, Kernel Density Estimation (KDE) score distributions, and risk heatmaps across cohorts.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Candidate_Portal [Candidate Interface (Flask + Vanilla JS)]
        A[Candidate Registration & Photo Capture] --> B[Authentication & Dashboard]
        B --> C[Live Examination Window]
        C -->|Webcam Video Stream| D[OpenCV Haar Cascade Face Detector]
        C -->|Tab Switch / Focus / Keystrokes| E[Browser Event Logger]
    end

    subgraph Core_Engine [Proctoring & Scoring Engine]
        D --> F[Live Exam Monitor]
        E --> F
        F --> G[Incident Snapshot Capture]
        F --> H[Algorithmic Integrity Scoring Module]
    end

    subgraph Storage [Persistence Layer]
        G -->|JPG Evidence with Path Security| I[(SQLite Database & File System)]
        H -->|Scores, Ratios, Risk Levels| I
    end

    subgraph AI_Analytics [AI & Data Science Modules]
        I --> J[LangChain + Gemini Integrity Agent]
        I --> K[Pandas ETL Pipeline & StandardScaler]
        K --> L[K-Means Behavioral Clustering & Heatmaps]
    end

    subgraph Invigilator_Portals [Invigilator & Admin Hub]
        J --> M[Automated PDF / AI Report Generation]
        L --> N[Streamlit Invigilator Dashboard]
        I --> O[Flask Admin Review Portal]
        N --> P[Enriched CSV / JSON Dataset Exports]
        O --> P
    end
```

---

## 🚀 Key Features

### 1. 📷 Computer Vision & Face Presence Monitoring
- **Real-Time Face Detection**: Powered by OpenCV Haar Cascade with histogram equalization for robust detection under varied lighting.
- **Absence Tracking**: Detects when candidate leaves webcam view; records accumulated and continuous absent duration.
- **Multiple Faces Detection**: Flags if unauthorized persons enter the webcam frame.
- **Automated Evidence Snapshots**: Takes timestamped JPG snapshots whenever high-severity events occur and stores them safely in session-isolated directories.

### 2. 🌐 Client-Side Browser Security
- **Tab & Window Focus Tracking**: Intercepts `visibilitychange` and `blur`/`focus` events to log tab switches and window un-focusing.
- **Input & Shortcut Guard**: Restricts context menus (right-click), copy, paste, and disallowed keyboard shortcuts (`Alt+Tab`, `Ctrl+C`, `Ctrl+V`, `Ctrl+T`, `F12`).
- **Asynchronous Telemetry**: Sends telemetry logs to backend endpoints with millisecond precision without interrupting candidate flow.

### 3. ⚖️ Algorithmic Integrity Scoring
- **Dynamic Risk Evaluation**: Calculates an integrity score from 0 to 100 based on weighted violation deductions.
- **Face Presence Ratio (FPR)**:
  $$\text{Face Presence Ratio (\%)} = \left( \frac{\text{Duration} - \text{Absent Duration}}{\text{Duration}} \right) \times 100$$
- **Standardized Risk Bands**:
  - 🟢 **Low Risk** ($\ge 80$)
  - 🟡 **Medium Risk** ($50 \le \text{Score} < 80$)
  - 🔴 **High Risk** ($< 50$)

### 4. 🤖 LangChain AI Integrity Summary Agent
- Converts raw logs, metrics, and incident counts into a structured natural-language evaluation.
- Highlights specific behavioral concerns and provides objective recommendations.
- **Deterministic Offline Fallback**: Generates instant structured summaries even without internet or when API rate limits are reached.

### 5. 📊 Data Science & Machine Learning Hub
- **K-Means Behavioral Clustering**: Clusters candidates into behavioral profiles based on 7 normalized dimensions (`Integrity Score`, `Face Presence Ratio`, `Tab Switches`, `Focus Losses`, `Copy/Paste`, `Face Missing`, `Multiple Faces`).
- **Visual Analytics**: Interactive event violation heatmaps, score distributions with KDE curves, and risk breakdown donut charts.
- **Multi-Format Data Exports**: Export candidate cohorts in enriched **CSV**, **JSON**, and downloadable **PDF** audit reports.

---

## 🧰 Technology Stack

| Domain | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+, Flask | Application routing, Blueprint modularization, REST APIs, session management |
| **Computer Vision** | OpenCV (`cv2`), Haar Cascade | Webcam processing, facial detection, incident snapshot capture |
| **AI & LLM Integration** | LangChain Core, `ChatGoogleGenerativeAI` | Natural language proctoring summaries powered by Google Gemini |
| **Data Science & ML** | Pandas, NumPy, Scikit-learn | Feature engineering, normalization (`StandardScaler`), K-Means clustering |
| **Data Visualization** | Matplotlib, Seaborn | Distribution plots, correlation heatmaps, cohort risk donut charts |
| **Dashboarding** | Streamlit | Dedicated live invigilator portal and deep-dive session analytics |
| **Database** | SQLite3 | Local relational storage for candidates, exam sessions, logs, and evidence |
| **PDF Reporting** | ReportLab | Generation of official academic & integrity audit PDF certificates |
| **Synthetic Data & Utils**| Faker, Python-dotenv | Multi-profile synthetic test datasets, environment configuration |

---

## 📂 Project Structure

```text
ExamTrace/
├── app.py                          # Flask application entry point & Streamlit auto-launcher
├── config.py                       # Global configuration, proctoring thresholds & penalty weights
├── database.db                     # SQLite database file
├── generate_data.py                # Synthetic candidate data generator runner
├── haarcascade_frontalface_default.xml # OpenCV Haar Cascade classifier model
├── insert_questions.py             # Script to populate SQLite database with test questions
├── requirements.txt                # Python package dependencies
├── streamlit_dashboard.py          # Streamlit Invigilator Dashboard & Analytics Suite
├── test_milestone3.py              # Automated validation test suite
│
├── Docs/                           # Project specifications, defect trackers & agile plans
│   ├── EXAMTRACE Generic Document.pdf
│   ├── ExamTrace_Agile_Document.pdf
│   ├── ExamTrace_Agile_Report.xlsx
│   ├── ExamTrace_Defect_Tracker_Normal_Excel_Style.xlsx
│   └── ExamTrace_Unit_Test_Plan.xlsx
│
├── models/                         # Database schema and CRUD models
│   ├── candidate.py                # Candidate registration, lookup, authentication
│   ├── database.py                 # SQLite table initialization & connection helpers
│   ├── evidence.py                 # Snapshot evidence database operations
│   ├── face_log.py                 # Face presence logs persistence
│   ├── question.py                 # Question bank query operations
│   └── session.py                  # Exam session lifecycle & finalization logic
│
├── routes/                         # Flask modular route blueprints
│   ├── auth.py                     # Candidate auth, exam flow, logging endpoints & admin routes
│   └── dashboard.py                # Dashboard route definitions
│
├── static/                         # Static assets
│   ├── analytics/                  # Generated plots and visualizations
│   ├── css/                        # Responsive CSS stylesheets
│   ├── evidence/                   # Timestamped incident snapshots (JPG)
│   └── photos/                     # Registration candidate profile photos
│
├── templates/                      # Jinja2 HTML templates
│   ├── admin.html                  # Flask Admin overview & candidate list
│   ├── admin_login.html            # Admin login interface
│   ├── analytics.html              # Embedded analytics view
│   ├── candidate_details.html      # Candidate evidence audit & deep-dive page
│   ├── dashboard.html              # Candidate exam dashboard & rules
│   ├── exam.html                   # Live exam interface with embedded webcam feed & timers
│   ├── index.html                  # Landing page
│   ├── login.html                  # Candidate login portal
│   ├── register.html               # Registration page with webcam photo snapshot
│   └── result.html                 # Post-exam score breakdown & AI summary report
│
└── utils/                          # Core proctoring, AI, and analytical engines
    ├── ai_report.py                # LangChain Gemini summary generator with fallback
    ├── analytics.py                # Pandas ETL, Seaborn visualization & K-Means clustering
    ├── browser_logger.py           # Browser event parsing & logging helpers
    ├── camera.py                   # Thread-safe OpenCV VideoCapture manager
    ├── camera_manager.py           # Camera lifecycle helpers
    ├── detector.py                 # Haar Cascade FaceDetector wrapper class
    ├── evidence_manager.py         # Snapshot capture & path security validator
    ├── faker_data.py               # Synthetic session generator for realistic cohorts
    ├── monitor.py                  # Real-time ExamMonitor state machine
    ├── report.py                   # ReportLab PDF report builder
    ├── rules.py                    # Proctoring rule validation helpers
    └── scoring.py                  # Integrity score, FPR, and risk level calculation engine
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- An active **webcam** (required for candidate photo capture and face detection).
- *(Optional)* A **Google Gemini API Key** for LLM-generated proctoring summaries.

### 2. Clone / Open Repository
```bash
cd "c:\Users\user\Downloads\ExamTrace"
```

### 3. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Seed Questions & Generate Synthetic Data
```bash
# Populate database with sample questions
python insert_questions.py

# (Optional) Generate realistic synthetic candidate cohort for rich analytics
python generate_data.py
```

---

## 🔐 Configuration & Environment Variables

Create or update a `.env` file in the project root:

```ini
SECRET_KEY=examguard_secret_key
GEMINI_API_KEY=your_gemini_api_key_here
ADMIN_EMAIL=admin@examguard.com
ADMIN_PASSWORD=admin123
STREAMLIT_URL=http://localhost:8501
```

> **Note**: If `GEMINI_API_KEY` is not provided or API calls fail, ExamTrace automatically invokes its **Deterministic Rule-Based Fallback Generator** without crashing.

---

## 💻 Running the Platform

### Start the Flask Application
```bash
python app.py
```
*When `app.py` starts, it automatically initializes database tables and checks/launches the Streamlit Invigilator Dashboard on port 8501 in the background.*

---

## 🌐 User Portals & Credentials

| Portal | URL | Description | Default Credentials |
| :--- | :--- | :--- | :--- |
| **Landing Page** | `http://127.0.0.1:5000/` | Main welcome page and portal selector | — |
| **Candidate Portal** | `http://127.0.0.1:5000/login` | Candidate login, registration, and exam window | Register new or use test candidate |
| **Admin Web Portal** | `http://127.0.0.1:5000/admin/login` | Flask-based candidate list & evidence audit | `admin@examguard.com` / `admin123` |
| **Invigilator Dashboard** | `http://localhost:8501` | Interactive Streamlit live proctoring & ML analytics | Public/Invigilator access |

---

## 📏 Proctoring Rules & Scoring Engine

Integrity scoring starts at a base score of **100** points. Deductions are applied dynamically:

| Event / Violation | Penalty Weight | Description |
| :--- | :---: | :--- |
| **Tab Switch** | `-5` | Candidate leaves exam tab |
| **Focus Loss** | `-3` | Window loses focus or minimizes |
| **Copy Attempt** | `-5` | Attempting to copy exam content |
| **Paste Attempt** | `-5` | Attempting to paste external text |
| **Right Click** | `-2` | Context menu invocation attempt |
| **Restricted Shortcut** | `-3` | Keyboard shortcuts like Alt+Tab, F12 |
| **Face Missing (Per event)** | `-5` | Webcam cannot detect candidate face |
| **Multiple Faces (Per event)**| `-10` | More than one person detected in frame |

### Risk Level Classification
- 🟢 **Low Risk**: $\text{Score} \ge 80$
- 🟡 **Medium Risk**: $50 \le \text{Score} < 80$
- 🔴 **High Risk**: $\text{Score} < 50$

---

## 🧪 Testing & Verification

Run the automated test suite to verify scoring boundaries, risk level thresholds, analytical dataset transformations, K-Means clustering, and evidence security:

```bash
python -m unittest test_milestone3.py
```

---

## 📚 Project Documentation

Additional documentation and project artifacts are available in the [`Docs/`](file:///c:/Users/user/Downloads/ExamTrace/Docs) folder:
- **`EXAMTRACE Generic Document.pdf`**: Detailed functional requirements and architectural specifications.
- **`ExamTrace_Agile_Document.pdf` & `ExamTrace_Agile_Report.xlsx`**: Agile sprint tracking, user stories, and milestone deliverables.
- **`ExamTrace_Defect_Tracker_Normal_Excel_Style.xlsx`**: Comprehensive defect log, severity categorizations, and resolution audit.
- **`ExamTrace_Unit_Test_Plan.xlsx`**: Test case matrices, verification criteria, and pass/fail metrics.

---

## 📄 License

This project is developed for educational and academic assessment integrity purposes.
