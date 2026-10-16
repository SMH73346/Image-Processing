"""Runs the selected steps for one image or a whole batch."""
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image, ImageOps

from . import background, cleanup, cutout, export, framing, touchup
from .settings import STEPS, Settings

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}


@dataclass
class ImageResult:
    src: Path
    out: Path | None = None
    ok: bool = False
    message: str = ""
    seconds: float = 0.0
    used_ai: bool = False       # the AI model ran for this image (not taken from the cache)


def find_images(src_dir: Path, only: Iterable[str] | None = None) -> list[Path]:
    """Image files in a folder, sorted; optionally only the given base names."""
    files = sorted(p for p in Path(src_dir).iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    if only:
        wanted = set(only)
        files = [p for p in files if p.stem in wanted]
    return files


def needs_cutout(s: Settings) -> bool:
    return s.has("remove_bg") or s.has("cleanup") or s.has("background")


def result_is_transparent(s: Settings) -> bool:
    if not needs_cutout(s):
        return False
    return not s.has("background") or s.background == "transparent"


def validate(s: Settings) -> tuple[list[str], list[str]]:
    """Check a step combination. Returns (errors that block running, warnings to show)."""
    errors, warnings = [], []
    unknown = [st for st in s.steps if st not in STEPS]
    if unknown:
        errors.append(f"Unknown step(s): {', '.join(unknown)}")
    if not s.steps:
        errors.append("Select at least one step.")
    fmt = s.format if s.has("export") else None
    if result_is_transparent(s) and fmt == "jpg":
        errors.append("JPG can't be transparent. Choose PNG, WebP or AVIF, or pick a background.")
    if (s.has("cleanup") or s.has("background")) and not s.has("remove_bg"):
        warnings.append("Remove background is off: saved cut-outs will be used, "
                        "and images without one will be skipped.")
    if s.has("background") and s.background == "transparent" and s.shadow:
        warnings.append("The shadow will be saved as a semi-transparent layer.")
    if not s.has("export"):
        warnings.append("Convert is off: images are saved in their original format at high quality.")
    return errors, warnings


def process_image(src: Path, s: Settings, cache_dir: Path, out_dir: Path,
                  force_recut: bool = False) -> ImageResult:
    t0 = time.time()
    res = ImageResult(src=src)
    try:
        if needs_cutout(s):
            cut_path = cutout.cached_cutout(src, cache_dir)
            if s.has("remove_bg") and (force_recut or not cutout.is_cached(src, cache_dir)):
                cutout.save_cutout(cutout.cut_out(src, s.model, s.seg_max), cut_path)
                touchup.clear_history(Path(cache_dir), src.stem)  # old touch-up backups no longer apply
                res.used_ai = True
            if not cut_path.exists():
                raise RuntimeError("no saved cut-out; turn on Remove background")
            rgba = Image.open(cut_path).convert("RGBA")

            if s.has("cleanup"):
                rgba = cleanup.clean_cutout(rgba, cutout.open_rgb(src), s.min_part, s.dark_bg_threshold)

            if s.has("framing"):
                cw, ch = framing.canvas_size(rgba.width, rgba.height, s.size, s.shape)
                layer = framing.place_product(rgba, cw, ch, s.fill, s.center_y, s.max_upscale,
                                              s.keep_edges, s.edge_tol)
            else:
                layer = rgba

            if s.has("background"):
                img = background.compose(layer, s.background, s.custom_color, s.shadow, s.shadow_strength)
            else:
                img = layer  # transparent cut-out
        else:
            img = ImageOps.exif_transpose(Image.open(src))
            has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
            img = img.convert("RGBA" if has_alpha else "RGB")
            if s.has("framing"):
                img = framing.frame_image(img, s.size, s.shape, s.pad_color)

        fmt = s.format if s.has("export") else export.source_format(src)
        quality = s.quality if s.has("export") else 95
        res.out = export.output_path(Path(out_dir), src, fmt, s.name_pattern)
        export.save(img, res.out, fmt, quality)
        res.ok = True
        res.message = f"{res.out.stat().st_size // 1024} KB"
    except Exception as e:  # report and keep going
        res.message = str(e) or e.__class__.__name__
    res.seconds = time.time() - t0
    return res


def run_batch(files: list[Path], s: Settings, cache_dir: Path, out_dir: Path, force_recut: bool = False,
              on_progress: Callable[[int, int, ImageResult], None] | None = None,
              should_cancel: Callable[[], bool] | None = None) -> list[ImageResult]:
    """Process files in order. on_progress(index, total, result) is called after each image;
    should_cancel() is checked before each image."""
    errors, _ = validate(s)
    if errors:
        raise ValueError(" ".join(errors))
    results = []
    for i, src in enumerate(files, 1):
        if should_cancel and should_cancel():
            break
        r = process_image(src, s, Path(cache_dir), Path(out_dir), force_recut)
        results.append(r)
        if on_progress:
            on_progress(i, len(files), r)
    return results
