"""Product Image Studio core: the processing steps, shared by the command line and the GUI."""
from .settings import STEPS, Settings
from .presets import builtin_presets, list_presets, load_preset, save_preset
from .pipeline import ImageResult, find_images, process_image, run_batch, validate

__all__ = [
    "STEPS", "Settings", "builtin_presets", "list_presets", "load_preset", "save_preset",
    "ImageResult", "find_images", "process_image", "run_batch", "validate",
]
