"""Manual touch-up of AI cut-outs: paint red to erase, green to restore.

Edits are applied to the cached cut-out's alpha channel (the cut-out PNG keeps the full original
pixels, so restoring simply makes them visible again). The untouched AI result is kept in
<cache>/_history/<name>/ai.png for "Reset", and the state before the last edit in last.png for "Undo".
"""
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from . import background, cleanup, cutout
from .settings import Settings

ERASE_RGB = (255, 59, 48)     # red brush
RESTORE_RGB = (52, 199, 89)   # green brush
BRUSH_OPACITY = 0.6
WORK_MAX = 1600               # longest side of the editing view


def history_dir(cache_dir: Path, stem: str) -> Path:
    return cache_dir / "_history" / stem


def has_ai_backup(cache_dir: Path, stem: str) -> bool:
    return (history_dir(cache_dir, stem) / "ai.png").exists()


def can_undo(cache_dir: Path, stem: str) -> bool:
    return (history_dir(cache_dir, stem) / "last.png").exists()


def clear_history(cache_dir: Path, stem: str) -> None:
    shutil.rmtree(history_dir(cache_dir, stem), ignore_errors=True)


def editing_view(src: Path, cache_dir: Path, s: Settings, on: str = "background") -> Image.Image:
    """What you paint on: the cleaned cut-out at its own resolution (scaled to WORK_MAX),
    shown on the project's background or on a checkerboard."""
    rgba = Image.open(cutout.cached_cutout(src, cache_dir)).convert("RGBA")
    if s.has("cleanup"):
        rgba = cleanup.clean_cutout(rgba, cutout.open_rgb(src), s.min_part, s.dark_bg_threshold)
    if max(rgba.size) > WORK_MAX:
        rgba.thumbnail((WORK_MAX, WORK_MAX), Image.LANCZOS)
    style = s.background if on == "background" and s.background != "transparent" else "checker"
    if style == "checker":
        from .sheets import on_checkerboard
        return on_checkerboard(rgba, cell=max(8, rgba.width // 80))
    return background.compose(rgba, style, s.custom_color, shadow=False)


def stroke_masks(layer: np.ndarray, size: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Split a painted RGBA layer into erase / restore weights (0..1) at the cut-out's size."""
    layer = np.asarray(Image.fromarray(layer.astype(np.uint8), "RGBA").resize(size, Image.BILINEAR), np.float32)
    rgb, a = layer[..., :3], layer[..., 3] / 255.0
    weight = np.clip(a / BRUSH_OPACITY, 0.0, 1.0)
    is_restore = rgb[..., 1] > rgb[..., 0]  # green beats red -> restore
    erase = np.where(~is_restore, weight, 0.0)
    restore = np.where(is_restore, weight, 0.0)
    return erase, restore


def apply_strokes(src: Path, cache_dir: Path, layers: list[np.ndarray]) -> bool:
    """Apply painted layers to the cached cut-out. Returns False if nothing was painted."""
    cut_path = cutout.cached_cutout(src, cache_dir)
    rgba = Image.open(cut_path).convert("RGBA")
    arr = np.asarray(rgba).copy()
    alpha = arr[..., 3].astype(np.float32)
    changed = False
    for layer in layers or []:
        if layer is None or layer.ndim != 3 or layer.shape[2] != 4 or not layer[..., 3].any():
            continue
        erase, restore = stroke_masks(layer, rgba.size)
        alpha = alpha * (1.0 - erase)
        alpha = np.maximum(alpha, restore * 255.0)
        changed = True
    if not changed:
        return False

    hist = history_dir(cache_dir, src.stem)
    hist.mkdir(parents=True, exist_ok=True)
    if not (hist / "ai.png").exists():
        shutil.copy2(cut_path, hist / "ai.png")
    shutil.copy2(cut_path, hist / "last.png")
    arr[..., 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    cutout.save_cutout(Image.fromarray(arr, "RGBA"), cut_path)
    return True


def undo(src: Path, cache_dir: Path) -> bool:
    last = history_dir(cache_dir, src.stem) / "last.png"
    if not last.exists():
        return False
    shutil.copy2(last, cutout.cached_cutout(src, cache_dir))
    last.unlink()
    cutout.cached_cutout(src, cache_dir).touch()  # keep it newer than the source photo
    return True


def reset(src: Path, cache_dir: Path) -> bool:
    """Back to the untouched AI cut-out."""
    ai = history_dir(cache_dir, src.stem) / "ai.png"
    if not ai.exists():
        return False
    shutil.copy2(ai, cutout.cached_cutout(src, cache_dir))
    cutout.cached_cutout(src, cache_dir).touch()
    clear_history(cache_dir, src.stem)
    return True
