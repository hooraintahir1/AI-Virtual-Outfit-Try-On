import cv2
import numpy as np
import math
from PIL import Image
from bg_remover import ensure_transparent


class OverlayEngine:

    BODY_WIDTH_SCALE = 1.8
    MIN_WIDTH_FACTOR = 1.5
    NECK_FRAC        = 0.08
    BOTTOM_EXTEND    = 0.03

    def __init__(self):
        self._cache = {}

    def _is_top(self, clothing_rgba):
        w, h = clothing_rgba.size

        if h / w > 1.3:
            return False

        return True

    def _crop_transparent(self, pil_img):
        arr = np.array(pil_img)
        if arr.shape[2] < 4:
            return pil_img

        alpha = arr[:, :, 3]
        coords = np.argwhere(alpha > 10)

        if coords.size == 0:
            return pil_img

        y0, x0 = coords.min(axis=0)
        y1, x1 = coords.max(axis=0) + 1

        return pil_img.crop((x0, y0, x1, y1))

    def composite(self, frame_bgr, keypoints, clothing_rgba, cache_key=None):

        if keypoints is None or clothing_rgba is None:
            return frame_bgr

        fh, fw = frame_bgr.shape[:2]

        ls_x, ls_y = keypoints['left_shoulder']
        rs_x, rs_y = keypoints['right_shoulder']
        lh_x, lh_y = keypoints['left_hip']
        rh_x, rh_y = keypoints['right_hip']

        shoulder_span = math.hypot(rs_x - ls_x, rs_y - ls_y)
        hip_span      = math.hypot(rh_x - lh_x, rh_y - lh_y)

        if shoulder_span < 10:
            return frame_bgr

        shoulder_mid_x = (ls_x + rs_x) / 2
        hip_mid_x      = (lh_x + rh_x) / 2
        mid_x          = (shoulder_mid_x + hip_mid_x) / 2

        shoulder_mid_y = (ls_y + rs_y) / 2
        hip_mid_y      = (lh_y + rh_y) / 2
        torso_h        = abs(hip_mid_y - shoulder_mid_y)

        collar_y = max(0, shoulder_mid_y - torso_h * self.NECK_FRAC)

        if cache_key and cache_key in self._cache:
            clean = self._cache[cache_key]
        else:
            clean = ensure_transparent(clothing_rgba)
            clean = self._crop_transparent(clean)   
            if cache_key:
                self._cache[cache_key] = clean

        is_top = self._is_top(clean)

        if is_top:
            floor_y = hip_mid_y + torso_h * 0.4  
        else:
            ankle_ys = [keypoints[k][1] for k in keypoints if 'ankle' in k]
            if ankle_ys:
                floor_y = max(ankle_ys)
            else:
                floor_y = hip_mid_y + torso_h * 2.0

        floor_y = min(floor_y, fh - 2)

        body_span = max(shoulder_span, hip_span)

        target_h = int(floor_y - collar_y)
        target_w = int(max(
            body_span * self.BODY_WIDTH_SCALE,
            shoulder_span * self.MIN_WIDTH_FACTOR
        ))

        target_w = min(target_w, int(fw * 0.95))

        if is_top:
            cw, ch = clean.size
            aspect = cw / ch if ch else 1

            if target_w / aspect <= target_h:
                target_h = int(target_w / aspect)
            else:
                target_w = int(target_h * aspect)

        target_h = max(target_h, 40)
        target_w = max(target_w, 40)

        resized = clean.resize((target_w, target_h), Image.Resampling.LANCZOS)

        arr = np.array(resized)
        alpha = arr[:, :, 3].astype(np.float32)
        arr[:, :, 3] = cv2.GaussianBlur(alpha, (5, 5), 2)
        resized = Image.fromarray(arr.astype(np.uint8))

        paste_x = int(mid_x) - target_w // 2
        paste_y = int(collar_y)

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb).convert('RGBA')

        frame_pil.paste(resized, (paste_x, paste_y), resized)

        return cv2.cvtColor(
            np.array(frame_pil.convert('RGB')), cv2.COLOR_RGB2BGR
        )

    def clear_cache(self):
        self._cache.clear()