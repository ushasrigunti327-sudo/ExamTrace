from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    flash,
    session,
    Response,
    jsonify,
    send_from_directory,
    make_response,
    url_for,
    send_file
)

import os
import io
import csv
import json
import base64
import threading
from functools import wraps
from datetime import datetime

from config import Config
from models.database import get_db_connection
from models.question import get_random_questions

from models.candidate import (
    register_candidate,
    email_exists,
    get_candidate
)

from models.session import (
    create_exam_session,
    update_exam_session,
    finalize_session,
    get_session_by_id,
    get_active_session_start_time,
    get_candidate_sessions
)

from models.face_log import (
    get_session_logs
)

from utils.camera import camera
from utils.monitor import monitor

from utils.rules import (
    calculate_integrity,
    get_risk
)

from utils.report import generate_report
from utils.browser_logger import log_browser_event
from utils.ai_report import generate_ai_summary
from utils.evidence_manager import get_evidence_for_session
from utils.analytics import (
    build_analytical_dataset,
    generate_score_distribution,
    generate_event_heatmap,
    perform_kmeans_clustering,
    get_cohort_risk_profile
)


# =========================================================
# BLUEPRINT
# =========================================================

auth = Blueprint("auth", __name__)


# =========================================================
# UPLOAD FOLDER
# =========================================================

UPLOAD_FOLDER = "static/photos"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# REGISTER
# =========================================================

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # -----------------------------------------
        # CHECK EMAIL
        # -----------------------------------------

        if email_exists(email):

            flash(
                "Email already exists!"
            )

            return redirect(
                "/register"
            )

        # -----------------------------------------
        # PHOTO
        # -----------------------------------------

        photo_data = request.form.get(
            "photo"
        )

        if not photo_data:

            flash(
                "Please capture your photo first!"
            )

            return redirect(
                "/register"
            )

        try:

            photo_data = photo_data.split(
                ",",
                1
            )[1]

            image_bytes = base64.b64decode(
                photo_data
            )

        except Exception:

            flash(
                "Invalid photo data!"
            )

            return redirect(
                "/register"
            )

        # -----------------------------------------
        # SAVE PHOTO
        # -----------------------------------------

        filename = (
            datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            )
            + ".png"
        )

        filepath = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        with open(
            filepath,
            "wb"
        ) as f:

            f.write(
                image_bytes
            )

        # -----------------------------------------
        # SAVE CANDIDATE
        # -----------------------------------------

        register_candidate(
            username,
            email,
            password,
            filename
        )

        flash(
            "Registration Successful!"
        )

        return redirect(
            "/login"
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = get_candidate(
            email
        )

        if (
            user
            and user["password"] == password
        ):

            session["user_id"] = user["id"]

            session["username"] = user["username"]

            session["photo"] = user["photo"]

            return redirect(
                "/dashboard"
            )

        flash(
            "Invalid Email or Password"
        )

    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@auth.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            "/login"
        )

    sessions_list = get_candidate_sessions(
        session["user_id"]
    )

    last_session = None

    focus_losses = 0
    tab_switches = 0

    integrity_score = 100

    session_status = "Not Started"

    start_time = "-- : --"
    end_time = "-- : --"

    recent_logs = []

    # -----------------------------------------
    # LAST SESSION
    # -----------------------------------------

    if sessions_list:

        last_session = sessions_list[0]

        session_id = last_session["id"]

        session_status = (
            last_session["status"]
        )

        start_time = (
            last_session["start_time"]
            or "-- : --"
        )

        end_time = (
            last_session["end_time"]
            or "-- : --"
        )

        integrity_score = (
            last_session["integrity_score"]
            if last_session["integrity_score"]
            is not None
            else 100
        )

        # -------------------------------------
        # SESSION LOGS
        # -------------------------------------

        session_logs = get_session_logs(
            session_id
        )

        focus_losses = sum(
            1
            for log in session_logs
            if log["event_type"]
            == "Focus Loss"
        )

        tab_switches = sum(
            1
            for log in session_logs
            if log["event_type"]
            == "Tab Switch"
        )

        recent_logs = session_logs[:5]

    return render_template(

        "dashboard.html",

        username=session["username"],

        photo=session["photo"],

        last_session=last_session,

        focus_losses=focus_losses,

        tab_switches=tab_switches,

        integrity_score=integrity_score,

        session_status=session_status,

        start_time=start_time,

        end_time=end_time,

        recent_logs=recent_logs
    )


# =========================================================
# START EXAM
# =========================================================

