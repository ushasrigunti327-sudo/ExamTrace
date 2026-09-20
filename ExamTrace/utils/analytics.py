"""
Analytical Dataset, Data Science Visualizations, and Machine Learning Module.
Provides:
1. build_analytical_dataset(): Constructs the unified Pandas DataFrame for all sessions.
2. generate_score_distribution(): Matplotlib/Seaborn histogram & KDE of integrity scores.
3. generate_event_heatmap(): Seaborn heatmap of event categories across risk bands / time.
4. perform_kmeans_clustering(): Scikit-learn StandardScaler + KMeans behavioral clustering.
5. get_cohort_risk_profile(): Comprehensive cohort statistics and summary charts.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from models.database import get_db_connection
from utils.scoring import evaluate_session_integrity, get_risk_level, calculate_face_presence_ratio

# Ensure analytics charts directory exists
ANALYTICS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "static", "analytics")
os.makedirs(ANALYTICS_DIR, exist_ok=True)

COLUMNS = [
    "session_id",
    "candidate_id",
    "exam_id",
    "duration",
    "tab_switch_count",
    "focus_loss_count",
    "copy_count",
    "paste_count",
    "right_click_count",
    "shortcut_count",
    "face_missing_count",
    "multiple_face_count",
    "face_absent_duration",
    "face_presence_ratio",
    "suspicious_event_count",
    "integrity_score",
    "risk_level"
]


def build_analytical_dataset(conn=None):
    """
    Constructs a unified, clean Pandas DataFrame representing completed examination sessions
    by aggregating session metadata, browser logs, and face logs.
    """
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, candidate_id, status, start_time, end_time,
                   integrity_score, risk_level, face_presence_ratio,
                   face_absent_duration
            FROM sessions
            ORDER BY id ASC
        """)
        sessions = cursor.fetchall()

        if not sessions:
            return pd.DataFrame(columns=COLUMNS)

        cursor.execute("SELECT session_id, event_type FROM browser_logs")
        browser_rows = cursor.fetchall()
        browser_df = pd.DataFrame([dict(r) for r in browser_rows]) if browser_rows else pd.DataFrame(columns=["session_id", "event_type"])

        cursor.execute("SELECT session_id, event_type FROM face_logs")
        face_rows = cursor.fetchall()
        face_df = pd.DataFrame([dict(r) for r in face_rows]) if face_rows else pd.DataFrame(columns=["session_id", "event_type"])

        records = []
        for s in sessions:
            s_dict = dict(s)
            sid = s_dict["id"]

            # Aggregate browser event counts
            if not browser_df.empty:
                s_b = browser_df[browser_df["session_id"] == sid]
                tab_switches = int((s_b["event_type"] == "Tab Switch").sum())
                focus_losses = int((s_b["event_type"].isin(["Focus Lost", "Focus Loss"])).sum())
                copy_count = int((s_b["event_type"] == "Copy Attempt").sum())
                paste_count = int((s_b["event_type"] == "Paste Attempt").sum())
                right_clicks = int((s_b["event_type"] == "Right Click").sum())
                shortcuts = int((s_b["event_type"] == "Keyboard Shortcut").sum())
            else:
                tab_switches = focus_losses = copy_count = paste_count = right_clicks = shortcuts = 0

            # Aggregate face event counts
            if not face_df.empty:
                s_f = face_df[face_df["session_id"] == sid]
                face_missing = int((s_f["event_type"] == "Face Missing").sum())
                multiple_faces = int((s_f["event_type"] == "Multiple Faces").sum())
            else:
                face_missing = multiple_faces = 0

            # Duration calculation (default to 1800s / 30 mins)
            duration = 1800
            if s_dict.get("start_time") and s_dict.get("end_time"):
                try:
                    fmt = "%Y-%m-%d %H:%M:%S"
                    st = pd.to_datetime(s_dict["start_time"], format=fmt)
                    et = pd.to_datetime(s_dict["end_time"], format=fmt)
                    diff = int((et - st).total_seconds())
                    if diff > 0:
                        duration = diff
                except Exception:
                    pass

            absent_duration = s_dict.get("face_absent_duration")
            if absent_duration is None:
                absent_duration = face_missing * 15  # Fallback approximation if untracked

            # Calculate unified metrics
            eval_res = evaluate_session_integrity(
                tab_switches=tab_switches,
                focus_losses=focus_losses,
                face_missing_count=face_missing,
                multiple_face_count=multiple_faces,
                right_clicks=right_clicks,
                copy_attempts=copy_count,
                paste_attempts=paste_count,
                shortcuts=shortcuts,
                duration_seconds=duration,
                face_absent_seconds=absent_duration
            )

            # Store record
            records.append({
                "session_id": sid,
                "candidate_id": s_dict["candidate_id"],
                "exam_id": 1,
                "duration": duration,
                "tab_switch_count": tab_switches,
                "focus_loss_count": focus_losses,
                "copy_count": copy_count,
                "paste_count": paste_count,
                "right_click_count": right_clicks,
                "shortcut_count": shortcuts,
                "face_missing_count": face_missing,
                "multiple_face_count": multiple_faces,
                "face_absent_duration": eval_res["face_absent_seconds"],
                "face_presence_ratio": eval_res["face_presence_ratio"],
                "suspicious_event_count": eval_res["suspicious_event_count"],
                "integrity_score": eval_res["integrity_score"],
                "risk_level": eval_res["risk_level"]
            })

        df = pd.DataFrame(records, columns=COLUMNS)
        return df

    finally:
        if close_conn:
            conn.close()


