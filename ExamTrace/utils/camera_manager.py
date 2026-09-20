import cv2

class CameraManager:

    def __init__(self):
        self.camera = None

    def start(self):

        if self.camera is None:

            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):

        if self.camera is None:
            self.start()

        return self.camera.read()

    def stop(self):

        if self.camera is not None:

            self.camera.release()
            self.camera = None


camera_manager = CameraManager()