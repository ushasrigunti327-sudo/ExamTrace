"""
ExamGuard — Invigilator & Proctoring Intelligence Dashboard (Streamlit)
Online Exam Monitoring & Integrity Analytics Platform.
"""

import os
import io
import csv
import json
import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

from config import Config
from models.database import get_db_connection
from utils.evidence_manager import get_evidence_for_session
from utils.analytics import (
    build_analytical_dataset,
    generate_score_distribution,
    generate_event_heatmap,
    perform_kmeans_clustering,
    get_cohort_risk_profile
)

# ---------------------------------------------------------
# STREAMLIT PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(
    page_title="ExamGuard | Invigilator Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 16px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 12px;
    }
    .metric-title {
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.5px;
    }
    .metric-val {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        margin: 4px 0;
    }
    .badge-low { background-color: #dcfce7; color: #15803d; padding: 3px 8px; border-radius: 12px; font-weight: 600; font-size: 11px; }
    .badge-med { background-color: #fef3c7; color: #b45309; padding: 3px 8px; border-radius: 12px; font-weight: 600; font-size: 11px; }
    .badge-high { background-color: #fee2e2; color: #b91c1c; padding: 3px 8px; border-radius: 12px; font-weight: 600; font-size: 11px; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# DATABASE QUERIES
# ---------------------------------------------------------
def load_dashboard_data():
    conn = get_db_connection()
    
    sessions_df = pd.read_sql_query("""
        SELECT 
            sessions.id as session_id,
            sessions.candidate_id,
            candidates.username,
            candidates.email,
            candidates.photo,
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
    """, conn)

    alerts_df = pd.read_sql_query("""
        SELECT 'Face' as category, face_logs.event_type, face_logs.event_time, face_logs.session_id, candidates.username
        FROM face_logs
        JOIN sessions ON sessions.id = face_logs.session_id
        JOIN candidates ON candidates.id = sessions.candidate_id
        WHERE face_logs.event_type LIKE '%Missing%' OR face_logs.event_type LIKE '%Multiple%'
        UNION ALL
        SELECT 'Browser' as category, browser_logs.event_type, browser_logs.event_time, browser_logs.session_id, candidates.username
        FROM browser_logs
        JOIN sessions ON sessions.id = browser_logs.session_id
        JOIN candidates ON candidates.id = sessions.candidate_id
        ORDER BY event_time DESC
    """, conn)

    candidates_count = pd.read_sql_query("SELECT COUNT(*) as cnt FROM candidates", conn).iloc[0]["cnt"]
    events_count = pd.read_sql_query("SELECT (SELECT COUNT(*) FROM face_logs) + (SELECT COUNT(*) FROM browser_logs) as cnt", conn).iloc[0]["cnt"]
    
    conn.close()
    return sessions_df, alerts_df, candidates_count, events_count


sessions_df, alerts_df, candidates_count, events_count = load_dashboard_data()

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
    <h2 style="margin: 0; color: #2563eb;">🛡️ ExamGuard</h2>
</div>
<div style="font-size: 13px; color: #64748b; margin-bottom: 20px;">
    Invigilator & Proctoring Intelligence Portal
</div>
""", unsafe_allow_html=True)

nav_option = st.sidebar.radio(
    "Navigation Menu",
    [
        "📊 Overview",
        "🔴 Live Monitoring",
        "⚠️ Alerts & Evidence",
        "📁 Reports & Exports",
        "📈 Cohort Analytics & ML",
        "⚙️ Settings",
        "🚪 Logout / Switch Portal"
    ]
)

st.sidebar.divider()
st.sidebar.markdown(f"**Live Server:** `http://127.0.0.1:5000`")
st.sidebar.markdown(f"**Database:** SQLite (`database.db`)")


# ---------------------------------------------------------
# TAB 1: OVERVIEW
# ---------------------------------------------------------
if nav_option == "📊 Overview":
    st.header("📊 Invigilator Dashboard Overview")
    st.caption("Real-time summary metrics across all examination sessions and candidates.")

    total_sessions = len(sessions_df)
    active_sessions = len(sessions_df[sessions_df["status"] == "Active"]) if not sessions_df.empty else 0
    high_risk = len(sessions_df[sessions_df["risk_level"] == "High"]) if not sessions_df.empty else 0
    med_risk = len(sessions_df[sessions_df["risk_level"] == "Medium"]) if not sessions_df.empty else 0
    low_risk = len(sessions_df[sessions_df["risk_level"] == "Low"]) if not sessions_df.empty else 0
    avg_integrity = round(sessions_df["integrity_score"].mean(), 1) if not sessions_df.empty and sessions_df["integrity_score"].notnull().any() else 100.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔴 Active Sessions", active_sessions)
        st.metric("👥 Total Candidates", candidates_count)
    with col2:
        st.metric("⚠️ High Risk Sessions", high_risk, delta_color="inverse")
        st.metric("📁 Total Sessions", total_sessions)
    with col3:
        st.metric("🟡 Medium Risk Sessions", med_risk)
        st.metric("🛡️ Mean Integrity Score", f"{avg_integrity}%")
    with col4:
        st.metric("🟢 Low Risk Sessions", low_risk)
        st.metric("⚡ Total Event Logs", events_count)

    st.divider()

    st.subheader("🚨 Recent Suspicious Anomaly Alerts")
    if not alerts_df.empty:
        st.dataframe(
            alerts_df.head(10)[["category", "username", "session_id", "event_type", "event_time"]],
            column_config={
                "category": "Source",
                "username": "Candidate",
                "session_id": "Session #",
                "event_type": "Proctoring Anomaly Description",
                "event_time": "Timestamp"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No suspicious proctoring alerts recorded.")

    st.subheader("📋 Recent Examination Sessions")
    if not sessions_df.empty:
        st.dataframe(
            sessions_df[["session_id", "username", "status", "integrity_score", "risk_level", "face_presence_ratio", "start_time"]],
            column_config={
                "session_id": "ID",
                "username": "Candidate",
                "status": "Session Status",
                "integrity_score": "Score (%)",
                "risk_level": "Risk Profile",
                "face_presence_ratio": "Face Ratio (%)",
                "start_time": "Date & Time"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No examination sessions recorded.")


# ---------------------------------------------------------
# TAB 2: LIVE MONITORING
# ---------------------------------------------------------
elif nav_option == "🔴 Live Monitoring":
    st.header("🔴 Live Examination Monitoring")
    st.caption("Active candidate sessions currently being proctored in real-time.")

    active_df = sessions_df[sessions_df["status"] == "Active"] if not sessions_df.empty else pd.DataFrame()

    if not active_df.empty:
        st.success(f"Currently monitoring {len(active_df)} active examination session(s).")
        st.dataframe(
            active_df[["session_id", "username", "email", "integrity_score", "risk_level", "face_presence_ratio", "start_time"]],
            column_config={
                "session_id": "Session ID",
                "username": "Candidate Name",
                "email": "Email",
                "integrity_score": "Live Integrity (%)",
                "risk_level": "Current Risk",
                "face_presence_ratio": "Face Presence (%)",
                "start_time": "Exam Started"
            },
            hide_index=True,
            use_container_width=True
        )

        st.subheader("🔍 Active Session Inspection")
        selected_sid = st.selectbox("Select Session to Inspect:", active_df["session_id"].tolist())
        if selected_sid:
            row = active_df[active_df["session_id"] == selected_sid].iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Candidate:** {row['username']} ({row['email']})")
            c2.warning(f"**Live Score:** {row['integrity_score']}% | **Risk:** {row['risk_level']}")
            c3.success(f"**Face Ratio:** {row['face_presence_ratio']}% | Started: {row['start_time']}")
    else:
        st.info("No active examination sessions in progress right now.")


# ---------------------------------------------------------
# TAB 3: ALERTS & EVIDENCE
# ---------------------------------------------------------
elif nav_option == "⚠️ Alerts & Evidence":
    st.header("⚠️ Security Alerts & Incident Evidence")
    st.caption("Investigate suspicious proctoring alerts and visual evidence snapshots.")

    sev_filter = st.selectbox("Filter Alert Severity:", ["All Alerts", "Face Missing", "Multiple Faces", "Tab Switch", "Focus Loss"])
    
    filtered_alerts = alerts_df
    if sev_filter != "All Alerts" and not alerts_df.empty:
        filtered_alerts = alerts_df[alerts_df["event_type"].str.contains(sev_filter, case=False, na=False)]

    if not filtered_alerts.empty:
        st.dataframe(
            filtered_alerts,
            column_config={
                "category": "Category",
                "event_type": "Incident Event",
                "event_time": "Timestamp",
                "session_id": "Session ID",
                "username": "Candidate"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No alerts match the selected criteria.")

    st.subheader("📸 Captured Incident Evidence Snapshots")
    if not sessions_df.empty:
        evidence_sid = st.selectbox("Select Session ID for Evidence Review:", sessions_df["session_id"].tolist())
        if evidence_sid:
            evidence_items = get_evidence_for_session(evidence_sid)
            if evidence_items:
                st.write(f"Found {len(evidence_items)} incident snapshot(s) for Session #{evidence_sid}:")
                cols = st.columns(min(3, len(evidence_items)))
                for idx, ev in enumerate(evidence_items):
                    with cols[idx % 3]:
                        local_path = os.path.join("static", "evidence", ev["image_path"])
                        if os.path.exists(local_path):
                            st.image(local_path, caption=f"{ev['event_type']} - {ev['timestamp']}", use_container_width=True)
                        else:
                            st.caption(f"📸 {ev['event_type']} ({ev['timestamp']})")
            else:
                st.info(f"No visual incident snapshots recorded for Session #{evidence_sid}.")


# ---------------------------------------------------------
# TAB 4: REPORTS & EXPORTS
# ---------------------------------------------------------
elif nav_option == "📁 Reports & Exports":
    st.header("📁 Examination Reports & Data Exports")
    st.caption("Review completed sessions and download comprehensive CSV, JSON, and PDF reports.")

    # Export Action Buttons
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        if not sessions_df.empty:
            csv_buffer = io.StringIO()
            sessions_df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download All Sessions CSV",
                data=csv_buffer.getvalue(),
                file_name="examguard_sessions_report.csv",
                mime="text/csv",
                use_container_width=True
            )
    with col_exp2:
        if not sessions_df.empty:
            json_buffer = sessions_df.to_json(orient="records", indent=2)
            st.download_button(
                label="📥 Download All Sessions JSON",
                data=json_buffer,
                file_name="examguard_sessions_report.json",
                mime="application/json",
                use_container_width=True
            )

    st.divider()

    completed_df = sessions_df[sessions_df["status"] == "Completed"] if not sessions_df.empty else pd.DataFrame()
    if not completed_df.empty:
        st.subheader("Completed Examinations")
        st.dataframe(
            completed_df[["session_id", "username", "integrity_score", "risk_level", "face_presence_ratio", "end_time"]],
            column_config={
                "session_id": "ID",
                "username": "Candidate",
                "integrity_score": "Score (%)",
                "risk_level": "Risk",
                "face_presence_ratio": "Face Ratio (%)",
                "end_time": "Completion Time"
            },
            hide_index=True,
            use_container_width=True
        )

        st.subheader("📄 Candidate PDF Report Viewer")
        selected_rep_sid = st.selectbox("Select Completed Session:", completed_df["session_id"].tolist())
        if selected_rep_sid:
            rep_row = completed_df[completed_df["session_id"] == selected_rep_sid].iloc[0]
            pdf_path = os.path.join(Config.REPORTS_FOLDER, f"{rep_row['username']}_exam_report.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                st.download_button(
                    label=f"🖨 Download PDF Report for {rep_row['username']}",
                    data=pdf_bytes,
                    file_name=f"{rep_row['username']}_exam_report.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning(f"PDF report for {rep_row['username']} will be compiled upon request in Flask portal.")

            st.markdown("### 🤖 AI Integrity Report")
            st.info(rep_row.get("ai_summary") or "AI Integrity Summary is generating or not recorded.")


# ---------------------------------------------------------
# TAB 5: COHORT ANALYTICS & ML
# ---------------------------------------------------------
elif nav_option == "📈 Cohort Analytics & ML":
    st.header("📈 Cohort Integrity Analytics & Machine Learning")
    st.caption("Aggregated Data Science visual distributions and Scikit-Learn K-Means unsupervised clustering.")

    df_analytics = build_analytical_dataset()

    if not df_analytics.empty:
        cohort_stats, cohort_chart = get_cohort_risk_profile(df_analytics)

        col_st1, col_st2, col_st3, col_st4 = st.columns(4)
        col_st1.metric("Total Cohort", cohort_stats["total_sessions"])
        col_st2.metric("Mean Integrity", f"{cohort_stats['avg_integrity_score']}%")
        col_st3.metric("Low Risk Proportion", f"{cohort_stats['low_risk_pct']}%")
        col_st4.metric("High Risk Proportion", f"{cohort_stats['high_risk_pct']}%", delta_color="inverse")

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 Integrity Score Distribution")
            dist_img = generate_score_distribution(df_analytics)
            if os.path.exists(dist_img):
                st.image(dist_img, use_container_width=True)
        with c2:
            st.subheader("🍩 Cohort Risk Profiling")
            if os.path.exists(cohort_chart):
                st.image(cohort_chart, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.subheader("🔥 Event Frequency Heatmap")
            heat_img = generate_event_heatmap(df_analytics)
            if os.path.exists(heat_img):
                st.image(heat_img, use_container_width=True)
        with c4:
            st.subheader("🤖 K-Means Clustering")
            df_clustered, cluster_summaries, cluster_chart = perform_kmeans_clustering(df_analytics)
            if os.path.exists(cluster_chart):
                st.image(cluster_chart, use_container_width=True)

        st.subheader("💡 Behavioral Cluster Characteristics & Interpretation")
        cl_cols = st.columns(len(cluster_summaries))
        for idx, (cid, cinfo) in enumerate(cluster_summaries.items()):
            with cl_cols[idx]:
                st.markdown(f"""
                <div class="metric-card" style="border-left: 4px solid #2563eb;">
                    <h4>Cluster {cid} ({cinfo['session_count']} Sessions)</h4>
                    <p>• <b>Avg Integrity:</b> {cinfo['avg_integrity_score']}%<br>
                    • <b>Avg Events:</b> {cinfo['avg_suspicious_events']}<br>
                    • <b>Face Presence:</b> {cinfo['avg_face_presence_ratio']}%</p>
                    <p style="color: #2563eb; font-size: 13px;">{cinfo['behavior_profile']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No analytics session data available in database.")


# ---------------------------------------------------------
# TAB 6: SETTINGS
# ---------------------------------------------------------
elif nav_option == "⚙️ Settings":
    st.header("⚙️ Platform Proctoring Configuration")
    st.caption("Active proctoring rules, risk thresholds, and AI model parameters.")

    s1, s2 = st.columns(2)
    with s1:
        st.subheader("Event Deductions (Points)")
        st.write(f"• **Tab Switch Penalty:** -{Config.PENALTY_TAB_SWITCH} pts")
        st.write(f"• **Focus Loss Penalty:** -{Config.PENALTY_FOCUS_LOSS} pts")
        st.write(f"• **Copy Attempt Penalty:** -{Config.PENALTY_COPY} pts")
        st.write(f"• **Paste Attempt Penalty:** -{Config.PENALTY_PASTE} pts")
        st.write(f"• **Restricted Shortcut:** -{Config.PENALTY_SHORTCUT} pts")
        st.write(f"• **Face Missing Penalty:** -{Config.PENALTY_FACE_MISSING} pts")
        st.write(f"• **Multiple Faces Penalty:** -{Config.PENALTY_MULTIPLE_FACES} pts")

    with s2:
        st.subheader("Classification & AI Config")
        st.write(f"• **Low Risk Threshold:** Score ≥ {Config.RISK_LOW_THRESHOLD}%")
        st.write(f"• **Medium Risk Range:** Score {Config.RISK_MEDIUM_THRESHOLD}% – {Config.RISK_LOW_THRESHOLD - 1}%")
        st.write(f"• **High Risk Trigger:** Score < {Config.RISK_MEDIUM_THRESHOLD}%")
        st.write(f"• **Prolonged Absence Limit:** {Config.FACE_ABSENCE_PROLONGED_SECONDS}s")
        st.write(f"• **LangChain LLM Model:** `{Config.GEMINI_MODEL}`")
        st.write(f"• **Database Path:** `{Config.DATABASE}`")


# ---------------------------------------------------------
# TAB 7: LOGOUT / SWITCH PORTAL
# ---------------------------------------------------------
elif nav_option == "🚪 Logout / Switch Portal":
    st.header("🚪 Invigilator Portal Navigation")
    st.info("You are currently viewing the Streamlit Invigilator Dashboard.")
    
    st.markdown("""
    ### Quick Links:
    - [🔗 Open Flask Candidate Portal](http://127.0.0.1:5000/)
    - [🔗 Open Flask Invigilator Portal](http://127.0.0.1:5000/admin)
    - [🔗 Flask Admin Login](http://127.0.0.1:5000/admin/login)
    """)
