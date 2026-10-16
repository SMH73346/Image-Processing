r"""
Product Image Studio - command line.

Runs any combination of the five steps (remove background, clean up, new background,
resize/frame, convert/compress), usually via a preset.

Examples (from this folder):
  .venv\Scripts\python.exe process.py                                  # "Shopify product" preset, all images
  .venv\Scripts\python.exe process.py --only name1 name2               # selected images (base names)
  .venv\Scripts\python.exe process.py --preset "Transparent PNG" --out transparent
  .venv\Scripts\python.exe process.py --preset "Just compress" --src "C:\photos" --out "C:\photos\web"
  .venv\Scripts\python.exe process.py --bg white --format jpg --quality 90
  .venv\Scripts\python.exe process.py --steps framing export --shape original
  .venv\Scripts\python.exe process.py --list-presets
"""
import argparse
import sys
from pathlib import Path

from core import STEPS, find_images, list_presets, load_preset, run_batch, validate
from core.settings import BACKGROUNDS, DEFAULT_QUALITY, FORMATS, SHAPES

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "Original Images"
CUTOUTS = HERE / "cutouts"
OUTPUT = HERE / "output"


def main() -> None:
    ap = argparse.ArgumentParser(description="Batch product image processing.")
    ap.add_argument("--preset", default="Shopify product", help="preset name (see --list-presets)")
    ap.add_argument("--list-presets", action="store_true", help="show available presets and exit")
    ap.add_argument("--steps", nargs="+", choices=list(STEPS), help="override the preset's steps")
    ap.add_argument("--src", default=str(SRC), help="folder with the original images")
    ap.add_argument("--out", default=str(OUTPUT), help="output folder")
    ap.add_argument("--cache", default=str(CUTOUTS), help="folder for cached AI cut-outs")
    ap.add_argument("--only", nargs="*", help="base names to process")
    ap.add_argument("--recut", action="store_true", help="redo background removal even if cached")
    ap.add_argument("--bg", choices=BACKGROUNDS, help="background style")
    ap.add_argument("--color", help="custom background colour, e.g. #f2f2f2 (with --bg custom)")
    ap.add_argument("--no-shadow", action="store_true", help="no shadow under the product")
    ap.add_argument("--size", type=int, help="long side of the output in pixels")
    ap.add_argument("--shape", choices=SHAPES, help="square canvas or keep the original shape")
    ap.add_argument("--format", choices=FORMATS, help="output format")
    ap.add_argument("--quality", type=int, help="output quality 1-100")
    args = ap.parse_args()

    if args.list_presets:
        print("\n".join(list_presets()))
        return

    s = load_preset(args.preset)
    if args.steps:
        s.steps = [st for st in STEPS if st in args.steps]
    for opt, attr in (("bg", "background"), ("color", "custom_color"), ("size", "size"),
                      ("shape", "shape"), ("format", "format"), ("quality", "quality")):
        if getattr(args, opt) is not None:
            setattr(s, attr, getattr(args, opt))
    if args.format and args.quality is None:
        s.quality = DEFAULT_QUALITY[args.format]
    if args.no_shadow:
        s.shadow = False

    errors, warnings = validate(s)
    for w in warnings:
        print("Note:", w)
    if errors:
        sys.exit("Error: " + " ".join(errors))

    files = find_images(Path(args.src), args.only)
    if args.only:
        missing = set(args.only) - {p.stem for p in files}
        if missing:
            print("Not found:", ", ".join(sorted(missing)))
    print(f"Preset '{args.preset}', steps: {', '.join(STEPS[st] for st in s.steps)}; {len(files)} image(s)")

    def progress(i, n, r):
        label = f"-> {r.out.name} ({r.message}, {r.seconds:.0f}s{', AI' if r.used_ai else ''})" if r.ok \
            else f"FAILED: {r.message}"
        print(f"[{i}/{n}] {r.src.name} {label}", flush=True)

    results = run_batch(files, s, Path(args.cache), Path(args.out), args.recut, on_progress=progress)
    failed = [r.src.name for r in results if not r.ok]
    if failed:
        print("\nFailed:", *failed, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
