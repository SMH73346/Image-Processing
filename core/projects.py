"""Projects: one batch of photos with its own settings, cut-out cache, output folder and status."""
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import cutout, export
from .pipeline import ImageResult, find_images
from .settings import Settings

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT / "projects"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"


@dataclass
class Project:
    name: str
    src: str                      # folder with the original photos
    out: str = ""                 # finished images (default: <project>/output)
    cache: str = ""               # AI cut-outs (default: <project>/cutouts)
    preset: str = "Shopify product"
    settings: dict = field(default_factory=lambda: Settings().to_dict())
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)

    @property
    def slug(self) -> str:
        return slugify(self.name)

    @property
    def dir(self) -> Path:
        return PROJECTS_DIR / self.slug

    @property
    def src_dir(self) -> Path:
        return Path(self.src)

    @property
    def out_dir(self) -> Path:
        return Path(self.out) if self.out else self.dir / "output"

    @property
    def cache_dir(self) -> Path:
        return Path(self.cache) if self.cache else self.dir / "cutouts"

    def get_settings(self) -> Settings:
        return Settings.from_dict(self.settings)

    def set_settings(self, s: Settings) -> None:
        self.settings = s.to_dict()

    def images(self, only=None) -> list[Path]:
        return find_images(self.src_dir, only) if self.src_dir.exists() else []

    def save(self) -> None:
        self.updated = time.time()
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "project.json").write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    # ---------------------------------------------------------- status per image
    @property
    def status_path(self) -> Path:
        return self.dir / "status.json"

    def load_status(self) -> dict:
        if self.status_path.exists():
            return json.loads(self.status_path.read_text(encoding="utf-8"))
        return {}

    def _write_status(self, status: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.status_path.write_text(json.dumps(status, indent=1), encoding="utf-8")

    def record(self, results: list[ImageResult], s: Settings) -> None:
        """Store run results. A re-processed image is a new result, so its review resets
        (the note is kept, since it usually describes what still needs doing)."""
        status = self.load_status()
        h = settings_hash(s)
        for r in results:
            old = status.get(r.src.stem, {})
            status[r.src.stem] = {
                "src": str(r.src), "out": str(r.out) if r.out else "", "ok": r.ok,
                "message": r.message, "seconds": round(r.seconds, 1), "at": time.time(), "settings": h,
                "review": "", "note": old.get("note", ""),
                "touched": False if r.used_ai else old.get("touched", False),  # a new AI cut-out replaces edits
            }
        self._write_status(status)

    def mark_touched(self, stem: str, touched: bool = True) -> None:
        status = self.load_status()
        if stem in status:
            status[stem]["touched"] = touched
            self._write_status(status)

    def set_review(self, stems: list[str], review: str | None = None, note: str | None = None) -> None:
        """review: 'approved', 'needs_fix' or '' (not reviewed)."""
        if review not in (None, "", "approved", "needs_fix"):
            raise ValueError(f"unknown review state: {review}")
        status = self.load_status()
        for stem in stems:
            if stem not in status:
                continue
            if review is not None:
                status[stem]["review"] = review
            if note is not None:
                status[stem]["note"] = note
        self._write_status(status)

    def review_counts(self) -> dict:
        status = self.load_status()
        names = {f.stem for f in self.images()}
        c = {"all": len(names), "not_reviewed": 0, "needs_fix": 0, "approved": 0, "failed": 0, "not_processed": 0}
        for stem in names:
            st = status.get(stem)
            if not st:
                c["not_processed"] += 1
            elif not st["ok"]:
                c["failed"] += 1
            else:
                c[st.get("review") or "not_reviewed"] += 1
        return c

    def is_up_to_date(self, src: Path, s: Settings, status: dict | None = None) -> bool:
        """Processed successfully with these exact settings, after the photo last changed."""
        st = (status if status is not None else self.load_status()).get(src.stem)
        return bool(st and st["ok"] and st["settings"] == settings_hash(s)
                    and Path(st["out"]).exists() and st["at"] >= src.stat().st_mtime)

    def scan(self) -> dict:
        files = self.images()
        s = self.get_settings()
        status = self.load_status()
        return {
            "images": len(files),
            "cut_out": sum(cutout.is_cached(f, self.cache_dir) for f in files),
            "up_to_date": sum(self.is_up_to_date(f, s, status) for f in files),
            "failed": sum(1 for f in files if f.stem in status and not status[f.stem]["ok"]),
            "src_exists": self.src_dir.exists(),
        }

    def expected_output(self, src: Path) -> Path:
        s = self.get_settings()
        fmt = s.format if s.has("export") else export.source_format(src)
        return export.output_path(self.out_dir, src, fmt, s.name_pattern)


def settings_hash(s: Settings) -> str:
    return hashlib.md5(json.dumps(s.to_dict(), sort_keys=True).encode()).hexdigest()[:12]


def list_projects() -> list[Project]:
    projects = []
    if PROJECTS_DIR.exists():
        for p in PROJECTS_DIR.glob("*/project.json"):
            try:
                projects.append(Project(**json.loads(p.read_text(encoding="utf-8"))))
            except Exception:
                continue  # skip broken project files
    return sorted(projects, key=lambda p: p.updated, reverse=True)


def load_project(name_or_slug: str) -> Project:
    path = PROJECTS_DIR / slugify(name_or_slug) / "project.json"
    return Project(**json.loads(path.read_text(encoding="utf-8")))


def create_project(name: str, src: str, out: str = "", cache: str = "", preset: str = "Shopify product",
                   settings: Settings | None = None) -> Project:
    name = name.strip()
    if not name:
        raise ValueError("Give the project a name.")
    if (PROJECTS_DIR / slugify(name) / "project.json").exists():
        raise ValueError(f"A project called '{name}' already exists.")
    if not Path(src).is_dir():
        raise ValueError(f"Source folder not found: {src}")
    from .presets import load_preset
    p = Project(name=name, src=str(Path(src)), out=out, cache=cache, preset=preset,
                settings=(settings or load_preset(preset)).to_dict())
    p.save()
    return p