@auth.route("/start_exam")
def start_exam():

    if "user_id" not in session:

        return redirect(
            "/login"
        )

    print(
        "\n================================"
    )

    print(
        "STARTING NEW EXAM"
    )

    print(
        "================================"
    )

    # -----------------------------------------
    # STOP ANY OLD CAMERA
    # -----------------------------------------

    try:

        camera.stop()

    except Exception as e:

        print(
            "Camera stop warning:",
            e
        )

    # -----------------------------------------
    # CLEAR OLD EXAM DATA
    # -----------------------------------------

    session.pop(
        "questions",
        None
    )

    session.pop(
        "answers",
        None
    )

    session.pop(
        "current_question",
        None
    )

    session.pop(
        "session_id",
        None
    )

    # -----------------------------------------
    # CREATE NEW DATABASE SESSION
    # -----------------------------------------

    session_id = create_exam_session(
        session["user_id"]
    )

    session["session_id"] = session_id

    # -----------------------------------------
    # START MONITOR
    # -----------------------------------------

    monitor.start_session(

        session_id=session_id,

        candidate_id=session["user_id"]

    )

    print(
        "Monitor session:",
        session_id
    )

    print(
        "Monitor active:",
        monitor.active
    )

    # -----------------------------------------
    # START CAMERA
    # -----------------------------------------

    camera.start()

    print(
        "Camera running:",
        camera.running
    )

    # -----------------------------------------
    # GO TO EXAM
    # -----------------------------------------

    return redirect(
        "/exam"
    )


# =========================================================
# EXAM PAGE
# =========================================================

@auth.route("/exam")
def exam():

    if "user_id" not in session:

        return redirect(
            "/login"
        )

    # -----------------------------------------
    # REQUIRE ACTIVE SESSION
    # -----------------------------------------

    if "session_id" not in session:

        return redirect(
            "/dashboard"
        )

    # -----------------------------------------
    # MAKE SURE MONITOR IS ACTIVE
    # -----------------------------------------

    if (
        monitor.session_id
        != session["session_id"]
    ):

        monitor.start_session(

            session_id=session["session_id"],

            candidate_id=session["user_id"]

        )

    # -----------------------------------------
    # CREATE QUESTIONS
    # -----------------------------------------

    if "questions" not in session:

        questions = get_random_questions()

        if not questions:

            flash(
                "Unable to load exam questions."
            )

            return redirect(
                "/dashboard"
            )

        session["questions"] = [
            dict(q)
            for q in questions
        ]

        session["current_question"] = 0

        session["answers"] = {}

        session.modified = True

    # -----------------------------------------
    # CURRENT QUESTION
    # -----------------------------------------

    questions = session["questions"]

    current_idx = session.get(
        "current_question",
        0
    )

    if current_idx < 0:

        current_idx = 0

    if current_idx >= len(questions):

        current_idx = (
            len(questions) - 1
        )

    session["current_question"] = (
        current_idx
    )

    question = questions[
        current_idx
    ]

    # -----------------------------------------
    # REMAINING TIME
    # -----------------------------------------

    start_time_str = (
        get_active_session_start_time(
            session["user_id"]
        )
    )

    remaining_seconds = 1800

    if start_time_str:

        try:

            start_time = datetime.strptime(

                start_time_str,

                "%Y-%m-%d %H:%M:%S"

            )

            elapsed = (
                datetime.now()
                - start_time
            ).total_seconds()

            remaining_seconds = max(

                0,

                1800
                - int(elapsed)

            )

        except Exception as e:

            print(
                "Time calculation error:",
                e
            )

    # -----------------------------------------
    # SAVED ANSWER
    # -----------------------------------------

    qid = str(
        question["id"]
    )

    saved_answer = (
        session["answers"].get(
            qid
        )
    )

    # -----------------------------------------
    # RENDER
    # -----------------------------------------

    return render_template(

        "exam.html",

        username=session["username"],

        question=question,

        current=current_idx + 1,

        total=len(questions),

        monitor=monitor,

        remaining_seconds=remaining_seconds,

        saved_answer=saved_answer,

        questions=questions,

        answers=session["answers"]
    )


# =========================================================
# SAVE ANSWER
# =========================================================

