"""Step 5: save in the chosen format and quality."""
from pathlib import Path

from PIL import Image

EXTENSIONS = {"webp": ".webp", "avif": ".avif", "jpg": ".jpg", "png": ".png"}


def output_path(out_dir: Path, src: Path, fmt: str, name_pattern: str = "{name}") -> Path:
    return out_dir / (name_pattern.format(name=src.stem) + EXTENSIONS[fmt])


def save(img: Image.Image, path: Path, fmt: str, quality: int = 85) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "jpg":
        if img.mode == "RGBA":  # JPG has no transparency: flatten onto white
            flat = Image.new("RGB", img.size, (255, 255, 255))
            flat.paste(img, (0, 0), img)
            img = flat
        img.convert("RGB").save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    elif fmt == "webp":
        img.save(path, "WEBP", quality=quality, method=6)
    elif fmt == "avif":
        img.save(path, "AVIF", quality=quality)
    elif fmt == "png":
        img.save(path, "PNG", optimize=True)
    else:
        raise ValueError(f"unknown format: {fmt}")


def source_format(src: Path) -> str:
    """Format matching the source file, used when the Convert step is switched off."""
    ext = src.suffix.lower()
    return {".jpg": "jpg", ".jpeg": "jpg", ".png": "png", ".webp": "webp", ".avif": "avif"}.get(ext, "png")
