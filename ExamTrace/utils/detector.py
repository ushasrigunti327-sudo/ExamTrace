import cv2


class FaceDetector:

    def __init__(self):

        self.model = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )

    def detect(self, frame):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.equalizeHist(gray)

        faces = self.model.detectMultiScale(

            gray,

            scaleFactor=1.1,

            minNeighbors=6,

            minSize=(70, 70),

            flags=cv2.CASCADE_SCALE_IMAGE

        )

        return faces


detector = FaceDetector()