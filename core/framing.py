"""Step 4: size and position the product on the output canvas."""
from PIL import Image, ImageColor


def canvas_size(src_w: int, src_h: int, size: int, shape: str) -> tuple[int, int]:
    """Output dimensions: a square, or the source's shape with its long side = size."""
    if shape == "square":
        return size, size
    if src_w >= src_h:
        return size, max(1, round(size * src_h / src_w))
    return max(1, round(size * src_w / src_h)), size


def place_product(rgba: Image.Image, cw: int, ch: int, fill: float = 0.84, center_y: float = 0.52,
                  max_upscale: float = 2.5, keep_edges: bool = True,
                  edge_tol: float = 0.006) -> Image.Image:
    """Return a cw x ch transparent layer with the product positioned on it.

    Normally the product is centred and scaled to `fill` of the canvas. If the product runs off
    an edge of the original photo (close-up shots) and keep_edges is on, that edge stays flush
    with the canvas edge, so cables leave the frame naturally instead of ending in mid-air."""
    W, H = rgba.size
    bbox = rgba.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
    if not bbox:
        raise RuntimeError("empty mask: nothing was cut out")
    l, t, r, b = bbox
    tol = max(2, round(min(W, H) * edge_tol))
    L, T, R, B = (l <= tol, t <= tol, r >= W - tol, b >= H - tol) if keep_edges else (False,) * 4
    pw, ph = r - l, b - t
    cx, cy = (l + r) / 2, (t + b) / 2
    ratio = cw / ch

    # window (in source pixels) with the canvas' aspect ratio that becomes the canvas
    if (L and R) and (T and B):
        ww = min(W, H * ratio)           # fills the photo both ways: crop
    elif L and R:
        ww = W                           # runs off left and right: window spans the full width
    elif T and B:
        ww = H * ratio
    else:
        wh = max(ph / fill, pw / fill / ratio, ch / max_upscale)  # margin, and limit enlargement
        ww = wh * ratio
    wh = ww / ratio

    def start(lo_touch: bool, hi_touch: bool, extent: int, centre: float, side: float, frac: float) -> float:
        if lo_touch and hi_touch:        # crop evenly around the product
            return min(max(centre - side / 2, 0.0), max(extent - side, 0.0))
        if lo_touch:                     # keep the cut edge flush with the canvas edge
            return 0.0
        if hi_touch:
            return extent - side
        return centre - side * frac      # free on this axis: usual placement

    x0 = start(L, R, W, cx, ww, 0.5)
    y0 = start(T, B, H, cy, wh, center_y)

    window = Image.new("RGBA", (round(ww), round(wh)), (0, 0, 0, 0))
    window.paste(rgba, (round(-x0), round(-y0)))   # straight copy keeps soft alpha edges intact
    return window.resize((cw, ch), Image.LANCZOS)


def frame_image(img: Image.Image, size: int, shape: str, pad_color: str = "#ffffff") -> Image.Image:
    """Resize a whole photo (no cut-out): fit inside the canvas, never enlarge, pad if square."""
    cw, ch = canvas_size(img.width, img.height, size, shape)
    scale = min(cw / img.width, ch / img.height, 1.0)
    fitted = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    if shape != "square":
        return fitted
    mode = "RGBA" if fitted.mode == "RGBA" else "RGB"
    color = ImageColor.getrgb(pad_color) + ((0,) if mode == "RGBA" else ())
    canvas = Image.new(mode, (min(cw, max(fitted.size)),) * 2, color)
    canvas.paste(fitted, ((canvas.width - fitted.width) // 2, (canvas.height - fitted.height) // 2))
    return canvas
