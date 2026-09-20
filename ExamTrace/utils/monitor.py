import time
from config import Config
from utils.scoring import (
    calculate_integrity_score,
    calculate_face_presence_ratio,
    get_risk_level,
    evaluate_session_integrity
)


class ExamMonitor:

    def __init__(self):
        self.reset()

    def reset(self):

        # ==============================
        # FACE MONITORING
        # ==============================

        self.face_status = "Face Detected"

        self.face_missing_count = 0
        self.multiple_face_count = 0

        self._missing_started = None
        self._multiple_started = None

        self._missing_logged = False
        self._multiple_logged = False

        self.face_absent_duration = 0.0
        self._current_absence_start = None

        # ==============================
        # BROWSER MONITORING
        # ==============================

        self.tab_switch_count = 0
        self.focus_loss_count = 0
        self.right_click_count = 0
        self.copy_count = 0
        self.paste_count = 0
        self.shortcut_count = 0

        # ==============================
        # INTEGRITY & RISK
        # ==============================

        self.integrity_score = 100
        self.risk_level = "Low"

        # ==============================
        # SESSION
        # ==============================

        self.candidate_id = None
        self.session_id = None
        self.session_start_time = None
        self.session_end_time = None

        # Camera/session state
        self.active = False

    # ==================================================
    # START NEW SESSION
    # ==================================================

    def start_session(self, session_id=None, candidate_id=None):

        self.reset()

        self.session_id = session_id
        self.candidate_id = candidate_id
        self.session_start_time = time.time()

        self.active = True

        print(
            f"[MONITOR] New session started: {session_id}"
        )

    # ==================================================
    # END SESSION
    # ==================================================

    def end_session(self):

        if self._current_absence_start is not None:
            self.face_absent_duration += time.time() - self._current_absence_start
            self._current_absence_start = None

        self.session_end_time = time.time()
        self.active = False
        self._recalculate_score()

        print(
            f"[MONITOR] Session ended: {self.session_id}"
        )

    # ==================================================
    # DURATION & PRESENCE RATIO HELPERS
    # ==================================================

    def get_duration_seconds(self):
        if self.session_start_time is None:
            return 1800
        end = self.session_end_time if not self.active and self.session_end_time else time.time()
        duration = end - self.session_start_time
        return max(1, int(round(duration)))

    def get_total_face_absent_seconds(self):
        total = self.face_absent_duration
        if self._current_absence_start is not None:
            total += time.time() - self._current_absence_start
        return int(round(total))

    def get_face_presence_ratio(self):
        duration = self.get_duration_seconds()
        absent = self.get_total_face_absent_seconds()
        return calculate_face_presence_ratio(duration, absent)

    def _recalculate_score(self):
        duration = self.get_duration_seconds()
        absent = self.get_total_face_absent_seconds()
        self.integrity_score = calculate_integrity_score(
            tab_switches=self.tab_switch_count,
            focus_losses=self.focus_loss_count,
            face_missing_count=self.face_missing_count,
            multiple_face_count=self.multiple_face_count,
            right_clicks=self.right_click_count,
            copy_attempts=self.copy_count,
            paste_attempts=self.paste_count,
            shortcuts=self.shortcut_count,
            duration_seconds=duration,
            face_absent_seconds=absent
        )
        self.risk_level = get_risk_level(self.integrity_score)
        return self.integrity_score

    def get_metrics_dict(self):
        duration = self.get_duration_seconds()
        absent = self.get_total_face_absent_seconds()
        return evaluate_session_integrity(
            tab_switches=self.tab_switch_count,
            focus_losses=self.focus_loss_count,
            face_missing_count=self.face_missing_count,
            multiple_face_count=self.multiple_face_count,
            right_clicks=self.right_click_count,
            copy_attempts=self.copy_count,
            paste_attempts=self.paste_count,
            shortcuts=self.shortcut_count,
            duration_seconds=duration,
            face_absent_seconds=absent
        )

    # ==================================================
    # FACE DETECTION
    # ==================================================

    def update(self, face_count):

        if not self.active:
            return

        now = time.time()

        # ------------------------------------------
        # NO FACE
        # ------------------------------------------

        if face_count == 0:

            if self._current_absence_start is None:
                self._current_absence_start = now

            if self._missing_started is None:
                self._missing_started = now

            if now - self._missing_started >= 2:

                self.face_status = "Face Missing"

                if not self._missing_logged:

                    self.face_missing_count += 1
                    self._recalculate_score()
                    self._missing_logged = True

            self._multiple_started = None
            self._multiple_logged = False

            return

        # ------------------------------------------
        # ONE FACE
        # ------------------------------------------

        if face_count == 1:

            if self._current_absence_start is not None:
                self.face_absent_duration += now - self._current_absence_start
                self._current_absence_start = None

            self.face_status = "Face Detected"

            self._missing_started = None
            self._multiple_started = None

            self._missing_logged = False
            self._multiple_logged = False

            return

        # ------------------------------------------
        # MULTIPLE FACES
        # ------------------------------------------

        if self._current_absence_start is not None:
            self.face_absent_duration += now - self._current_absence_start
            self._current_absence_start = None

        if self._multiple_started is None:
            self._multiple_started = now

        if now - self._multiple_started >= 2:

            self.face_status = "Multiple Faces"

            if not self._multiple_logged:

                self.multiple_face_count += 1
                self._recalculate_score()
                self._multiple_logged = True

        self._missing_started = None
        self._missing_logged = False

    # ==================================================
    # BROWSER EVENTS
    # ==================================================

    def tab_switch(self):

        if not self.active:
            return

        self.tab_switch_count += 1
        self._recalculate_score()

    def focus_loss(self):

        if not self.active:
            return

        self.focus_loss_count += 1
        self._recalculate_score()

    def right_click(self):

        if not self.active:
            return

        self.right_click_count += 1
        self._recalculate_score()

    def copy(self):

        if not self.active:
            return

        self.copy_count += 1
        self._recalculate_score()

    def paste(self):

        if not self.active:
            return

        self.paste_count += 1
        self._recalculate_score()

    def shortcut(self):

        if not self.active:
            return

        self.shortcut_count += 1
        self._recalculate_score()


monitor = ExamMonitor()