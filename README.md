# Product Image Studio

This tool batch-processes product photos into consistent, store-ready images. It runs fully offline. The originals are never modified.

## The app (recommended)
Double-click **`Start.bat`**. The app opens in your browser. Keep the black window open while you use it, and close that window to stop the app.

| Tab | What you do there |
|---|---|
| **1 · Project** | Open a project, or create one: give it a name, pick the photo folder (Browse…) and optionally an output folder. You'll see how many images were found, how many are already cut out and how many are done. |
| **2 · Settings** | Pick a preset or tick the steps. Then set the background, size and framing, and format. A live before/after preview updates as you change things; drag the handle to compare. Changes are saved to the project automatically. "Save as preset" stores your own combination. |
| **3 · Run** | Process all images, only those not done yet with the current settings, or a selection. It shows a progress bar, the time left, the last finished image and a log, and Cancel stops after the current image. |
| **4 · Review** | Go through the results. You can filter by Not reviewed, Needs fix, Approved or Failed, and search by name. Click an image for a large before/after view and its details. Then **Approve** (A), **Needs fix** (F) with a note, or **Redo** it with the current settings (R), optionally redoing the AI cut-out as well. **← →** move between images, and approving or flagging moves on automatically. "Approve all shown" approves the whole current view. Re-processing an image resets its review. |
| **5 · Touch-up** | Fix cut-outs by hand. Paint **red** over what should go, such as a reflection, and **green** over parts of the product the AI missed. Then click **Apply**: the cut-out is updated and the final image is re-made in about 2 s. **Undo last apply** reverses the last Apply, and **Reset to AI cut-out** goes back to the original AI result. **Approve & next** approves the image and moves to the next flagged one. You can show the cut-out on the project background or on a checkerboard, and the mouse wheel zooms in for small details. From Review, press **T** to open the current image here. |
| **6 · Export** | Shows the total size saved. From here you can open the output folder, create before/after contact sheets, or export a CSV report. |
| **⚙ App** | AI model status and location, and "Load AI model now". |

