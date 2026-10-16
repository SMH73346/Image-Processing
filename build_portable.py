r"""Build the portable package: one folder (and zip) that runs on another Windows PC with
nothing installed - Python, all libraries, the AI model and the app are inside.

  .venv\Scripts\python.exe build_portable.py [--out C:\path\to\folder] [--no-zip]

Result (default): ..\_portable\ProductImageStudio\  and  ..\_portable\ProductImageStudio-portable.zip
"""
import argparse
import shutil
import sys
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON_HOME = Path(sys.base_prefix)                     # the Python install the .venv was made from
SITE_PACKAGES = HERE / ".venv" / "Lib" / "site-packages"
MODEL = Path.home() / ".rembg" / "models" / "birefnet-general" / "birefnet-general.onnx"
SYSTEM32 = Path(r"C:\Windows\System32")
# Visual C++ runtime, shipped next to python.exe so PCs without the VC++ redistributable work too.
VC_RUNTIME = ["msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "vcruntime140.dll", "vcruntime140_1.dll",
              "concrt140.dll", "vcomp140.dll"]
APP_FILES = ["app.py", "process.py", "compare.py", "README.md", "TEST-CHECKLIST.md", "requirements.txt"]
SKIP_PY_DIRS = {"Doc", "include", "libs", "Scripts"}    # not needed to run
SKIP_NAMES = shutil.ignore_patterns("__pycache__", "*.pyc", "test", "tests", "idle_test")

START_BAT = r"""@echo off
rem Product Image Studio (portable). Close this window to stop the app.
cd /d "%~dp0"
set "REMBG_HOME=%~dp0ai-model"
set "PYTHONNOUSERSITE=1"
set "PYTHONHOME="
set "PYTHONPATH="
set "GRADIO_ANALYTICS_ENABLED=False"
title Product Image Studio
echo Starting Product Image Studio... your browser will open in a moment.
echo Keep this window open while you use the app. Close it to stop the app.
echo.
"%~dp0python\python.exe" "%~dp0app\app.py"
if errorlevel 1 pause
"""

CLI_BAT = r"""@echo off
rem Opens a command prompt set up for the command-line tool (process.py).
cd /d "%~dp0app"
set "REMBG_HOME=%~dp0ai-model"
set "PYTHONNOUSERSITE=1"
set "PYTHONHOME="
set "PYTHONPATH="
set "PATH=%~dp0python;%PATH%"
echo Product Image Studio - command line
echo   python process.py --list-presets
echo   python process.py --src "C:\photos" --out "C:\photos\done"
echo   python process.py --help
echo.
cmd /k
"""

README_FIRST = """PRODUCT IMAGE STUDIO - portable version
=======================================

Nothing needs to be installed and no internet is needed. Everything is in this folder:
Python, the libraries, the AI model (~1 GB) and the app.

HOW TO USE
1. Unzip this folder somewhere with a SHORT path, for example:  C:\\ProductImageStudio
   (Windows has trouble with very long folder paths.)
2. Double-click  Start.bat
   Your browser opens the app. Keep the black window open while you work; close it to stop.
3. In the app: tab 1 "Project" -> New project -> pick the folder with your photos -> Create.
   Then Settings -> Run -> Review -> Touch-up -> Export.

OTHER FILES
- Command line.bat   command prompt for the command-line tool (process.py)
- app\\README.md      full documentation (tabs, steps, presets, command line)
- app\\TEST-CHECKLIST.md   step-by-step test list
- app\\projects\\      your projects are saved here (settings, review status, results)

NOTES
- The first image that needs the AI takes ~10 s extra while the model loads.
- AI background removal takes ~30 s per image on a typical laptop; everything else ~2 s.
- If Windows SmartScreen warns about Start.bat, choose "More info" -> "Run anyway".
- To move or back up your work, copy the whole folder (projects are inside app\\projects).
"""


def size_mb(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1024 / 1024


def build(out: Path) -> Path:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    t = time.time()

    print(f"Python      {PYTHON_HOME} -> python\\")
    py = out / "python"
    py.mkdir()
    for item in PYTHON_HOME.iterdir():
        if item.name in SKIP_PY_DIRS:
            continue
        if item.is_dir():
            ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "test", "tests", "idle_test",
                                            "site-packages") if item.name == "Lib" else SKIP_NAMES
            shutil.copytree(item, py / item.name, ignore=ignore)
        else:
            shutil.copy2(item, py / item.name)

    print("Libraries   .venv site-packages -> python\\Lib\\site-packages\\")
    shutil.copytree(SITE_PACKAGES, py / "Lib" / "site-packages",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    print("VC runtime  " + ", ".join(VC_RUNTIME))
    for dll in VC_RUNTIME:
        if (SYSTEM32 / dll).exists():
            shutil.copy2(SYSTEM32 / dll, py / dll)

    print("App         core\\, ui\\, " + ", ".join(APP_FILES))
    app = out / "app"
    app.mkdir()
    shutil.copytree(HERE / "core", app / "core", ignore=SKIP_NAMES)
    shutil.copytree(HERE / "ui", app / "ui", ignore=SKIP_NAMES)  # theme, styles, icons and fonts
    for f in APP_FILES:
        shutil.copy2(HERE / f, app / f)
    if (HERE / "presets").exists():
        shutil.copytree(HERE / "presets", app / "presets")
    (app / "projects").mkdir()

    print(f"AI model    {MODEL} -> ai-model\\")
    if not MODEL.exists():
        raise SystemExit("AI model not found - open the app once and load the model first.")
    model_dst = out / "ai-model" / "models" / "birefnet-general"
    model_dst.mkdir(parents=True)
    shutil.copy2(MODEL, model_dst / MODEL.name)

    (out / "Start.bat").write_text(START_BAT, encoding="ascii")
    (out / "Command line.bat").write_text(CLI_BAT, encoding="ascii")
    (out / "README-FIRST.txt").write_text(README_FIRST, encoding="utf-8")
    print(f"Folder done: {size_mb(out):,.0f} MB in {time.time() - t:.0f}s")
    return out


def make_zip(folder: Path) -> Path:
    zip_path = folder.with_name(folder.name + "-portable.zip")
    zip_path.unlink(missing_ok=True)
    t = time.time()
    files = [f for f in folder.rglob("*") if f.is_file()]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for i, f in enumerate(files, 1):
            arc = Path(folder.name) / f.relative_to(folder)
            # the model and other large binaries barely compress: store them to save time
            method = zipfile.ZIP_STORED if f.suffix in (".onnx",) else zipfile.ZIP_DEFLATED
            z.write(f, arc, compress_type=method)
            if i % 5000 == 0:
                print(f"  zipped {i:,}/{len(files):,} files…", flush=True)
    print(f"Zip done: {zip_path} ({zip_path.stat().st_size / 1024 / 1024:,.0f} MB, "
          f"{len(files):,} files, {time.time() - t:.0f}s)")
    return zip_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE.parent / "_portable" / "ProductImageStudio"))
    ap.add_argument("--no-zip", action="store_true")
    args = ap.parse_args()
    folder = build(Path(args.out))
    if not args.no_zip:
        make_zip(folder)
