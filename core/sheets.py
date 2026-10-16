"""Thumbnails for the GUI and before/after contact sheets."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


def thumbnail(path: Path, thumbs_dir: Path, size: int = 320) -> Path:
    """Small JPG copy of an image (cached; redone when the image changes). Transparent areas
    are shown on a checkerboard so cut-outs stay visible."""
    path = Path(path)
    dst = thumbs_dir / f"{size}" / f"{path.stem}.{path.suffix.lstrip('.')}.jpg"
    if dst.exists() and dst.stat().st_mtime >= path.stat().st_mtime:
        return dst
    im = ImageOps.exif_transpose(Image.open(path))
    im.thumbnail((size, size), Image.LANCZOS)
    if im.mode in ("RGBA", "LA", "P"):
        im = on_checkerboard(im.convert("RGBA"))
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(dst, quality=85)
    return dst


def on_checkerboard(rgba: Image.Image, cell: int = 12) -> Image.Image:
    board = Image.new("RGB", rgba.size, (58, 58, 58))
    d = ImageDraw.Draw(board)
    for y in range(0, rgba.height, cell):
        for x in range(0, rgba.width, cell):
            if (x // cell + y // cell) % 2:
                d.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(78, 78, 78))
    board.paste(rgba, (0, 0), rgba)
    return board


def contact_sheets(pairs: list[tuple[Path, Path]], out_dir: Path, cell: int = 300,
                   per_row: int = 3, rows: int = 5) -> list[Path]:
    """Before/after sheets: each tile shows the original (left) and the result (right)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("review-*.jpg"):
        old.unlink()
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    gap, label = 16, 26
    tile_w, tile_h = cell * 2 + 4, cell + label
    per_sheet = per_row * rows
    sheets = []
    for s in range(0, len(pairs), per_sheet):
        chunk = pairs[s:s + per_sheet]
        n_rows = -(-len(chunk) // per_row)
        sheet = Image.new("RGB", (per_row * (tile_w + gap) + gap, n_rows * (tile_h + gap) + gap), (235, 235, 235))
        draw = ImageDraw.Draw(sheet)
        for i, (src, out) in enumerate(chunk):
            x0 = gap + (i % per_row) * (tile_w + gap)
            y0 = gap + (i // per_row) * (tile_h + gap)
            draw.rectangle((x0 - 1, y0 - 1, x0 + tile_w, y0 + tile_h), fill="white")
            for col, path in enumerate((src, out)):
                im = ImageOps.contain(ImageOps.exif_transpose(Image.open(path)), (cell, cell))
                if im.mode in ("RGBA", "LA", "P"):
                    im = on_checkerboard(im.convert("RGBA"))
                sheet.paste(im.convert("RGB"), (x0 + col * (cell + 4) + (cell - im.width) // 2,
                                                y0 + (cell - im.height) // 2))
            draw.text((x0 + 4, y0 + cell + 5), f"{s + i + 1}. {Path(src).stem}", fill="black", font=font)
        path = out_dir / f"review-{s // per_sheet + 1:02d}.jpg"
        sheet.save(path, quality=88)
        sheets.append(path)
    return sheets