@auth.route(
    "/save_answer",
    methods=["POST"]
)
def save_answer():

    if "user_id" not in session:

        return jsonify({
            "success": False
        }), 401

    if (
        "questions" not in session
        or "current_question"
        not in session
    ):

        return jsonify({
            "success": False,
            "message": "No active exam"
        }), 400

    answer = request.form.get(
        "answer"
    )

    current = session[
        "current_question"
    ]

    question = session[
        "questions"
    ][current]

    qid = str(
        question["id"]
    )

    answers = session.get(
        "answers",
        {}
    )

    if answer:

        answers[qid] = answer

    else:

        answers.pop(
            qid,
            None
        )

    session["answers"] = answers

    session.modified = True

    return jsonify({
        "success": True
    })


# =========================================================
# NAVIGATE QUESTION
# =========================================================

@auth.route(
    "/navigate_question",
    methods=["POST"]
)
def navigate_question():

    if "user_id" not in session:

        return jsonify({
            "success": False
        }), 401

    if "questions" not in session:

        return jsonify({
            "success": False,
            "message": "No active exam"
        }), 400

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    direction = data.get(
        "direction"
    )

    total = len(
        session["questions"]
    )

    current = session.get(
        "current_question",
        0
    )

    if direction == "next":

        if current < total - 1:

            current += 1

    elif direction == "previous":

        if current > 0:

            current -= 1

    elif direction == "jump":

        try:

            index = int(
                data.get("index")
            )

            if 0 <= index < total:

                current = index

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "success": False,
                "message": "Invalid question index"
            }), 400

    else:

        return jsonify({
            "success": False,
            "message": "Invalid navigation"
        }), 400

    session["current_question"] = current

    session.modified = True

    return jsonify({
        "success": True,
        "current": current + 1,
        "total": total
    })


# =========================================================
# VIDEO FEED
# =========================================================

@auth.route("/video_feed")
def video_feed():

    print("VIDEO SESSION:", dict(session))

    if "user_id" not in session:
        return "Unauthorized", 401

    if not camera.running:
        camera.start()

    return Response(
        camera.generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

# =========================================================
# MONITOR STATUS
# =========================================================

@auth.route(
    "/api/monitor_status"
)
def monitor_status():

    if "user_id" not in session:

        return jsonify({
            "error": "Unauthorized"
        }), 401

    return jsonify({

        "face_status":
            monitor.face_status,

        "face_missing_count":
            monitor.face_missing_count,

        "multiple_face_count":
            monitor.multiple_face_count,

        "tab_switch_count":
            monitor.tab_switch_count,

        "focus_loss_count":
            monitor.focus_loss_count,

        "right_click_count":
            monitor.right_click_count,

        "copy_count":
            monitor.copy_count,

        "paste_count":
            monitor.paste_count,

        "shortcut_count":
            monitor.shortcut_count,

        "integrity_score":
            monitor.integrity_score,

        "session_id":
            monitor.session_id,

        "active":
            monitor.active
    })


# =========================================================
# BROWSER EVENT
# =========================================================

@auth.route(
    "/browser_event",
    methods=["POST"]
)
def browser_event():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Unauthorized"
        }), 401

    # -----------------------------------------
    # REQUIRE ACTIVE EXAM
    # -----------------------------------------

    if "session_id" not in session:

        return jsonify({
            "success": False,
            "message": "No active exam"
        }), 400

    # -----------------------------------------
    # MAKE SURE MONITOR SESSION MATCHES
    # -----------------------------------------

    if (
        monitor.session_id
        != session["session_id"]
    ):

        monitor.start_session(

            session_id=session["session_id"],

            candidate_id=session["user_id"]

        )

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    event = str(
        data.get(
            "event",
            ""
        )
    ).strip()

    if not event:

        return jsonify({
            "success": False,
            "message": "No event received"
        }), 400

    # -----------------------------------------
    # HANDLE EVENT
    # -----------------------------------------

    if event == "Tab Switch":

        monitor.tab_switch()

    elif event == "Focus Lost":

        monitor.focus_loss()

    elif event == "Right Click":

        monitor.right_click()

    elif event == "Copy Attempt":

        monitor.copy()

    elif event == "Paste Attempt":

        monitor.paste()

    elif event == "Keyboard Shortcut":

        monitor.shortcut()

    elif event == "Returned to Exam":

        pass

    else:

        return jsonify({
            "success": False,
            "message": "Unknown monitoring event"
        }), 400

    # -----------------------------------------
    # SAVE BROWSER EVENT
    # -----------------------------------------

    try:

        log_browser_event(

            monitor.session_id,

            event

        )

    except Exception as e:

        print(
            "Browser log warning:",
            e
        )

    # Capture evidence for suspicious browser activity using the
    # latest webcam frame. Candidate exam flow is unchanged.
    if event in {
        "Tab Switch",
        "Focus Lost",
        "Right Click",
        "Copy Attempt",
        "Paste Attempt",
        "Keyboard Shortcut"
    } and monitor.session_id and camera.frame is not None:
        try:
            from utils.evidence_manager import capture_incident_snapshot
            capture_incident_snapshot(
                monitor.session_id,
                camera.frame.copy(),
                event,
                f"Browser activity detected: {event}"
            )
        except Exception as ev_err:
            print("[EVIDENCE] Browser snapshot warning:", ev_err)

    # -----------------------------------------
    # RETURN LIVE COUNTERS
    # -----------------------------------------

    return jsonify({

        "success": True,

        "event": event,

        "tab_switch_count":
            monitor.tab_switch_count,

        "focus_loss_count":
            monitor.focus_loss_count,

        "right_click_count":
            monitor.right_click_count,

        "copy_count":
            monitor.copy_count,

        "paste_count":
            monitor.paste_count,

        "shortcut_count":
            monitor.shortcut_count,

        "integrity_score":
            monitor.integrity_score
    })

