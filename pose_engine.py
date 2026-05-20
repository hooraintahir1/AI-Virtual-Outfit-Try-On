import cv2
import mediapipe as mp


class PoseDetectionEngine:
    REQUIRED = {
        'left_shoulder':  11,
        'right_shoulder': 12,
        'left_hip':       23,
        'right_hip':      24,
    }

    OPTIONAL = {
        'nose':            0,
        'left_knee':      25,
        'right_knee':     26,
        'left_ankle':     27,
        'right_ankle':    28,
        'left_foot':      31,
        'right_foot':     32,
    }

    MIN_VIS_REQUIRED = 0.50
    MIN_VIS_OPTIONAL = 0.30

    def __init__(self, static_image_mode=False): 
        self.mp_pose    = mp.solutions.pose
        self.pose_model = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=1,
            smooth_landmarks=not static_image_mode,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def detect(self, frame_bgr):
        h, w = frame_bgr.shape[:2]

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.pose_model.process(rgb)
        rgb.flags.writeable = True

        if results.pose_landmarks is None:
            return None

        lms = results.pose_landmarks.landmark
        kp  = {}

        for name, idx in self.REQUIRED.items():
            lm = lms[idx]
            if lm.visibility < self.MIN_VIS_REQUIRED:
                return None   
            kp[name] = (int(lm.x * w), int(lm.y * h))

        for name, idx in self.OPTIONAL.items():
            lm = lms[idx]
            if lm.visibility >= self.MIN_VIS_OPTIONAL:
                px, py = int(lm.x * w), int(lm.y * h)
                if 0 <= px < w and 0 <= py < h:
                    kp[name] = (px, py)

        return kp

    def close(self):
        self.pose_model.close()