Each project lives in `projects/<name>/`. It holds the project settings, `status.json` (what's done and with which settings), thumbnails, previews, `review/` sheets and `report.csv`. Cut-outs and output go inside the project folder unless you choose other folders. The "HiFi Catalogue" project uses the existing `cutouts/` and `output/` folders.

Automatic previews never start the slow AI cut-out. For an image that hasn't been cut out yet, click **Refresh preview**.

## The five steps
Run all five steps, or any combination of them.

| # | Step | What it does | Speed |
|---|---|---|---|
| 1 | **Remove background** (`remove_bg`) | Cuts out the product with an AI model (BiRefNet). The results are cached in `cutouts/`. | about 30 s per image (AI) |
| 2 | **Clean up** (`cleanup`) | Removes detached reflection pieces, and the dark fringes left by dark backdrops | fast |
| 3 | **New background** (`background`) | Background: `grey`, `light`, `white`, `transparent` or `custom` colour, with an optional soft shadow | fast |
| 4 | **Resize / frame** (`framing`) | A `square` canvas or the `original` shape, plus output size and product size. Cables cut off in the photo stay at the frame edge. | fast |
| 5 | **Convert / compress** (`export`) | Output format `webp`, `avif`, `jpg` or `png`, and quality | fast |

How the steps depend on each other:
- Steps 2 and 3 need a cut-out. If step 1 is off, saved cut-outs are used, and images without one are skipped.
- Without step 3 the result is transparent.
- JPG can't be transparent.
- With step 5 off, each image is saved in its original format.

## Presets
| Preset | Steps | Result |
|---|---|---|
| Shopify product (default) | all | Grey studio background, 2048 px square WebP |
| Light studio | all | Light-grey background, 2048 px square WebP |
| White marketplace | all | White background with a light shadow, JPG (Amazon or Google Shopping style) |
| Transparent PNG | 1, 2, 4, 5 | Cut-out on transparency, 2048 px square PNG |
| Re-background | 2, 3, 4, 5 | New background from saved cut-outs, with no AI and fast |
| Just compress | 4, 5 | Resize (never enlarge) and convert, with no cut-out |

You can save your own presets with `core.save_preset(...)`; the GUI will have a "Save as preset" button. They're stored in `presets/`.

## Command line
Run these from this folder in PowerShell.

```powershell
.\.venv\Scripts\python.exe process.py                                   # Shopify product, all images
.\.venv\Scripts\python.exe process.py --list-presets
.\.venv\Scripts\python.exe process.py --preset "Transparent PNG" --out transparent
.\.venv\Scripts\python.exe process.py --preset "Just compress" --src "C:\photos" --out "C:\photos\web"
.\.venv\Scripts\python.exe process.py --bg white --format jpg            # override preset options
.\.venv\Scripts\python.exe process.py --bg custom --color "#1e2a3a" --no-shadow
.\.venv\Scripts\python.exe process.py --steps framing export --shape original --size 1600
.\.venv\Scripts\python.exe process.py --only transparent-usb-cable       # selected images (base names)
.\.venv\Scripts\python.exe process.py --recut --only <name>              # redo the AI cut-out
.\.venv\Scripts\python.exe compare.py output review                      # before/after contact sheets
```

Default folders:
- Source: `../Original Images`
- Cut-out cache: `cutouts/` (change it with `--cache`)
- Output: `output/` (change it with `--out`)

A cut-out is redone automatically when its source photo is newer than the cached version.

Quality defaults per format: WebP 85, AVIF 60, JPG 90. AVIF 60 looks about the same as WebP 85 and is about 25% smaller.

## Folders
- `core/` is the processing library, used by `process.py` and by the GUI that's coming next:
  - `settings.py`: all options
  - `presets.py`
  - `pipeline.py`: step order and checks
  - `cutout.py`, `cleanup.py`, `background.py`, `framing.py` and `export.py`: one file per step
- `ui/` is the app's look, shared by every tab (design reference: `Design/`):
  - `theme.py`: the colours (one list, `TOKENS`) and the Gradio theme
  - `html.py`: reusable panels (cards, notes, badges, path rows, progress, log …)
  - `layout.py`: reusable layout pieces (side panel, buttons with icons and key caps, button rows, image panels)
  - `icons.py`, `studio.css`, `studio.js`, and `fonts/` (IBM Plex, bundled so the app stays offline)
- `cutouts/`: cached AI cut-outs as transparent PNGs. Edit these to touch up an image (see below).
- `output/`: finished images.
- `review/`: before/after sheets.

## Manual touch-ups
The easiest way is the app's **Touch-up** tab. Its edits change the cut-out PNG in the cache. The untouched AI result is kept in `<cache>/_history/<name>/ai.png`, which is what "Reset" uses. Running the AI cut-out again (Redo with "Also redo the AI cut-out") replaces any manual edits.

You can also edit `cutouts/<name>.png` in Photopea or GIMP, then run `process.py --only <name>`.

## Portable package (recommended for another PC)
`..\_portable\ProductImageStudio-portable.zip` (about 1.2 GB) contains everything: Python, the libraries, the AI model, the Visual C++ runtime and the app. The other PC needs nothing installed and no internet.

1. Unzip it to a short path, for example `C:\ProductImageStudio`.
2. Double-click `Start.bat`. `README-FIRST.txt` inside the package explains the rest.

To rebuild the package after changing the app, run:

```powershell
.\.venv\Scripts\python.exe build_portable.py              # folder + zip in ..\_portable
.\.venv\Scripts\python.exe build_portable.py --no-zip     # folder only
```

The build includes any presets saved in `presets/`, but not your projects.

## Setting up on another PC (with an internet connection)
1. Install Python 3.12, for example with `winget install Python.Python.3.12`.
2. Copy this folder without `.venv`, `cutouts` and `output`. Keep the folder path short: Windows has trouble with paths over 260 characters.
3. Double-click `Setup.bat`. It creates `.venv`, installs the libraries in `requirements.txt` and downloads the AI model. This takes about 1 GB, one time only, and stores the model in `%USERPROFILE%\.rembg`.
4. After that, it works offline.
