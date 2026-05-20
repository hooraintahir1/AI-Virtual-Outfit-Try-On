
import cv2
import numpy as np
from PIL import Image


def ensure_transparent(pil_image: Image.Image) -> Image.Image:
    img = pil_image.convert('RGBA')
    arr = np.array(img)

    alpha = arr[:, :, 3]
    transparent_ratio = (alpha < 30).sum() / alpha.size
    if transparent_ratio > 0.25:
        return img

    return _remove_background_grabcut(img)


def _remove_background_grabcut(pil_rgba: Image.Image) -> Image.Image:
    rgb = np.array(pil_rgba.convert('RGB'))
    h, w = rgb.shape[:2]

    mask = np.zeros((h, w), np.uint8)

    margin_x = max(10, int(w * 0.05))
    margin_y = max(10, int(h * 0.05))
    rect = (margin_x, margin_y, w - 2*margin_x, h - 2*margin_y)

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    try:
        cv2.grabCut(rgb, mask, rect, bgd_model, fgd_model,
                    5, cv2.GC_INIT_WITH_RECT)
        fg_mask = np.where((mask == 2) | (mask == 0), 0, 255).astype(np.uint8)
    except Exception:
        fg_mask = _color_based_removal(rgb)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN,  kernel, iterations=1)

    fg_mask = cv2.GaussianBlur(fg_mask, (9, 9), sigmaX=4)

    result = np.array(pil_rgba.convert('RGBA'))
    result[:, :, 3] = fg_mask

    return Image.fromarray(result)


def _color_based_removal(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]

    corners = [
        rgb[0, 0], rgb[0, w-1],
        rgb[h-1, 0], rgb[h-1, w-1],
        rgb[0, w//2], rgb[h-1, w//2],
        rgb[h//2, 0], rgb[h//2, w-1],
    ]
    bg_color = np.mean(corners, axis=0).astype(np.uint8)

    diff = np.abs(rgb.astype(np.int32) - bg_color.astype(np.int32))
    dist = np.max(diff, axis=2)

    bg_mask = (dist < 40).astype(np.uint8) * 255
    fg_mask = 255 - bg_mask

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=3)
    fg_mask = cv2.GaussianBlur(fg_mask, (7, 7), sigmaX=3)

    return fg_mask
