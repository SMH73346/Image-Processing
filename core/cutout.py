"""Step 1: AI background removal (rembg + BiRefNet). The model is loaded once and reused."""
from pathlib import Path

from PIL import Image, ImageOps

_sessions = {}


def load_model(model: str = "birefnet-general"):
    """Load (and on first use download, ~1 GB) the segmentation model. Safe to call repeatedly."""
    if model not in _sessions:
        from rembg import new_session
        _sessions[model] = new_session(model)
    return _sessions[model]


def model_loaded(model: str = "birefnet-general") -> bool:
    return model in _sessions


def open_rgb(path: Path) -> Image.Image:
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def cut_out(src: Path, model: str = "birefnet-general", seg_max: int = 3000) -> Image.Image:
    """Return the source image as RGBA with the AI mask as its alpha channel."""
    import warnings

    import numpy as np
    from rembg import remove

    img = open_rgb(src)
    if max(img.size) > seg_max:
        img.thumbnail((seg_max, seg_max), Image.LANCZOS)
    # the model's sigmoid overflows harmlessly on very confident pixels (result is exactly 0 or 1)
    with warnings.catch_warnings(), np.errstate(over="ignore"):
        warnings.filterwarnings("ignore", message="overflow encountered", category=RuntimeWarning)
        mask = remove(img, session=load_model(model), only_mask=True)
    rgba = img.copy()
    rgba.putalpha(mask.convert("L"))
    return rgba


def cached_cutout(src: Path, cache_dir: Path) -> Path:
    return cache_dir / f"{src.stem}.png"


def is_cached(src: Path, cache_dir: Path) -> bool:
    """A cut-out is valid if it exists and is newer than its source photo."""
    cut = cached_cutout(src, cache_dir)
    return cut.exists() and cut.stat().st_mtime >= src.stat().st_mtime


def save_cutout(rgba: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rgba.save(path, optimize=False, compress_level=1)