def generate_score_distribution(df=None, output_path=None):
    """
    Generates a Data Science visualization showing the distribution of integrity scores across all sessions.
    """
    if df is None:
        df = build_analytical_dataset()

    if output_path is None:
        output_path = os.path.join(ANALYTICS_DIR, "integrity_distribution.png")

    plt.figure(figsize=(9, 5))
    if df.empty or "integrity_score" not in df.columns:
        plt.text(0.5, 0.5, "No Examination Session Data Available", ha="center", va="center", fontsize=14)
        plt.title("Integrity Score Distribution")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path

    # Plot histogram with KDE
    sns.histplot(
        df["integrity_score"],
        kde=True,
        bins=15,
        color="#3b82f6",
        edgecolor="black",
        alpha=0.6
    )

    # Add risk threshold guideline regions
    plt.axvline(80, color="#22c55e", linestyle="--", linewidth=2, label="Low Risk (>=80)")
    plt.axvline(50, color="#ef4444", linestyle="--", linewidth=2, label="High Risk (<50)")

    plt.title("Integrity Score Distribution Across Cohort", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Integrity Score (0 - 100)", fontsize=11)
    plt.ylabel("Number of Examination Sessions", fontsize=11)
    plt.xlim(-5, 105)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def generate_event_heatmap(df=None, output_path=None):
    """
    Generates an Event Frequency Heatmap analyzing the density of monitoring events
    across risk classifications or session cohorts.
    """
    if df is None:
        df = build_analytical_dataset()

    if output_path is None:
        output_path = os.path.join(ANALYTICS_DIR, "event_heatmap.png")

    plt.figure(figsize=(10, 5))
    if df.empty:
        plt.text(0.5, 0.5, "No Event Data Available", ha="center", va="center", fontsize=14)
        plt.title("Event Frequency Heatmap")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        return output_path

    event_cols = [
        "tab_switch_count",
        "focus_loss_count",
        "face_missing_count",
        "multiple_face_count",
        "copy_count",
        "paste_count",
        "right_click_count",
        "shortcut_count"
    ]
    renamed_cols = {
        "tab_switch_count": "Tab Switch",
        "focus_loss_count": "Focus Loss",
        "face_missing_count": "Face Missing",
        "multiple_face_count": "Multiple Faces",
        "copy_count": "Copy",
        "paste_count": "Paste",
        "right_click_count": "Right Click",
        "shortcut_count": "Shortcut"
    }

    # Group by Risk Level
    grouped = df.groupby("risk_level")[event_cols].mean().rename(columns=renamed_cols)
    # Order index logically: Low -> Medium -> High
    order = [r for r in ["Low", "Medium", "High"] if r in grouped.index]
    grouped = grouped.reindex(order)

    sns.heatmap(
        grouped,
        annot=True,
        fmt=".2f",
        cmap="YlOrRd",
        linewidths=1,
        linecolor="white",
        cbar_kws={"label": "Average Events per Session"}
    )

    plt.title("Event Frequency Heatmap by Risk Profile", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Event Categories", fontsize=11)
    plt.ylabel("Cohort Risk Level", fontsize=11)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def perform_kmeans_clustering(df=None, n_clusters=3, output_path=None):
    """
    Performs K-Means session clustering to discover behavioral patterns across the cohort.
    Uses StandardScaler, handles missing data, and assigns descriptive, non-judgmental cluster labels.
    """
    if df is None:
        df = build_analytical_dataset()

    if output_path is None:
        output_path = os.path.join(ANALYTICS_DIR, "kmeans_clusters.png")

    if df.empty or len(df) < n_clusters:
        return df, {}, None

    features = [
        "tab_switch_count",
        "focus_loss_count",
        "face_absent_duration",
        "multiple_face_count",
        "face_presence_ratio",
        "suspicious_event_count",
        "integrity_score"
    ]

    # Preprocessing
    X = df[features].fillna(0).copy()
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Fit K-Means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)
    df_clustered = df.copy()
    df_clustered["cluster_id"] = cluster_labels

    # Compute cluster profiles & factual descriptions
    cluster_summaries = {}
    for cid in range(n_clusters):
        c_df = df_clustered[df_clustered["cluster_id"] == cid]
        avg_score = float(c_df["integrity_score"].mean()) if not c_df.empty else 0.0
        avg_suspicious = float(c_df["suspicious_event_count"].mean()) if not c_df.empty else 0.0
        avg_ratio = float(c_df["face_presence_ratio"].mean()) if not c_df.empty else 0.0
        count = len(c_df)

        if avg_score >= 85:
            desc = "Standard Examination Behavior (High integrity, minimal monitoring events)"
        elif avg_score >= 60:
            desc = "Moderate Activity Behavior (Minor tab switches and brief face absences)"
        else:
            desc = "Elevated Event Activity (Frequent tab switches or prolonged face absences)"

        cluster_summaries[cid] = {
            "session_count": count,
            "avg_integrity_score": round(avg_score, 2),
            "avg_suspicious_events": round(avg_suspicious, 2),
            "avg_face_presence_ratio": round(avg_ratio, 2),
            "behavior_profile": desc
        }

    # Visualization
    plt.figure(figsize=(9, 6))
    palette = sns.color_palette("Set2", n_clusters)
    sns.scatterplot(
        data=df_clustered,
        x="suspicious_event_count",
        y="integrity_score",
        hue="cluster_id",
        palette=palette,
        s=90,
        alpha=0.85,
        edgecolor="black"
    )

    plt.title("K-Means Session Behavioral Clustering", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Total Suspicious Events Recorded", fontsize=11)
    plt.ylabel("Integrity Score (0 - 100)", fontsize=11)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(title="Cluster Profile", labels=[f"Cluster {i}: {cluster_summaries[i]['avg_integrity_score']}% avg" for i in range(n_clusters)])
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return df_clustered, cluster_summaries, output_path


def get_cohort_risk_profile(df=None, output_path=None):
    """
    Calculates cohort-level risk statistics and generates a risk breakdown visualization.
    """
    if df is None:
        df = build_analytical_dataset()

    if output_path is None:
        output_path = os.path.join(ANALYTICS_DIR, "cohort_risk_profile.png")

    total_sessions = len(df)
    if total_sessions == 0:
        return {
            "total_sessions": 0,
            "low_risk_count": 0,
            "medium_risk_count": 0,
            "high_risk_count": 0,
            "low_risk_pct": 0.0,
            "medium_risk_pct": 0.0,
            "high_risk_pct": 0.0,
            "avg_integrity_score": 0.0,
            "avg_events": {}
        }, output_path

    low_count = int((df["risk_level"] == "Low").sum())
    med_count = int((df["risk_level"] == "Medium").sum())
    high_count = int((df["risk_level"] == "High").sum())

    low_pct = round((low_count / total_sessions) * 100.0, 2)
    med_pct = round((med_count / total_sessions) * 100.0, 2)
    high_pct = round((high_count / total_sessions) * 100.0, 2)
    avg_score = round(float(df["integrity_score"].mean()), 2)

    stats = {
        "total_sessions": total_sessions,
        "low_risk_count": low_count,
        "medium_risk_count": med_count,
        "high_risk_count": high_count,
        "low_risk_pct": low_pct,
        "medium_risk_pct": med_pct,
        "high_risk_pct": high_pct,
        "avg_integrity_score": avg_score,
        "avg_events": {
            "tab_switches": round(float(df["tab_switch_count"].mean()), 2),
            "focus_losses": round(float(df["focus_loss_count"].mean()), 2),
            "face_missing": round(float(df["face_missing_count"].mean()), 2),
            "multiple_faces": round(float(df["multiple_face_count"].mean()), 2)
        }
    }

    # Risk Distribution Donut Chart
    plt.figure(figsize=(7, 5))
    labels = [f"Low Risk ({low_pct}%)", f"Medium Risk ({med_pct}%)", f"High Risk ({high_pct}%)"]
    counts = [low_count, med_count, high_count]
    colors = ["#22c55e", "#f59e0b", "#ef4444"]

    # Filter zero slices
    active_labels = [l for l, c in zip(labels, counts) if c > 0]
    active_counts = [c for c in counts if c > 0]
    active_colors = [col for col, c in zip(colors, counts) if c > 0]

    if active_counts:
        plt.pie(
            active_counts,
            labels=active_labels,
            colors=active_colors,
            startangle=140,
            wedgeprops=dict(width=0.4, edgecolor="white")
        )
    else:
        plt.text(0.5, 0.5, "No Data", ha="center")

    plt.title("Cohort-Level Risk Classification Breakdown", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

    return stats, output_path
