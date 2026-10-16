"""Built-in and user-saved presets (a named Settings)."""
import json
import re
from pathlib import Path

from .settings import Settings

PRESET_DIR = Path(__file__).resolve().parent.parent / "presets"

ALL = ["remove_bg", "cleanup", "background", "framing", "export"]

_BUILTIN = {
    "Shopify product": dict(steps=ALL, background="grey", size=2048, shape="square",
                            format="webp", quality=85),
    "Light studio": dict(steps=ALL, background="light", size=2048, shape="square",
                         format="webp", quality=85),
    "White marketplace": dict(steps=ALL, background="white", shadow=True, shadow_strength=0.6,
                              size=2048, shape="square", format="jpg", quality=90),
    "Transparent PNG": dict(steps=["remove_bg", "cleanup", "framing", "export"], background="transparent",
                            shadow=False, size=2048, shape="square", format="png"),
    "Re-background": dict(steps=["cleanup", "background", "framing", "export"], background="grey",
                          size=2048, shape="square", format="webp", quality=85),
    "Just compress": dict(steps=["framing", "export"], size=2048, shape="original",
                          format="webp", quality=85),
}


def builtin_presets() -> dict[str, Settings]:
    return {name: Settings.from_dict(d) for name, d in _BUILTIN.items()}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "preset"


def list_presets(preset_dir: Path = PRESET_DIR) -> list[str]:
    names = list(_BUILTIN)
    if preset_dir.exists():
        for p in sorted(preset_dir.glob("*.json")):
            name = json.loads(p.read_text(encoding="utf-8")).get("name", p.stem)
            if name not in names:
                names.append(name)
    return names


def load_preset(name: str, preset_dir: Path = PRESET_DIR) -> Settings:
    if name in _BUILTIN:
        return Settings.from_dict(_BUILTIN[name])
    path = preset_dir / f"{_slug(name)}.json"
    if not path.exists():
        raise KeyError(f"preset not found: {name}")
    return Settings.from_dict(json.loads(path.read_text(encoding="utf-8"))["settings"])


def save_preset(name: str, settings: Settings, preset_dir: Path = PRESET_DIR) -> Path:
    if name in _BUILTIN:
        raise ValueError(f"'{name}' is a built-in preset; choose another name")
    preset_dir.mkdir(parents=True, exist_ok=True)
    path = preset_dir / f"{_slug(name)}.json"
    path.write_text(json.dumps({"name": name, "settings": settings.to_dict()}, indent=2), encoding="utf-8")
    return path
