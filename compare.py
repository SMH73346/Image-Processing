r"""Build before/after contact sheets.

  compare.py <processed folder> <out folder> [names...]

Each tile shows the original (left) and the processed image (right), numbered and labelled.
Sheets are saved as review-01.jpg, review-02.jpg, ... in <out folder>.
"""
import sys
from pathlib import Path

from core.pipeline import find_images
from core.sheets import contact_sheets

SRC = Path(__file__).resolve().parent.parent / "Original Images"

folder, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
names = sys.argv[3:] or None
pairs = []
for src in find_images(SRC, names):
    done = [p for p in folder.glob(src.stem + ".*") if p.stem == src.stem]
    if done:
        pairs.append((src, done[0]))
sheets = contact_sheets(pairs, out_dir)
print(f"{len(pairs)} images -> {len(sheets)} sheets in {out_dir}")