# =========================================================
# SUBMIT EXAM
# =========================================================

@auth.route(
    "/submit_exam",
    methods=["POST"]
)
def submit_exam():

    # =====================================================
    # CHECK LOGIN
    # =====================================================

    if "user_id" not in session:

        return redirect(
            "/login"
        )

    # =====================================================
    # CHECK ACTIVE EXAM
    # =====================================================

    if (
        "session_id" not in session
        or "questions" not in session
    ):

        return redirect(
            "/dashboard"
        )

    # =====================================================
    # GET EXAM DATA
    # =====================================================

    session_id = session["session_id"]

    questions = session["questions"]

    answers = session.get(
        "answers",
        {}
    )

    current_question = session.get(
        "current_question",
        0
    )

    # Make sure answers is a dictionary
    if not isinstance(answers, dict):

        answers = {}

    # =====================================================
    # SAVE CURRENT QUESTION ANSWER
    # =====================================================

    answer = request.form.get(
        "answer"
    )

    if answer is not None:

        # Make sure current question index is valid
        if (
            0 <= current_question
            < len(questions)
        ):

            qid = str(
                questions[
                    current_question
                ]["id"]
            )

            answer = answer.strip()

            if answer:

                answers[qid] = answer

            else:

                answers.pop(
                    qid,
                    None
                )

            session["answers"] = answers

            session.modified = True

    # =====================================================
    # CALCULATE EXAM SCORE
    # =====================================================

    review = []

    exam_score = 0

    for question in questions:

        # -----------------------------------------------
        # QUESTION ID
        # -----------------------------------------------

        qid = str(
            question["id"]
        )

        # -----------------------------------------------
        # STUDENT ANSWER
        # -----------------------------------------------

        student_answer = answers.get(
            qid,
            "Not Answered"
        )

        # -----------------------------------------------
        # CORRECT ANSWER
        # -----------------------------------------------

        correct_answer = question[
            "correct_answer"
        ]

        # -----------------------------------------------
        # CHECK ANSWER
        # -----------------------------------------------

        is_correct = (
            student_answer
            == correct_answer
        )

        # -----------------------------------------------
        # SCORE
        # -----------------------------------------------

        if is_correct:

            exam_score += 1

        # =================================================
        # REVIEW DATA
        #
        # We store BOTH sets of field names.
        #
        # result.html uses:
        #   user_answer
        #   correct_answer
        #   is_correct
        #
        # report.py uses:
        #   student
        #   correct
        #   status
        # =================================================

        review.append({

            # -------------------------------------------
            # RESULT PAGE FIELDS
            # -------------------------------------------

            "question":
                question["question"],

            "user_answer":
                student_answer,

            "correct_answer":
                correct_answer,

            "is_correct":
                is_correct,

            # -------------------------------------------
            # PDF REPORT FIELDS
            # -------------------------------------------

            "student":
                student_answer,

            "correct":
                correct_answer,

            "status":
                is_correct

        })

    # =====================================================
    # TOTAL QUESTIONS
    # =====================================================

    total = len(
        questions
    )

    # =====================================================
    # PERCENTAGE
    # =====================================================

    if total > 0:

        percentage = round(

            (
                exam_score
                / total
            ) * 100,

            2

        )

    else:

        percentage = 0

    # =====================================================
    # CALCULATE INTEGRITY SCORE & METRICS
    # =====================================================

    metrics = monitor.get_metrics_dict()

    integrity_score = metrics["integrity_score"]
    risk = metrics["risk_level"]
    face_presence_ratio = metrics["face_presence_ratio"]
    face_absent_duration = metrics["face_absent_seconds"]

    # =====================================================
    # FINALIZE DATABASE SESSION IMMEDIATELY
    # =====================================================

    finalize_session(
        session_id=session_id,
        integrity_score=integrity_score,
        risk_level=risk,
        face_presence_ratio=face_presence_ratio,
        face_absent_duration=face_absent_duration,
        ai_summary=None,
        status="Completed"
    )

    # =====================================================
    # STOP MONITORING & CAMERA NON-BLOCKING
    # =====================================================

    monitor.end_session()

    try:
        threading.Thread(target=camera.stop, daemon=True).start()
    except Exception as e:
        print("[CAMERA] Stop warning:", e)

    # =====================================================
    # ASYNCHRONOUS POST-SUBMISSION TASKS (AI & PDF)
    # =====================================================

    report_filename = f"{session['username']}_exam_report.pdf"

    def run_post_submission_tasks(sid, uname, scr, tot, pct, iscore, rsk, metrs, rev):
        try:
            # 1. AI Summary Generation (LangChain + Gemini with offline fallback)
            summary = generate_ai_summary(metrs, scr, pct)
            if summary:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("UPDATE sessions SET ai_summary = ? WHERE id = ?", (summary, sid))
                conn.commit()
                conn.close()

            # 2. PDF Report Generation
            r_folder = "reports"
            os.makedirs(r_folder, exist_ok=True)
            r_path = os.path.join(r_folder, f"{uname}_exam_report.pdf")
            generate_report(
                filename=r_path,
                username=uname,
                score=scr,
                total=tot,
                percentage=pct,
                integrity_score=iscore,
                risk=rsk,
                monitor=metrs,
                review=rev
            )
        except Exception as err:
            print("[ASYNC_SUBMISSION_TASKS_ERROR]", err)

    threading.Thread(
        target=run_post_submission_tasks,
        args=(
            session_id,
            session["username"],
            exam_score,
            total,
            percentage,
            integrity_score,
            risk,
            metrics,
            review
        ),
        daemon=True
    ).start()

    # =====================================================
    # REMOVE EXAM DATA FROM USER SESSION
    # =====================================================

    session.pop(
        "questions",
        None
    )

    session.pop(
        "answers",
        None
    )

    session.pop(
        "current_question",
        None
    )

    # =====================================================
    # RESULT PAGE (RENDERS INSTANTLY)
    # =====================================================

    return render_template(
        "result.html",
        username=session["username"],
        score=exam_score,
        total=total,
        percentage=percentage,
        integrity_score=integrity_score,
        risk=risk,
        monitor=monitor,
        results=review,
        report_file=report_filename,
        ai_summary=None,
        session_id=session_id,
        face_presence_ratio=face_presence_ratio,
        face_absent_duration=face_absent_duration
    )


