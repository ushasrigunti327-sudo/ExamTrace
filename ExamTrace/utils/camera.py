import cv2
import threading
import time

from utils.detector import detector
from utils.monitor import monitor
from models.face_log import save_face_log


class Camera:

    def __init__(self):
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None

        self.lock = threading.Lock()

    # ==================================================
    # START
    # ==================================================

    def start(self):

        if self.running:
            return

        print("[CAMERA] Starting...")

        self.cap = cv2.VideoCapture(
            0,
            cv2.CAP_DSHOW
        )

        if not self.cap.isOpened():

            print("[CAMERA] ERROR: Cannot open camera")

            self.cap.release()
            self.cap = None

            return

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            640
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            480
        )

        # Keep only the newest camera frame
        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1
        )

        self.running = True

        self.thread = threading.Thread(
            target=self.update,
            daemon=True
        )

        self.thread.start()

        print("[CAMERA] Started")

    # ==================================================
    # CAMERA LOOP
    # ==================================================

    def update(self):

        while self.running:

            if self.cap is None:
                time.sleep(0.02)
                continue

            success, frame = self.cap.read()

            if not success:

                print(
                    "[CAMERA] Frame read failed"
                )

                time.sleep(0.05)

                continue

            # Mirror camera
            frame = cv2.flip(
                frame,
                1
            )

            # ------------------------------------------
            # FACE DETECTION
            # ------------------------------------------

            try:

                faces = detector.detect(
                    frame
                )

            except Exception as e:

                print(
                    "[CAMERA] Detection error:",
                    e
                )

                faces = []

            face_count = len(faces)

            # ------------------------------------------
            # MONITOR
            # ------------------------------------------

            previous_status = (
                monitor.face_status
            )

            try:

                monitor.update(
                    face_count
                )

            except Exception as e:

                print(
                    "[CAMERA] Monitor error:",
                    e
                )

            current_status = (
                monitor.face_status
            )

            # ------------------------------------------
            # LOG STATUS CHANGES
            # ------------------------------------------

            if (
                current_status
                != previous_status
            ):

                try:

                    if current_status == "Face Missing":

                        save_face_log(
                            monitor.session_id,
                            "Face Missing"
                        )
                        if monitor.session_id:
                            try:
                                from utils.evidence_manager import capture_incident_snapshot
                                capture_incident_snapshot(
                                    monitor.session_id,
                                    frame,
                                    "Face Missing",
                                    "Candidate face missing during examination"
                                )
                            except Exception as ev_err:
                                print("[EVIDENCE] Snapshot warning:", ev_err)

                    elif current_status == "Multiple Faces":

                        save_face_log(
                            monitor.session_id,
                            "Multiple Faces"
                        )
                        if monitor.session_id:
                            try:
                                from utils.evidence_manager import capture_incident_snapshot
                                capture_incident_snapshot(
                                    monitor.session_id,
                                    frame,
                                    "Multiple Faces",
                                    "Multiple faces detected in camera feed"
                                )
                            except Exception as ev_err:
                                print("[EVIDENCE] Snapshot warning:", ev_err)

                    elif current_status == "Face Detected":

                        if previous_status in (
                            "Face Missing",
                            "Multiple Faces"
                        ):

                            save_face_log(
                                monitor.session_id,
                                "Face Detected"
                            )

                except Exception as e:

                    print(
                        "[CAMERA] Log error:",
                        e
                    )

            # ------------------------------------------
            # STATUS COLOR
            # ------------------------------------------

            if current_status == "Face Detected":

                color = (
                    0,
                    255,
                    0
                )

            elif current_status == "Face Missing":

                color = (
                    0,
                    0,
                    255
                )

            else:

                color = (
                    0,
                    165,
                    255
                )

            # ------------------------------------------
            # DRAW FACES
            # ------------------------------------------

            for (
                x,
                y,
                w,
                h
            ) in faces:

                cv2.rectangle(

                    frame,

                    (x, y),

                    (
                        x + w,
                        y + h
                    ),

                    color,

                    2
                )

            # ------------------------------------------
            # DRAW STATUS
            # ------------------------------------------

            cv2.putText(

                frame,

                current_status,

                (15, 35),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                color,

                2
            )

            # ------------------------------------------
            # DRAW FACE COUNT
            # ------------------------------------------

            cv2.putText(

                frame,

                f"Faces: {face_count}",

                (15, 70),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (255, 0, 0),

                2
            )

            # ------------------------------------------
            # SAVE LATEST FRAME
            # ------------------------------------------

            with self.lock:

                self.frame = frame

        print(
            "[CAMERA] Camera loop stopped"
        )

    # ==================================================
    # VIDEO STREAM
    # ==================================================

    def generate(self):

        while self.running:

            # Get newest frame
            with self.lock:

                if self.frame is None:

                    frame = None

                else:

                    frame = self.frame.copy()

            if frame is None:

                time.sleep(
                    0.03
                )

                continue

            # ------------------------------------------
            # ENCODE JPEG
            # ------------------------------------------

            try:

                success, buffer = cv2.imencode(

                    ".jpg",

                    frame,

                    [
                        int(
                            cv2.IMWRITE_JPEG_QUALITY
                        ),
                        70
                    ]
                )

            except Exception as e:

                print(
                    "[CAMERA] JPEG error:",
                    e
                )

                time.sleep(
                    0.03
                )

                continue

            if not success:

                time.sleep(
                    0.03
                )

                continue

            # ------------------------------------------
            # SEND FRAME
            # ------------------------------------------

            yield (

                b"--frame\r\n"

                b"Content-Type: image/jpeg\r\n\r\n"

                + buffer.tobytes()

                + b"\r\n"

            )

            # Important:
            # Don't let the generator spin too fast.

            time.sleep(
                0.02
            )

    # ==================================================
    # STOP
    # ==================================================

    def stop(self):

        if not self.running:
            return

        print(
            "[CAMERA] Stopping..."
        )

        self.running = False

        if self.thread:

            self.thread.join(
                timeout=2
            )

        if self.cap:

            self.cap.release()

        self.cap = None

        self.thread = None

        with self.lock:

            self.frame = None

        print(
            "[CAMERA] Stopped"
        )


camera = Camera()