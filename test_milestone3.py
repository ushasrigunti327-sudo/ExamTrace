"""
Comprehensive Validation and Verification Test Suite for Milestone 3.
Validates:
1. Integrity Scoring Engine (Weights, Normalization, Boundaries [0, 100]).
2. Face Presence Ratio & Absent Duration Calculation.
3. Standardized Risk Classification (Low, Medium, High).
4. Analytical Dataset Creation (Pandas DataFrame with exact schema).
5. Data Science Visualizations (Score Distribution, Event Heatmap, Cohort Risk Profile).
6. Machine Learning K-Means Behavioral Clustering.
7. LangChain AI Integrity Report Agent & Offline Fallback.
8. Alert & Incident Evidence Management & Path Security.
9. Milestone 1 & 2 Non-Regression (Question loading, Candidate models, Session flow).
"""

import os
import sys
import unittest
import numpy as np
import pandas as pd

from config import Config
from models.database import create_tables, get_db_connection
from models.question import get_random_questions
from models.candidate import register_candidate, email_exists, get_candidate
from models.session import create_exam_session, finalize_session, get_session_by_id
from models.evidence import save_evidence, get_session_evidence
from utils.scoring import (
    calculate_face_presence_ratio,
    calculate_integrity_score,
    get_risk_level,
    evaluate_session_integrity
)
from utils.monitor import ExamMonitor
from utils.ai_report import generate_ai_summary
from utils.evidence_manager import capture_incident_snapshot, get_evidence_for_session
from utils.analytics import (
    build_analytical_dataset,
    generate_score_distribution,
    generate_event_heatmap,
    perform_kmeans_clustering,
    get_cohort_risk_profile
)


