import cv2

class CameraModule:

    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            raise RuntimeError(

            )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def read_frame(self):         

        return self.cap.read()

    def release(self):             
        self.cap.release()