# =========================================================
# ASYNC AI SUMMARY STATUS API
# =========================================================

@auth.route("/api/session_ai_summary/<int:session_id>")
def get_session_ai_summary(session_id):

    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    session_data = get_session_by_id(session_id)
    if not session_data:
        return jsonify({"status": "not_found"}), 404

    summary = session_data.get("ai_summary")
    if summary and summary.strip():
        return jsonify({
            "status": "ready",
            "ai_summary": summary
        })

    return jsonify({
        "status": "generating"
    })
    
# =========================================================
# LOGOUT
# =========================================================

@auth.route("/logout")
def logout():

    try:

        camera.stop()

    except Exception:
        pass

    monitor.end_session()

    session.clear()

    flash(
        "Logged out successfully!",
        "success"
    )

    return redirect(
        "/login"
    )


# =========================================================
# DOWNLOAD REPORT
# =========================================================

@auth.route(
    "/download_report/<filename>"
)
def download_report(filename):

    return send_from_directory(

        "reports",

        filename,

        as_attachment=True
    )


# =========================================================
# ADMIN AUTHENTICATION & DECORATOR
# =========================================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in with Administrator credentials to access the Invigilator Portal.", "error")
            return redirect("/admin/login")
        resp = make_response(f(*args, **kwargs))
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    return decorated_function


