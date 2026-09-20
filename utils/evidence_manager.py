"""
Evidence and Alert Management Module.
Captures incident snapshots for critical suspicious events, persists metadata,
and manages secure, session-isolated evidence retrieval for invigilators.
"""

import os
import cv2
import time
from datetime import datetime
from config import Config
from models.evidence import save_evidence, get_session_evidence


# Ensure evidence folder exists
os.makedirs(Config.EVIDENCE_FOLDER, exist_ok=True)


def capture_incident_snapshot(session_id, frame, event_type, description=""):
    """
    Save a suspicious incident frame snapshot to the secure evidence directory
    and record its metadata in the database.
    """
    if session_id is None or frame is None:
        return None

    try:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_event_name = "".join(c for c in event_type if c.isalnum() or c in ("_", "-")).lower()
        filename = f"evidence_s{session_id}_{safe_event_name}_{timestamp_str}.jpg"
        filepath = os.path.join(Config.EVIDENCE_FOLDER, filename)

        # Save frame as JPEG
        cv2.imwrite(filepath, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])

        # Record in database
        save_evidence(
            session_id=session_id,
            event_type=event_type,
            image_path=filename,
            description=description or f"Incident captured for {event_type}"
        )

        print(f"[EVIDENCE] Captured snapshot for session {session_id}: {filename}")
        return filename
    except Exception as e:
        print(f"[EVIDENCE] Error capturing snapshot: {e}")
        return None


def get_evidence_for_session(session_id):
    """
    Retrieve all evidence records for a specific session.
    Verifies that the files exist and sanitizes paths against directory traversal.
    """
    records = get_session_evidence(session_id)
    verified_evidence = []

    for item in records:
        filename = os.path.basename(item["image_path"])
        full_path = os.path.join(Config.EVIDENCE_FOLDER, filename)
        item_copy = dict(item)
        item_copy["filename"] = filename
        item_copy["file_exists"] = os.path.exists(full_path)
        item_copy["url"] = f"/static/evidence/{filename}"
        verified_evidence.append(item_copy)

    return verified_evidence