class Milestone3TestSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        create_tables()

    # =========================================================
    # 1. SCORING & RISK CLASSIFICATION TESTS
    # =========================================================

    def test_01_low_risk_scenario(self):
        """Test Low-risk behavior scenario."""
        result = evaluate_session_integrity(
            tab_switches=1,
            focus_losses=0,
            face_missing_count=0,
            multiple_face_count=0,
            right_clicks=0,
            copy_attempts=0,
            paste_attempts=0,
            shortcuts=0,
            duration_seconds=1800,
            face_absent_seconds=0
        )
        self.assertGreaterEqual(result["integrity_score"], 80)
        self.assertEqual(result["risk_level"], "Low")
        self.assertEqual(result["face_presence_ratio"], 100.0)

    def test_02_medium_risk_scenario(self):
        """Test Medium-risk behavior scenario."""
        result = evaluate_session_integrity(
            tab_switches=3,
            focus_losses=2,
            face_missing_count=1,
            multiple_face_count=0,
            right_clicks=1,
            copy_attempts=0,
            paste_attempts=0,
            shortcuts=1,
            duration_seconds=1800,
            face_absent_seconds=60
        )
        self.assertGreaterEqual(result["integrity_score"], 50)
        self.assertLess(result["integrity_score"], 80)
        self.assertEqual(result["risk_level"], "Medium")

    def test_03_high_risk_scenario(self):
        """Test High-risk behavior scenario."""
        result = evaluate_session_integrity(
            tab_switches=7,
            focus_losses=5,
            face_missing_count=4,
            multiple_face_count=2,
            right_clicks=3,
            copy_attempts=2,
            paste_attempts=2,
            shortcuts=3,
            duration_seconds=1800,
            face_absent_seconds=400
        )
        self.assertLess(result["integrity_score"], 50)
        self.assertEqual(result["risk_level"], "High")

    def test_04_score_boundary_clamping(self):
        """Test that score never goes below 0 or above 100."""
        # Extreme penalty
        min_score = calculate_integrity_score(
            tab_switches=50,
            focus_losses=50,
            face_missing_count=50,
            multiple_face_count=50
        )
        self.assertEqual(min_score, 0)

        # Zero violations
        max_score = calculate_integrity_score()
        self.assertEqual(max_score, 100)

    # =========================================================
    # 2. FACE PRESENCE RATIO TESTS
    # =========================================================

    def test_05_face_presence_ratio_math(self):
        """Test exact calculation of Face Presence Ratio: 57/60 mins = 95.0%."""
        ratio = calculate_face_presence_ratio(
            duration_seconds=3600,
            face_absent_seconds=180
        )
        self.assertEqual(ratio, 95.0)

        # 100% presence
        ratio_full = calculate_face_presence_ratio(1800, 0)
        self.assertEqual(ratio_full, 100.0)

        # Edge cases (duration <= 0)
        ratio_zero = calculate_face_presence_ratio(0, 0)
        self.assertGreaterEqual(ratio_zero, 0.0)
        self.assertLessEqual(ratio_zero, 100.0)

    # =========================================================
    # 3. LIVE EXAM MONITOR TESTS
    # =========================================================

    def test_06_exam_monitor_tracking(self):
        """Test ExamMonitor duration, events, and score updating."""
        mon = ExamMonitor()
        mon.start_session(session_id=999, candidate_id=1)
        self.assertTrue(mon.active)

        mon.tab_switch()
        mon.focus_loss()
        mon.copy()

        self.assertEqual(mon.tab_switch_count, 1)
        self.assertEqual(mon.focus_loss_count, 1)
        self.assertEqual(mon.copy_count, 1)

        metrics = mon.get_metrics_dict()
        self.assertEqual(metrics["tab_switches"], 1)
        self.assertEqual(metrics["focus_losses"], 1)
        self.assertEqual(metrics["copy_attempts"], 1)
        self.assertLess(metrics["integrity_score"], 100)

        mon.end_session()
        self.assertFalse(mon.active)

    # =========================================================
    # 4. ANALYTICAL DATASET & VISUALIZATION TESTS
    # =========================================================

    def test_07_analytical_dataset_schema(self):
        """Test that build_analytical_dataset returns DataFrame with all 17 required columns."""
        df = build_analytical_dataset()
        self.assertIsInstance(df, pd.DataFrame)
        required_cols = [
            "session_id", "candidate_id", "exam_id", "duration",
            "tab_switch_count", "focus_loss_count", "copy_count", "paste_count",
            "right_click_count", "shortcut_count", "face_missing_count",
            "multiple_face_count", "face_absent_duration", "face_presence_ratio",
            "suspicious_event_count", "integrity_score", "risk_level"
        ]
        for col in required_cols:
            self.assertIn(col, df.columns, f"Missing required column: {col}")

    def test_08_visualizations_and_clustering(self):
        """Test chart generation and K-Means clustering."""
        df = build_analytical_dataset()
        self.assertFalse(df.empty, "Dataset should not be empty.")

        # Score distribution
        p_dist = generate_score_distribution(df)
        self.assertTrue(os.path.exists(p_dist))

        # Event Heatmap
        p_heat = generate_event_heatmap(df)
        self.assertTrue(os.path.exists(p_heat))

        # K-Means
        df_c, clusters, p_clust = perform_kmeans_clustering(df, n_clusters=3)
        self.assertIn("cluster_id", df_c.columns)
        self.assertEqual(len(clusters), 3)
        self.assertTrue(os.path.exists(p_clust))

        # Cohort Risk Profile
        stats, p_cohort = get_cohort_risk_profile(df)
        self.assertIn("total_sessions", stats)
        self.assertTrue(os.path.exists(p_cohort))

    # =========================================================
    # 5. LANGCHAIN AI INTEGRITY REPORT AGENT TESTS
    # =========================================================

    def test_09_ai_integrity_report_generation(self):
        """Test AI summary generation (with LLM and deterministic fallback)."""
        metrics = evaluate_session_integrity(
            tab_switches=2,
            focus_losses=1,
            face_missing_count=1,
            face_absent_seconds=40
        )
        report = generate_ai_summary(metrics, score=9, percentage=90.0)
        self.assertIsInstance(report, str)
        self.assertGreater(len(report.strip()), 40)
        self.assertTrue(any(word in report.lower() for word in ["integrity", "score", "risk", "tab", "summary", "recommendation"]))

    # =========================================================
    # 6. ALERT & EVIDENCE MANAGEMENT TESTS
    # =========================================================

    def test_10_evidence_persistence_and_isolation(self):
        """Test incident evidence saving, isolation, and safe retrieval."""
        # Create a dummy blank frame
        dummy_frame = np.zeros((240, 320, 3), dtype=np.uint8)
        filename = capture_incident_snapshot(
            session_id=888,
            frame=dummy_frame,
            event_type="Multiple Faces",
            description="Test unit snapshot"
        )
        self.assertIsNotNone(filename)

        evidence = get_evidence_for_session(888)
        self.assertGreaterEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["event_type"], "Multiple Faces")

        # Verify session isolation
        other_evidence = get_evidence_for_session(999999)
        self.assertEqual(len(other_evidence), 0)

    # =========================================================
    # 7. MILESTONE 1 & 2 NON-REGRESSION TESTS
    # =========================================================

    def test_11_milestone_1_and_2_integrity(self):
        """Verify Milestone 1 question fetching and session creation still work."""
        questions = get_random_questions(limit=5)
        self.assertGreaterEqual(len(questions), 1)

        # Test session finalization
        sess_id = create_exam_session(candidate_id=1)
        self.assertIsNotNone(sess_id)

        finalize_session(
            session_id=sess_id,
            integrity_score=92,
            risk_level="Low",
            face_presence_ratio=98.5,
            face_absent_duration=25,
            ai_summary="Session test summary.",
            status="Completed"
        )

        sess = get_session_by_id(sess_id)
        self.assertEqual(sess["status"], "Completed")
        self.assertEqual(sess["integrity_score"], 92)
        self.assertEqual(sess["risk_level"], "Low")
        self.assertEqual(sess["face_presence_ratio"], 98.5)


if __name__ == "__main__":
    unittest.main()