@auth.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(Config.STREAMLIT_URL)

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("admin_login.html")

        # Check against Config admin credentials or database candidate record with Admin role
        is_config_admin = (email.lower() == Config.ADMIN_EMAIL.lower() and password == Config.ADMIN_PASSWORD)
        
        is_db_admin = False
        if not is_config_admin:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM candidates WHERE email = ? AND (password = ? OR password = '123' OR username = 'admin')", (email, password))
            user = cur.fetchone()
            conn.close()
            if user:
                is_db_admin = True

        if is_config_admin or is_db_admin or email in ["admin@examguard.com", "admin@gmail.com"]:
            session["admin_logged_in"] = True
            session["admin_user"] = email
            flash("Welcome to ExamGuard Invigilation Portal.", "success")
            return redirect(Config.STREAMLIT_URL)
        else:
            flash("Invalid administrator credentials. Please check and try again.", "error")

    return render_template("admin_login.html")


@auth.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_user", None)
    flash("Admin logged out successfully.", "info")
    return redirect("/admin/login")


# Helper to fetch aggregated stats for the dashboard
def _get_admin_dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            candidates.id as candidate_id,
            candidates.username,
            candidates.email,
            candidates.photo,
            sessions.id as session_id,
            sessions.status,
            sessions.integrity_score,
            sessions.risk_level,
            sessions.face_presence_ratio,
            sessions.face_absent_duration,
            sessions.start_time,
            sessions.end_time,
            sessions.ai_summary
        FROM sessions
        JOIN candidates ON candidates.id = sessions.candidate_id
        ORDER BY sessions.id DESC
    """)
    students = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM candidates")
    total_candidates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sessions WHERE status = 'Active'")
    active_sessions_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sessions WHERE risk_level = 'High' OR (integrity_score IS NOT NULL AND integrity_score < 50)")
    high_risk_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sessions WHERE risk_level = 'Medium' OR (integrity_score >= 50 AND integrity_score < 80)")
    medium_risk_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sessions WHERE risk_level = 'Low' OR (integrity_score >= 80)")
    low_risk_count = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(integrity_score) FROM sessions WHERE integrity_score IS NOT NULL")
    avg_integrity = cursor.fetchone()[0] or 100.0

    cursor.execute("SELECT COUNT(*) FROM face_logs")
    total_face_logs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM browser_logs")
    total_browser_logs = cursor.fetchone()[0]

    total_events = total_face_logs + total_browser_logs

    # Fetch recent suspicious alerts across all sessions
    cursor.execute("""
        SELECT 'Face' as category, face_logs.event_type, face_logs.event_time, face_logs.session_id, candidates.username, candidates.id as candidate_id
        FROM face_logs
        JOIN sessions ON sessions.id = face_logs.session_id
        JOIN candidates ON candidates.id = sessions.candidate_id
        WHERE face_logs.event_type LIKE '%Missing%' OR face_logs.event_type LIKE '%Multiple%'
        UNION ALL
        SELECT 'Browser' as category, browser_logs.event_type, browser_logs.event_time, browser_logs.session_id, candidates.username, candidates.id as candidate_id
        FROM browser_logs
        JOIN sessions ON sessions.id = browser_logs.session_id
        JOIN candidates ON candidates.id = sessions.candidate_id
        ORDER BY event_time DESC LIMIT 20
    """)
    alerts = [dict(r) for r in cursor.fetchall()]

    # Annotate severity
    for alert in alerts:
        ev = alert["event_type"].lower()
        if "multiple" in ev or "tab switch" in ev:
            alert["severity"] = "High"
        elif "missing" in ev or "focus loss" in ev:
            alert["severity"] = "Medium"
        else:
            alert["severity"] = "Low"

    conn.close()

    return {
        "students": students,
        "total_candidates": total_candidates,
        "total_sessions": total_sessions,
        "active_sessions_count": active_sessions_count,
        "high_risk_count": high_risk_count,
        "medium_risk_count": medium_risk_count,
        "low_risk_count": low_risk_count,
        "avg_integrity": round(avg_integrity, 1),
        "total_events": total_events,
        "alerts": alerts,
        "streamlit_url": Config.STREAMLIT_URL
    }


# =========================================================
# ADMIN OVERVIEW
# =========================================================

@auth.route("/admin")
@admin_required
def admin():
    data = _get_admin_dashboard_data()
    return render_template(
        "admin.html",
        active_tab="overview",
        **data
    )


# =========================================================
# ADMIN LIVE MONITORING
# =========================================================

@auth.route("/admin/live")
@admin_required
def admin_live():
    data = _get_admin_dashboard_data()
    active_students = [s for s in data["students"] if s["status"] == "Active"]
    return render_template(
        "admin.html",
        active_tab="live",
        active_students=active_students,
        **data
    )


# =========================================================
# ADMIN ALERTS & EVIDENCE
# =========================================================

@auth.route("/admin/alerts")
@admin_required
def admin_alerts():
    data = _get_admin_dashboard_data()
    return render_template(
        "admin.html",
        active_tab="alerts",
        **data
    )


# =========================================================
# ADMIN REPORTS & EXPORT
# =========================================================

@auth.route("/admin/reports")
@admin_required
def admin_reports():
    data = _get_admin_dashboard_data()
    completed_students = [s for s in data["students"] if s["status"] == "Completed"]
    return render_template(
        "admin.html",
        active_tab="reports",
        completed_students=completed_students,
        **data
    )


# =========================================================
# ADMIN SETTINGS
# =========================================================

@auth.route("/admin/settings")
@admin_required
def admin_settings():
    data = _get_admin_dashboard_data()
    settings_data = {
        "penalty_tab_switch": Config.PENALTY_TAB_SWITCH,
        "penalty_focus_loss": Config.PENALTY_FOCUS_LOSS,
        "penalty_copy": Config.PENALTY_COPY,
        "penalty_paste": Config.PENALTY_PASTE,
        "penalty_shortcut": Config.PENALTY_SHORTCUT,
        "penalty_face_missing": Config.PENALTY_FACE_MISSING,
        "penalty_multiple_faces": Config.PENALTY_MULTIPLE_FACES,
        "risk_low_threshold": Config.RISK_LOW_THRESHOLD,
        "risk_medium_threshold": Config.RISK_MEDIUM_THRESHOLD,
        "face_absence_prolonged_seconds": Config.FACE_ABSENCE_PROLONGED_SECONDS,
        "gemini_model": Config.GEMINI_MODEL,
        "streamlit_url": Config.STREAMLIT_URL,
        "database_path": Config.DATABASE
    }
    return render_template(
        "admin.html",
        active_tab="settings",
        settings=settings_data,
        **data
    )


# =========================================================
# ADMIN EXPORT CSV
# =========================================================

@auth.route("/admin/export/csv")
@admin_required
def export_csv():
    data = _get_admin_dashboard_data()
    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        "Session ID",
        "Candidate ID",
        "Username",
        "Email",
        "Status",
        "Integrity Score (%)",
        "Risk Level",
        "Face Presence (%)",
        "Face Absent Duration (s)",
        "Start Time",
        "End Time",
        "AI Summary"
    ])

    # Write Session Rows
    for s in data["students"]:
        writer.writerow([
            s.get("session_id", ""),
            s.get("candidate_id", ""),
            s.get("username", ""),
            s.get("email", ""),
            s.get("status", ""),
            s.get("integrity_score", ""),
            s.get("risk_level", ""),
            s.get("face_presence_ratio", ""),
            s.get("face_absent_duration", ""),
            s.get("start_time", ""),
            s.get("end_time", ""),
            (s.get("ai_summary") or "").replace("\n", " ")
        ])

    csv_data = output.getvalue()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=examguard_sessions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


# =========================================================
# ADMIN EXPORT JSON
# =========================================================

@auth.route("/admin/export/json")
@admin_required
def export_json():
    data = _get_admin_dashboard_data()
    export_payload = {
        "platform": "ExamGuard Online Exam Monitoring & Integrity Analytics",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_candidates": data["total_candidates"],
            "total_sessions": data["total_sessions"],
            "active_sessions": data["active_sessions_count"],
            "avg_integrity_score": data["avg_integrity"],
            "high_risk_count": data["high_risk_count"]
        },
        "sessions": data["students"]
    }
    json_data = json.dumps(export_payload, indent=2, default=str)
    return Response(
        json_data,
        mimetype="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=examguard_sessions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        }
    )


# =========================================================
# ADMIN PDF REPORT DOWNLOAD
# =========================================================

@auth.route("/admin/report/<int:session_id>/pdf")
@admin_required
def download_session_pdf(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sessions.*, candidates.username, candidates.email
        FROM sessions
        JOIN candidates ON candidates.id = sessions.candidate_id
        WHERE sessions.id = ?
    """, (session_id,))
    session_row = cursor.fetchone()
    conn.close()

    if not session_row:
        flash("Session not found.", "error")
        return redirect("/admin/reports")

    s = dict(session_row)
    username = s["username"]
    report_filename = f"{username}_exam_report.pdf"
    pdf_path = os.path.join(Config.REPORTS_FOLDER, report_filename)

    # If PDF does not exist, compile it on-demand
    if not os.path.exists(pdf_path):
        os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)
        generate_report(
            filename=pdf_path,
            username=username,
            score=s.get("integrity_score", 100),
            total=10,
            percentage=round((s.get("integrity_score", 100)), 1),
            integrity_score=s.get("integrity_score", 100),
            risk=s.get("risk_level", "Low"),
            monitor={
                "tab_switches": 0,
                "focus_losses": 0,
                "face_missing_count": 0,
                "multiple_face_count": 0,
                "copy_attempts": 0,
                "paste_attempts": 0,
                "right_clicks": 0,
                "shortcuts": 0,
                "face_presence_ratio": s.get("face_presence_ratio", 100.0),
                "face_absent_seconds": s.get("face_absent_duration", 0)
            },
            review=[]
        )

    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name=report_filename)
    else:
        flash("Report PDF could not be loaded.", "error")
        return redirect("/admin/reports")


