"""All tunable options in one place. A Settings object fully describes how a batch is processed."""
from dataclasses import asdict, dataclass, field, fields

# The five pipeline steps, in run order.
STEPS = {
    "remove_bg": "Remove background",
    "cleanup": "Clean up",
    "background": "New background",
    "framing": "Resize / frame",
    "export": "Convert / compress",
}

BACKGROUNDS = ("grey", "light", "white", "transparent", "custom")
FORMATS = ("webp", "avif", "jpg", "png")
SHAPES = ("square", "original")
# Recommended quality per format. The scales differ: AVIF 60 is about the visual quality of WebP 85
# at ~25% smaller files. PNG is lossless, so quality doesn't apply.
DEFAULT_QUALITY = {"webp": 85, "avif": 60, "jpg": 90, "png": 100}


@dataclass
class Settings:
    steps: list = field(default_factory=lambda: list(STEPS))

    # 1. remove background
    model: str = "birefnet-general"
    seg_max: int = 3000            # downscale huge originals to this longest side before cutting out

    # 2. clean up
    min_part: float = 0.03         # detached mask pieces smaller than this fraction of the largest are removed
    dark_bg_threshold: int = 150   # originals with a background darker than this get reflection/fringe cleanup

    # 3. background
    background: str = "grey"       # grey | light | white | transparent | custom
    custom_color: str = "#ffffff"
    shadow: bool = True
    shadow_strength: float = 1.0   # 1.0 = default soft studio shadow

    # 4. resize / frame
    size: int = 2048               # long side of the output, in pixels
    shape: str = "square"          # square | original
    fill: float = 0.84             # product occupies at most this fraction of the canvas
    center_y: float = 0.52         # vertical centre of a free-standing product (0 = top, 1 = bottom)
    max_upscale: float = 2.5       # never enlarge the product more than this
    keep_edges: bool = True        # products cut off by the photo edge stay flush with the canvas edge
    edge_tol: float = 0.006        # within this fraction of the photo edge counts as "cut off"
    pad_color: str = "#ffffff"     # padding colour when framing an image without a cut-out

    # 5. convert / compress
    format: str = "webp"           # webp | avif | jpg | png
    quality: int = 85
    name_pattern: str = "{name}"   # {name} = original file name without extension

    def has(self, step: str) -> bool:
        return step in self.steps

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})
