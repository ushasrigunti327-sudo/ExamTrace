class SuspiciousEngine:

    def check(self, monitor):

        alerts = []

        if monitor.face_missing_count >= 2:
            alerts.append(
                "⚠ Candidate repeatedly moved away from the camera."
            )

        if monitor.multiple_face_count >= 1:
            alerts.append(
                "⚠ More than one face was detected during the examination."
            )

        if monitor.tab_switch_count >= 2:
            alerts.append(
                "⚠ Candidate switched browser tabs multiple times."
            )

        if monitor.focus_loss_count >= 2:
            alerts.append(
                "⚠ Exam window lost focus repeatedly."
            )

        if monitor.copy_count > 0:
            alerts.append(
                "⚠ Copy operation detected."
            )

        if monitor.paste_count > 0:
            alerts.append(
                "⚠ Paste operation detected."
            )

        if monitor.right_click_count > 0:
            alerts.append(
                "⚠ Right-click attempt detected."
            )

        if monitor.shortcut_count > 0:
            alerts.append(
                "⚠ Keyboard shortcuts were used."
            )

        return alerts


engine = SuspiciousEngine()