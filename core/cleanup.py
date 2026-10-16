"""Step 2: clean up the AI mask (reflection fragments, dark fringes)."""
import numpy as np
from PIL import Image


def clean_alpha(alpha: np.ndarray, rgb: np.ndarray, min_part: float = 0.03,
                dark_bg_threshold: int = 150) -> np.ndarray:
    """Drop small detached fragments (e.g. bits of a mirror reflection) and, on images
    shot against a dark backdrop, pull the edge in slightly to remove the dark fringe."""
    import cv2

    # dark backdrop? (median of the fully transparent area) - these are the mirror-floor shots
    bg_pixels = rgb[alpha < 8]
    dark = bool(bg_pixels.size) and np.median(bg_pixels) < dark_bg_threshold

    if dark:
        # morphological opening strips thin reflection streaks still attached to the cable
        k = max(3, round(min(alpha.shape) * 0.0025)) | 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
        opened = cv2.morphologyEx((alpha > 96).astype(np.uint8), cv2.MORPH_OPEN, kernel)
        alpha = alpha * cv2.dilate(opened, np.ones((3, 3), np.uint8))

    solid = (alpha > 24).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(solid, connectivity=8)
    if n > 2:
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = np.zeros(n, bool)
        keep[1:] = areas >= max(areas.max() * min_part, 50)
        # dilate the kept parts a little so soft edges belonging to them survive
        kept = cv2.dilate(keep[labels].astype(np.uint8), np.ones((5, 5), np.uint8))
        alpha = alpha * kept

    if dark:  # pull the edge in to remove the dark fringe
        eroded = cv2.erode(alpha, np.ones((3, 3), np.uint8), iterations=1)
        alpha = cv2.GaussianBlur(eroded, (3, 3), 0.8)
    return alpha


def clean_cutout(rgba: Image.Image, original: Image.Image, min_part: float = 0.03,
                 dark_bg_threshold: int = 150) -> Image.Image:
    """Apply clean_alpha to an RGBA cut-out, using the original photo to judge the backdrop."""
    rgb = np.asarray(original.convert("RGB").resize(rgba.size))
    arr = np.asarray(rgba.convert("RGBA")).copy()
    arr[..., 3] = clean_alpha(arr[..., 3], rgb, min_part, dark_bg_threshold)
    return Image.fromarray(arr, "RGBA")