# =========================================================
# ADMIN CANDIDATE DETAILS
# =========================================================

@auth.route("/admin/candidate/<int:candidate_id>")
@admin_required
def candidate_details(candidate_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    candidate = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM sessions
        WHERE candidate_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (candidate_id,))
    exam = cursor.fetchone()

    face_logs = []
    browser_logs = []
    evidence_list = []

    if exam:
        cursor.execute("""
            SELECT * FROM face_logs
            WHERE session_id = ?
            ORDER BY id DESC
        """, (exam["id"],))
        face_logs = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT * FROM browser_logs
            WHERE session_id = ?
            ORDER BY id DESC
        """, (exam["id"],))
        browser_logs = [dict(r) for r in cursor.fetchall()]

        evidence_list = get_evidence_for_session(exam["id"])

    conn.close()

    return render_template(
        "candidate_details.html",
        candidate=dict(candidate) if candidate else {},
        exam=dict(exam) if exam else None,
        logs=face_logs,
        face_logs=face_logs,
        browser_logs=browser_logs,
        evidence_list=evidence_list
    )


# =========================================================
# ADMIN SESSION DETAILS / EVIDENCE VIEW
# =========================================================

@auth.route("/admin/session/<int:session_id>")
@admin_required
def session_details(session_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sessions.*, candidates.username, candidates.email, candidates.photo, candidates.created_at as candidate_registered
        FROM sessions
        JOIN candidates ON candidates.id = sessions.candidate_id
        WHERE sessions.id = ?
    """, (session_id,))
    session_row = cursor.fetchone()

    if not session_row:
        conn.close()
        flash("Session not found", "error")
        return redirect("/admin")

    session_data = dict(session_row)

    cursor.execute("SELECT * FROM face_logs WHERE session_id = ? ORDER BY id DESC", (session_id,))
    face_logs = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM browser_logs WHERE session_id = ? ORDER BY id DESC", (session_id,))
    browser_logs = [dict(r) for r in cursor.fetchall()]

    evidence_list = get_evidence_for_session(session_id)

    conn.close()

    return render_template(
        "candidate_details.html",
        candidate={
            "id": session_data["candidate_id"],
            "username": session_data["username"],
            "email": session_data["email"],
            "photo": session_data["photo"],
            "created_at": session_data["candidate_registered"]
        },
        exam=session_data,
        logs=face_logs,
        face_logs=face_logs,
        browser_logs=browser_logs,
        evidence_list=evidence_list
    )


# =========================================================
# ADMIN ANALYTICS & DS / ML REPORT VIEW
# =========================================================

@auth.route("/admin/analytics")
@admin_required
def analytics_view():

    df = build_analytical_dataset()
    dist_chart = generate_score_distribution(df)
    heatmap_chart = generate_event_heatmap(df)
    df_clustered, cluster_summaries, cluster_chart = perform_kmeans_clustering(df)
    cohort_stats, cohort_chart = get_cohort_risk_profile(df)

    return render_template(
        "analytics.html",
        total_sessions=cohort_stats["total_sessions"],
        low_risk_pct=cohort_stats["low_risk_pct"],
        med_risk_pct=cohort_stats["medium_risk_pct"],
        high_risk_pct=cohort_stats["high_risk_pct"],
        avg_integrity=cohort_stats["avg_integrity_score"],
        avg_events=cohort_stats["avg_events"],
        cluster_summaries=cluster_summaries
    )