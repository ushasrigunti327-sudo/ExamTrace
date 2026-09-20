"""
Integrity Scoring Module for Online Exam Monitoring Platform.
Calculates event penalties, face presence ratio, normalized integrity scores (0-100),
and risk classifications using centralized configuration parameters.
"""

from config import Config


def calculate_face_presence_ratio(duration_seconds, face_absent_seconds):
    """
    Calculate the face presence ratio as a percentage.
    Formula: ((Duration - Absent Duration) / Duration) * 100
    Clamped strictly between 0.0 and 100.0%.
    """
    if duration_seconds is None or duration_seconds <= 0:
        duration_seconds = 1800  # Default standard 30-min exam duration

    face_absent_seconds = max(0.0, float(face_absent_seconds or 0.0))
    face_absent_seconds = min(float(duration_seconds), face_absent_seconds)

    present_seconds = float(duration_seconds) - face_absent_seconds
    ratio = (present_seconds / float(duration_seconds)) * 100.0
    return round(max(0.0, min(100.0, ratio)), 2)


def get_risk_level(integrity_score):
    """
    Assign standardized risk classification based on centralized thresholds.
    Score >= 80 -> Low
    Score >= 50 -> Medium
    Score < 50  -> High
    """
    score = int(round(integrity_score))
    if score >= Config.RISK_LOW_THRESHOLD:
        return "Low"
    elif score >= Config.RISK_MEDIUM_THRESHOLD:
        return "Medium"
    else:
        return "High"


def calculate_integrity_score(
    tab_switches=0,
    focus_losses=0,
    face_missing_count=0,
    multiple_face_count=0,
    right_clicks=0,
    copy_attempts=0,
    paste_attempts=0,
    shortcuts=0,
    duration_seconds=1800,
    face_absent_seconds=0
):
    """
    Calculate the final normalized integrity score (0-100) based on weighted event penalties.
    """
    # Event penalty deductions
    penalty = 0
    penalty += int(tab_switches or 0) * Config.PENALTY_TAB_SWITCH
    penalty += int(focus_losses or 0) * Config.PENALTY_FOCUS_LOSS
    penalty += int(copy_attempts or 0) * Config.PENALTY_COPY
    penalty += int(paste_attempts or 0) * Config.PENALTY_PASTE
    penalty += int(right_clicks or 0) * Config.PENALTY_RIGHT_CLICK
    penalty += int(shortcuts or 0) * Config.PENALTY_SHORTCUT
    penalty += int(face_missing_count or 0) * Config.PENALTY_FACE_MISSING
    penalty += int(multiple_face_count or 0) * Config.PENALTY_MULTIPLE_FACES

    # Additional deduction if face presence ratio falls significantly below acceptable threshold
    ratio = calculate_face_presence_ratio(duration_seconds, face_absent_seconds)
    if ratio < 80.0:
        # Deduct 1 point for every 2% drop below 80%
        ratio_penalty = int((80.0 - ratio) / 2.0)
        penalty += max(0, ratio_penalty)

    raw_score = 100 - penalty
    normalized_score = max(0, min(100, int(round(raw_score))))
    return normalized_score


def evaluate_session_integrity(
    tab_switches=0,
    focus_losses=0,
    face_missing_count=0,
    multiple_face_count=0,
    right_clicks=0,
    copy_attempts=0,
    paste_attempts=0,
    shortcuts=0,
    duration_seconds=1800,
    face_absent_seconds=0
):
    """
    Produce a complete structured integrity evaluation for a session.
    """
    ratio = calculate_face_presence_ratio(duration_seconds, face_absent_seconds)
    score = calculate_integrity_score(
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
    risk = get_risk_level(score)

    suspicious_count = (
        int(tab_switches or 0)
        + int(focus_losses or 0)
        + int(copy_attempts or 0)
        + int(paste_attempts or 0)
        + int(right_clicks or 0)
        + int(shortcuts or 0)
        + int(face_missing_count or 0)
        + int(multiple_face_count or 0)
    )

    weighted_penalty = 100 - score

    return {
        "duration_seconds": int(duration_seconds),
        "tab_switches": int(tab_switches or 0),
        "focus_losses": int(focus_losses or 0),
        "copy_attempts": int(copy_attempts or 0),
        "paste_attempts": int(paste_attempts or 0),
        "right_clicks": int(right_clicks or 0),
        "shortcuts": int(shortcuts or 0),
        "face_missing_count": int(face_missing_count or 0),
        "multiple_face_count": int(multiple_face_count or 0),
        "face_absent_seconds": int(face_absent_seconds or 0),
        "face_presence_ratio": ratio,
        "suspicious_event_count": suspicious_count,
        "weighted_penalty": weighted_penalty,
        "integrity_score": score,
        "risk_level": risk
    }
