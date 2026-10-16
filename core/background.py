"""Step 3: studio backgrounds and the soft product shadow."""
from functools import lru_cache

import numpy as np
from PIL import Image, ImageColor, ImageFilter


def _grain(w: int, h: int) -> np.ndarray:
    return np.random.default_rng(0).normal(0, 0.6, (h, w))  # anti-banding grain


def grey_background(w: int, h: int) -> Image.Image:
    """Mid-grey studio backdrop matched to the Transparent XL Phono photo: brightest in the
    centre (~160), falling off to darker left/right sides (~100) and slightly darker top/bottom."""
    y = np.linspace(0.0, 1.0, h)[:, None]
    x = np.linspace(0.0, 1.0, w)[None, :]

    peak, peak_at = 161.0, 0.55
    centre = np.where(
        y <= peak_at,
        peak - 19.0 * (np.clip(peak_at - y, 0, None) / peak_at) ** 2,
        peak - 28.0 * (np.clip(y - peak_at, 0, None) / (1 - peak_at)) ** 2.2,
    )
    side = 62.0 * (np.abs(x - 0.5) / 0.5) ** 1.55                 # dark falloff to both sides
    v = centre - side * (1.0 + 0.25 * np.clip(y - 0.6, 0, None))  # a touch darker in the bottom corners

    v = v + _grain(w, h)
    rgb = np.stack([v, v - 1.0, v - 4.0], axis=-1)                # warm neutral tint
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


def light_background(w: int, h: int) -> Image.Image:
    """Light-grey seamless sweep matched to the frontRow Reserve example: cooler/darker top,
    bright spot behind the product, slightly darker floor, gentle vignette."""
    y = np.linspace(0.0, 1.0, h)[:, None]
    x = np.linspace(0.0, 1.0, w)[None, :]

    # vertical sweep: 214 at top -> 241 around 62% -> 229 at bottom
    top, peak, bottom, peak_at = 214.0, 241.0, 229.0, 0.62
    t1 = np.clip(y / peak_at, 0, 1)
    t2 = np.clip((y - peak_at) / (1 - peak_at), 0, 1)
    up = top + (peak - top) * (1 - (1 - t1) ** 2)          # ease-out towards the peak
    down = peak + (bottom - peak) * t2 ** 1.5
    v = np.where(y <= peak_at, up, down)

    # vignette: darken towards left/right edges and corners
    r = np.sqrt(((x - 0.5) / 0.75) ** 2 + ((y - 0.6) / 1.1) ** 2)
    v = v - 16.0 * np.clip(r - 0.35, 0, None) ** 1.6

    v = v + _grain(w, h)
    rgb = np.stack([v, v, v + 4.0], axis=-1)               # slight cool tint
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


@lru_cache(maxsize=8)
def make_background(style: str, w: int, h: int, custom_color: str = "#ffffff") -> Image.Image | None:
    """RGB background of the given size, or None for a transparent result."""
    if style == "grey":
        return grey_background(w, h)
    if style == "light":
        return light_background(w, h)
    if style == "white":
        return Image.new("RGB", (w, h), (255, 255, 255))
    if style == "custom":
        return Image.new("RGB", (w, h), ImageColor.getrgb(custom_color))
    if style == "transparent":
        return None
    raise ValueError(f"unknown background style: {style}")


def shadow_mask(alpha: Image.Image, strength: float = 1.0) -> np.ndarray:
    """Darkening factor (0..1 per pixel) for a soft studio shadow under the product:
    a wide ambient shadow plus a tight contact shadow, both offset downwards."""
    w, h = alpha.size
    unit = min(w, h)
    shadow = np.zeros((h, w), np.float32)
    for blur, offset, opacity in ((unit * 0.022, unit * 0.018, 0.30), (unit * 0.005, unit * 0.005, 0.38)):
        sh = Image.new("L", (w, h), 0)
        sh.paste(alpha, (0, int(offset)))
        sh = sh.filter(ImageFilter.GaussianBlur(blur))
        shadow = np.maximum(shadow, np.asarray(sh, np.float32) / 255.0 * opacity * strength)
    return np.clip(shadow, 0.0, 1.0)


def compose(layer: Image.Image, style: str, custom_color: str = "#ffffff",
            shadow: bool = True, shadow_strength: float = 1.0) -> Image.Image:
    """Put an RGBA product layer onto the chosen background. Returns RGB, or RGBA for transparent."""
    bg = make_background(style, layer.width, layer.height, custom_color)
    alpha = layer.getchannel("A")

    if bg is None:  # transparent: optional shadow becomes semi-transparent black
        out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        if shadow:
            sh = shadow_mask(alpha, shadow_strength)
            out.putalpha(Image.fromarray((sh * 255).astype(np.uint8), "L"))
        return Image.alpha_composite(out, layer)

    canvas = bg.copy()
    if shadow:
        sh = shadow_mask(alpha, shadow_strength)
        base = np.asarray(canvas, np.float32) * (1.0 - sh[..., None])
        canvas = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
    canvas.paste(layer, (0, 0), layer)
    return canvas
