from utils.scoring import (
    calculate_integrity_score as calc_score,
    get_risk_level as calc_risk,
    calculate_face_presence_ratio as calc_ratio
)


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
    Calculate candidate integrity score using centralized scoring engine.
    """
    return calc_score(
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


def calculate_integrity():
    """
    Calculate integrity using the global ExamMonitor.
    """
    from utils.monitor import monitor

    monitor.integrity_score = calculate_integrity_score(
        tab_switches=monitor.tab_switch_count,
        focus_losses=monitor.focus_loss_count,
        face_missing_count=monitor.face_missing_count,
        multiple_face_count=monitor.multiple_face_count,
        right_clicks=monitor.right_click_count,
        copy_attempts=monitor.copy_count,
        paste_attempts=monitor.paste_count,
        shortcuts=monitor.shortcut_count,
        duration_seconds=monitor.get_duration_seconds(),
        face_absent_seconds=monitor.face_absent_duration
    )

    return monitor.integrity_score


def get_risk(score):
    """
    Assign standardized risk classification (Low, Medium, High).
    """
    return calc_risk(score)