"""Product Image Studio - local GUI (Gradio). Start with Start.bat or: .venv\\Scripts\\python.exe app.py"""
import os

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")  # fully offline, no telemetry

import csv
import queue
import socket
import threading
import time
from dataclasses import replace
from pathlib import Path

import gradio as gr

from core import STEPS, list_presets, load_preset, run_batch, save_preset, validate
from core import cutout
from core.pipeline import process_image
from core.projects import PROJECTS_DIR, Project, create_project, list_projects, load_project, settings_hash
from core.settings import DEFAULT_QUALITY, Settings
from core.sheets import contact_sheets, thumbnail
from ui import THEME, assets, h
from ui import layout as L

ROOT = Path(__file__).resolve().parent
MODEL_FILE = (Path(os.environ.get("REMBG_HOME", Path.home() / ".rembg"))  # the portable package sets REMBG_HOME
              / "models" / "birefnet-general" / "birefnet-general.onnx")
AI_SECONDS = 30            # rough time per AI cut-out on a typical laptop CPU
PREVIEW_SIZE = 1024

# labels shown in the UI <-> values used by core
STEP_LABELS = {f"{i}. {label}": key for i, (key, label) in enumerate(STEPS.items(), 1)}
BG_LABELS = {"Studio grey": "grey", "Light grey": "light", "White": "white",
             "Transparent": "transparent", "Custom colour": "custom"}
SHAPE_LABELS = {"Square": "square", "Original shape": "original"}
FMT_LABELS = {"WebP": "webp", "AVIF": "avif", "JPG": "jpg", "PNG": "png"}
SIZES = [1024, 1600, 2048, 2560, 3000]


def UserError(message: str) -> gr.Error:  # noqa: N802
    """An expected message for the user (e.g. 'Nothing to undo'): shown in the app,
    without a Python traceback in the console window."""
    return gr.Error(message, print_exception=False)


def inv(d: dict) -> dict:
    return {v: k for k, v in d.items()}


class AppState:
    project: Project | None = None
    cancel = threading.Event()
    running = False


APP = AppState()


def need_project() -> Project:
    if APP.project is None:
        raise UserError("Open or create a project first (tab 1).")
    return APP.project


def thumbs_dir(p: Project) -> Path:
    return p.dir / "_thumbs"


def fmt_time(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60}:{sec % 60:02d}"


def kb(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{n // 1024} KB"


# ------------------------------------------------------------------ header
def header_html() -> str:
    p = APP.project
    if cutout.model_loaded():
        model = ("ok", "AI model ready")
    elif MODEL_FILE.exists():
        model = ("warn", "AI model on disk · loads on first use")
    else:
        model = ("err", "AI model not downloaded")
    return h.header(p.name if p else None, [("ok", "Offline"), model])


# ------------------------------------------------------------------ settings <-> widgets
def settings_to_values(s: Settings) -> list:
    return [
        [lbl for lbl, key in STEP_LABELS.items() if key in s.steps],
        inv(BG_LABELS)[s.background], s.custom_color, s.shadow, s.shadow_strength,
        inv(SHAPE_LABELS)[s.shape], s.size, round(s.fill * 100), s.max_upscale, s.keep_edges,
        inv(FMT_LABELS)[s.format], s.quality, s.name_pattern,
    ]


def values_to_settings(base: Settings, steps, bg, color, shadow, strength, shape, size, fill,
                       upscale, keep_edges, fmt, quality, pattern) -> Settings:
    return replace(
        base,
        steps=[key for lbl, key in STEP_LABELS.items() if lbl in (steps or [])],
        background=BG_LABELS[bg], custom_color=color or "#ffffff", shadow=bool(shadow),
        shadow_strength=float(strength), shape=SHAPE_LABELS[shape], size=int(size), fill=float(fill) / 100,
        max_upscale=float(upscale), keep_edges=bool(keep_edges), format=FMT_LABELS[fmt],
        quality=int(quality), name_pattern=(pattern or "{name}").strip() or "{name}",
    )


def validation_md(s: Settings) -> str:
    return issues_html(s) or h.msg("Settings saved")


def issues_html(s: Settings) -> str:
    """Validation errors and warnings as notes ('' when there are none)."""
    errors, warnings = validate(s)
    return h.join(*[h.msg(h.esc(e), "err") for e in errors], *[h.msg(h.esc(w), "warn") for w in warnings])


# ------------------------------------------------------------------ tab 1: project
def project_summary(p: Project | None) -> str:
    if p is None:
        return h.note("Open a project, or create a new one on the left.")
    if not p.src_dir.exists():
        return h.note(f"Source folder not found: {h.code(p.src)}", "warn")
    c = p.scan()
    todo_ai = c["images"] - c["cut_out"]
    counts = (f"{h.b(c['images'])} images found · {h.b(c['cut_out'])} already cut out · "
              f"{h.b(c['up_to_date'])} done with the current settings"
              + (f" · {h.span(h.b(c['failed']) + ' failed', 'err-t')}" if c["failed"] else ""))
    return h.card(
        h.heading(p.name), h.para(counts, "muted"),
        h.path_rows([("Source:", p.src_dir), ("Output:", p.out_dir), ("Cut-out cache:", p.cache_dir)]),
        h.note(f"{todo_ai} image(s) still need the AI cut-out (about {fmt_time(todo_ai * AI_SECONDS)}).",
               "info", "sparkle") if todo_ai else "")


def project_gallery(p: Project | None, n: int = 36) -> list:
    if p is None:
        return []
    return [(str(thumbnail(f, thumbs_dir(p), 320)), f.stem) for f in p.images()[:n]]


def project_names() -> list[str]:
    return [p.name for p in list_projects()]


def load_into_ui(p: Project) -> tuple:
    """Everything that changes when a project is opened (order matches PROJECT_OUTPUTS)."""
    APP.project = p
    stems = [f.stem for f in p.images()]
    s = p.get_settings()
    return (
        header_html(), project_summary(p), project_gallery(p),
        gr.update(choices=project_names(), value=p.name),
        gr.update(choices=list_presets(), value=p.preset if p.preset in list_presets() else None),
        *settings_to_values(s), validation_md(s),
        gr.update(choices=stems, value=stems[0] if stems else None),
        gr.update(choices=stems, value=[]),
        run_summary(),
    )


def open_project(name: str):
    if not name:
        raise UserError("Choose a project to open.")
    return load_into_ui(load_project(name))


def new_project(name, src, out, preset):
    try:
        p = create_project(name, src, out.strip() if out else "", preset=preset or "Shopify product")
    except ValueError as e:
        raise UserError(str(e))
    gr.Info(f"Project '{p.name}' created.")
    return load_into_ui(p)


def browse_folder(current: str) -> str:
    """Native Windows folder picker (the app runs on this PC, so the dialog opens here)."""
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    chosen = filedialog.askdirectory(initialdir=current or str(ROOT.parent), title="Choose a folder")
    root.destroy()
    return str(Path(chosen)) if chosen else current


# ------------------------------------------------------------------ tab 2: settings + preview
def on_settings_input(*vals):
    p = need_project()
    s = values_to_settings(p.get_settings(), *vals)
    p.set_settings(s)
    p.save()
    return validation_md(s)


def on_format_input(fmt):
    return DEFAULT_QUALITY[FMT_LABELS[fmt]]


def apply_preset(name):
    p = need_project()
    if not name:
        raise UserError("Choose a preset.")
    s = load_preset(name)
    p.preset = name
    p.set_settings(s)
    p.save()
    return (*settings_to_values(s), validation_md(s))


def save_as_preset(name):
    p = need_project()
    name = (name or "").strip()
    if not name:
        raise UserError("Type a name for the preset.")
    try:
        save_preset(name, p.get_settings())
    except ValueError as e:
        raise UserError(str(e))
    p.preset = name
    p.save()
    gr.Info(f"Preset '{name}' saved.")
    return gr.update(choices=list_presets(), value=name), ""


def framed_like(before: Path, after: Path) -> Path:
    """Fit the original into the result's frame (on a neutral backing) so the before/after
    slider lines up even when the shapes differ."""
    from PIL import Image, ImageOps
    a = Image.open(after)
    b = ImageOps.contain(Image.open(before).convert("RGB"), a.size)
    canvas = Image.new("RGB", a.size, (38, 38, 38))
    canvas.paste(b, ((a.width - b.width) // 2, (a.height - b.height) // 2))
    dst = after.parent / f"{before.stem}.before.jpg"
    canvas.save(dst, quality=88)
    return dst


def render_preview(sample: str, allow_ai: bool = False):
    """Automatic previews never start the slow AI cut-out; the Refresh button may (allow_ai)."""
    p = need_project()
    if not sample:
        return None, h.para("Choose a sample image.", "small muted")
    s = p.get_settings()
    errors, _ = validate(s)
    if errors:
        return gr.update(), h.msg("Fix the settings on the left to see a preview.", "warn")
    src = next((f for f in p.images([sample])), None)
    if src is None:
        return None, h.msg(f"Sample not found: {h.esc(sample)}", "warn")
    ps = replace(s, size=min(s.size, PREVIEW_SIZE), name_pattern="{name}")
    ai = s.has("remove_bg") and not cutout.is_cached(src, p.cache_dir)
    if ai and not allow_ai:
        return None, h.note("This image hasn't been cut out yet. Click <b>Refresh preview</b> to run the AI on "
                            "it (about 30 s, plus about 10 s to load the model the first time).", "info", "sparkle")
    r = process_image(src, ps, p.cache_dir, p.dir / "_preview")
    if not r.ok:
        return gr.update(), h.msg(f"Preview failed: {h.esc(r.message)}", "err")
    after = thumbnail(r.out, p.dir / "_preview" / "_display", PREVIEW_SIZE)
    before = framed_like(thumbnail(src, thumbs_dir(p), PREVIEW_SIZE), after)
    note = (f"Preview {ps.size}px (final {s.size}px) · {s.format.upper()} · "
            f"{kb(r.out.stat().st_size)} at preview size · {r.seconds:.1f}s"
            + (" · includes the one-time AI cut-out for this image" if ai else ""))
    return (str(before), str(after)), h.para(note, "small muted")


# ------------------------------------------------------------------ tab 3: run
def files_for(scope: str, selected: list[str], p: Project) -> list[Path]:
    files = p.images()
    if scope == "Selected images":
        files = [f for f in files if f.stem in set(selected or [])]
    elif scope == "Only images not done yet":
        s, status = p.get_settings(), p.load_status()
        files = [f for f in files if not p.is_up_to_date(f, s, status)]
    return files


def run_summary(scope: str = "All images", selected=None, recut: bool = False) -> str:
    p = APP.project
    if p is None:
        return h.note("Open a project first.")
    files = files_for(scope, selected, p)
    s = p.get_settings()
    ai = sum(1 for f in files if s.has("remove_bg") and (recut or not cutout.is_cached(f, p.cache_dir)))
    est = ai * AI_SECONDS + (len(files) - ai) * 2
    steps = (f"Steps: {', '.join(STEPS[k] for k in s.steps) or 'none'} · "
             f"{s.background if s.has('background') else 'no background'} · {s.size}px {s.shape} · "
             f"{s.format.upper()} q{s.quality}")
    return h.join(h.inset(
        h.para(f"{h.b(len(files))} image(s) to process · {h.b(ai)} need the AI cut-out · "
               f"estimated time {h.b(fmt_time(est))}"),
        h.para(h.esc(steps), "muted"),
        f"<div><span class='muted'>Output folder:</span>{h.code(p.out_dir)}</div>"), issues_html(s))


def progress_html(done: int, total: int, failed: int, elapsed: float, eta: float | None, label: str,
                  busy: bool = False) -> str:
    pct = 0 if total == 0 else int(done * 100 / total)
    eta_txt = f" · about {fmt_time(eta)} left" if eta is not None and done < total else ""
    fail_txt = f" · {h.span(f'{failed} failed', 'err-t')}" if failed else ""
    line = (f"<b>{done} of {total}</b> ({pct}%){fail_txt} · elapsed {fmt_time(elapsed)}{eta_txt}" if total
            else "<b>Ready</b>")
    return h.progress(pct, line, h.esc(label), busy=busy, tone="ok" if total and done == total else "")


def start_run(scope, selected, recut):
    p = need_project()
    if APP.running:
        raise UserError("A run is already in progress.")
    s = p.get_settings()
    errors, _ = validate(s)
    if errors:
        raise UserError(" ".join(errors))
    files = files_for(scope, selected, p)
    if not files:
        yield (progress_html(0, 0, 0, 0, None, "Nothing to process for this selection."),
               None, h.log([]), gr.update(interactive=True), gr.update(interactive=False), header_html())
        return

    APP.cancel.clear()
    APP.running = True
    q: queue.Queue = queue.Queue()

    def worker():
        try:
            needs_ai = s.has("remove_bg") and any(recut or not cutout.is_cached(f, p.cache_dir) for f in files)
            if needs_ai and not cutout.model_loaded(s.model):
                q.put(("msg", "Loading the AI model (about 10 s, first time only)…"))
                cutout.load_model(s.model)
                q.put(("model",))
            run_batch(files, s, p.cache_dir, p.out_dir, recut,
                      on_progress=lambda i, n, r: q.put(("res", r)), should_cancel=APP.cancel.is_set)
        except Exception as e:
            q.put(("err", str(e)))
        finally:
            q.put(("end",))

    t0 = time.time()
    threading.Thread(target=worker, daemon=True).start()
    done = failed = 0
    log: list[tuple[str, str]] = []  # (tone, text) for h.log
    current = None
    label = "Starting…"
    finished = False
    try:
        while not finished:
            try:
                item = q.get(timeout=0.5)
            except queue.Empty:
                item = None
            while item is not None:
                kind = item[0]
                if kind == "msg":
                    label = item[1]
                elif kind == "res":
                    r = item[1]
                    done += 1
                    p.record([r], s)
                    if r.ok:
                        current = str(thumbnail(r.out, thumbs_dir(p), 512))
                        log.append(("ok", f"{r.src.name} → {r.out.name} ({r.message}, {r.seconds:.0f}s"
                                          f"{', AI' if r.used_ai else ''})"))
                    else:
                        failed += 1
                        log.append(("err", f"{r.src.name}: {r.message}"))
                    nxt = files[done].name if done < len(files) else ""
                    label = f"Working on {nxt}…" if nxt else "Finishing…"
                elif kind == "err":
                    log.append(("err", f"Error: {item[1]}"))
                elif kind == "end":
                    finished = True
                item = q.get_nowait() if not q.empty() else None
            elapsed = time.time() - t0
            eta = elapsed / done * (len(files) - done) if done and not finished else None
            if finished:
                if APP.cancel.is_set() and done < len(files):
                    label = f"Cancelled after {done} image(s)."
                else:
                    label = f"Finished: {done - failed} done, {failed} failed. Go to Review or Export."
            yield (progress_html(done, len(files), failed, elapsed, eta, label, busy=not finished), current,
                   h.log(log[-300:]), gr.update(interactive=finished),
                   gr.update(interactive=not finished), header_html())
    finally:
        APP.running = False


def cancel_run():
    if APP.running:
        APP.cancel.set()
        gr.Info("Cancelling after the current image…")


def open_folder(kind: str):
    p = need_project()
    path = {"output": p.out_dir, "source": p.src_dir, "project": p.dir, "sheets": p.dir / "review"}[kind]
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(path)  # Windows Explorer


# ------------------------------------------------------------------ tab 4: review
REVIEW_FILTERS = {"All": "all", "Not reviewed": "not_reviewed", "Needs fix": "needs_fix",
                  "Approved": "approved", "Failed": "failed"}
REVIEW_ICONS = {"approved": "✓", "needs_fix": "⚠", "": "•"}
REVIEW_DETAIL = 1400


def review_state(st: dict | None) -> str:
    """'not_processed', 'failed', 'not_reviewed', 'needs_fix' or 'approved'."""
    if not st:
        return "not_processed"
    if not st["ok"] or not Path(st["out"]).exists():
        return "failed"
    return st.get("review") or "not_reviewed"


def review_items(filter_label: str, search: str) -> list[str]:
    p = APP.project
    if p is None:
        return []
    want = REVIEW_FILTERS.get(filter_label, "all")
    status = p.load_status()
    q = (search or "").strip().lower()
    items = []
    for f in p.images():
        state = review_state(status.get(f.stem))
        if want == "all" and state == "not_processed":
            continue  # nothing to review yet
        if want != "all" and state != want:
            continue
        if q and q not in f.stem.lower():
            continue
        items.append(f.stem)
    return items


def review_counts_md() -> str:
    p = APP.project
    if p is None:
        return h.note("Open a project first.")
    c = p.review_counts()
    return h.badges(h.badge(f"{c['not_reviewed']} not reviewed"),
                    h.badge(f"⚠ {c['needs_fix']} need a fix", "warn"),
                    h.badge(f"✓ {c['approved']} approved", "ok"),
                    h.badge(f"✕ {c['failed']} failed", "err") if c["failed"] else "",
                    h.badge(f"{c['not_processed']} not processed yet") if c["not_processed"] else "")


def review_gallery(items: list[str], current: str | None = None):
    p = APP.project
    if p is None:
        return gr.update(value=[])
    status = p.load_status()
    value = []
    for stem in items:
        st = status.get(stem)
        state = review_state(st)
        img = Path(st["out"]) if state not in ("failed", "not_processed") else Path(st["src"] if st else "")
        if not img.exists():
            img = next(iter(p.images([stem])))
        icon = "✕" if state == "failed" else REVIEW_ICONS.get(st.get("review", "") if st else "", "•")
        value.append((str(thumbnail(img, thumbs_dir(p), 320)), f"{icon} {stem}"))
    idx = items.index(current) if current in items else None
    return gr.update(value=value, selected_index=idx)


def review_detail(stem: str | None):
    """Big before/after, info and note for one image."""
    p = APP.project
    if p is None or not stem:
        return None, h.para("Click an image in the gallery to review it.", "muted"), "", None
    st = p.load_status().get(stem)
    src = next(iter(p.images([stem])), None)
    if src is None:
        return None, h.msg(f"Image not found: {h.esc(stem)}", "warn"), "", None
    state = review_state(st)
    if state in ("failed", "not_processed"):
        msg = st["message"] if st else "not processed yet"
        before = thumbnail(src, thumbs_dir(p), REVIEW_DETAIL)
        info = h.join(h.heading(stem, mono=True), h.msg(h.esc(msg), "err"))
        return (str(before), str(before)), f"<div class='gstack'>{info}</div>", (st or {}).get("note", ""), stem

    from PIL import Image
    out = Path(st["out"])
    after = thumbnail(out, thumbs_dir(p), REVIEW_DETAIL)
    before = framed_like(thumbnail(src, thumbs_dir(p), REVIEW_DETAIL), after)
    with Image.open(out) as im:
        out_dims = f"{im.width}×{im.height}"
    with Image.open(src) as im:
        src_dims = f"{im.width}×{im.height}"
    label = {"approved": "✓ Approved", "needs_fix": "⚠ Needs fix", "not_reviewed": "Not reviewed"}[state]
    stale = "" if st["settings"] == settings_hash(p.get_settings()) else \
        h.msg("Made with different settings than the current ones. Redo to update it.", "warn")
    tone = {"approved": "ok-t", "needs_fix": "warn-t", "not_reviewed": "hl"}[state]
    info = h.join(
        h.heading(stem, mono=True),
        h.para(h.span(f"<b>{label}</b>", tone) +
               h.span(f" · {out.suffix[1:].upper()} {out_dims} · {kb(out.stat().st_size)}", "muted"), "small"),
        h.para(f"Original: {src.suffix[1:].upper()} {src_dims} · {kb(src.stat().st_size)}", "small muted"), stale)
    return (str(before), str(after)), f"<div class='gstack'>{info}</div>", st.get("note", ""), stem


def review_refresh(filter_label, search, current):
    items = review_items(filter_label, search)
    if current not in items:
        current = items[0] if items else None
    return (review_gallery(items, current), review_counts_md(), items, *review_detail(current))


def review_select(evt: gr.SelectData, items):
    stem = items[evt.index] if items and evt.index is not None and evt.index < len(items) else None
    return review_detail(stem)


def review_step(current, items, delta):
    if not items:
        return review_gallery(items), *review_detail(None)
    i = items.index(current) if current in items else -1
    stem = items[max(0, min(len(items) - 1, i + delta))]
    return review_gallery(items, stem), *review_detail(stem)


def review_mark(review, current, note, filter_label, search, items):
    """Set approved / needs fix on the current image, then move on to the next one."""
    p = need_project()
    if not current:
        raise UserError("Select an image first.")
    st = p.load_status().get(current)
    if review_state(st) in ("failed", "not_processed"):
        raise UserError("This image has no result to review. Redo it first.")
    p.set_review([current], review, note or "")
    old_i = items.index(current) if current in items else 0
    new_items = review_items(filter_label, search)
    if current in new_items:  # still listed: go to the next one
        i = new_items.index(current) + 1
        nxt = new_items[i] if i < len(new_items) else current
    else:                      # dropped out of this filter: the next one moved into its place
        nxt = new_items[min(old_i, len(new_items) - 1)] if new_items else None
    return (review_gallery(new_items, nxt), review_counts_md(), new_items, *review_detail(nxt))


def review_save_note(current, note):
    p = APP.project
    if p and current:
        p.set_review([current], None, note or "")


def review_redo(current, recut, filter_label, search):
    """Re-process the current image with the project's current settings."""
    p = need_project()
    if not current:
        raise UserError("Select an image first.")
    src = next(iter(p.images([current])), None)
    if src is None:
        raise UserError(f"Image not found: {current}")
    s = p.get_settings()
    errors, _ = validate(s)
    if errors:
        raise UserError(" ".join(errors))
    if recut and s.has("remove_bg"):
        gr.Info("Running the AI cut-out again (about 30 s)…")
    r = process_image(src, s, p.cache_dir, p.out_dir, force_recut=bool(recut))
    p.record([r], s)
    if r.ok:
        gr.Info(f"Redone: {r.out.name} ({r.message})")
    else:
        gr.Warning(f"Redo failed: {r.message}")
    items = review_items(filter_label, search)
    if current not in items:
        items = items + [current]  # keep it visible while you look at the new result
    return (review_gallery(items, current), review_counts_md(), items, *review_detail(current))


def review_approve_shown(items, filter_label, search, current):
    p = need_project()
    status = p.load_status()
    ok = [s for s in items if review_state(status.get(s)) in ("not_reviewed", "needs_fix", "approved")]
    if not ok:
        raise UserError("Nothing to approve in this view.")
    p.set_review(ok, "approved")
    gr.Info(f"{len(ok)} image(s) approved.")
    return review_refresh(filter_label, search, current)


# ------------------------------------------------------------------ tab 5: touch-up
TU_VIEWS = {"On the background": "background", "On a checkerboard": "checker"}


def tu_order(only_fix: bool) -> list[str]:
    """Images that can be touched up: flagged ones first, then the rest (unless only_fix)."""
    p = APP.project
    if p is None:
        return []
    status = p.load_status()
    fix, rest = [], []
    for f in p.images():
        st = status.get(f.stem)
        if not cutout.cached_cutout(f, p.cache_dir).exists():
            continue
        (fix if st and st.get("review") == "needs_fix" else rest).append(f.stem)
    return fix if only_fix else fix + rest


def tu_choices(only_fix: bool, current: str | None = None):
    p = APP.project
    status = p.load_status() if p else {}
    stems = tu_order(only_fix)
    labels = [(("⚠ " if status.get(s, {}).get("review") == "needs_fix" else "") + s, s) for s in stems]
    value = current if current in stems else (stems[0] if stems else None)
    return gr.update(choices=labels, value=value)


def tu_load(stem: str | None, view: str):
    """Editor background, info and current result for one image (order matches TU_OUTPUTS)."""
    p = APP.project
    empty = {"background": None, "layers": [], "composite": None}
    if p is None or not stem:
        return empty, h.para("Choose an image to touch up.", "small"), None, stem
    s = p.get_settings()
    if not (s.has("remove_bg") or s.has("cleanup") or s.has("background")):
        return empty, h.msg("Touch-up works on cut-outs. Turn on Remove background in Settings.", "warn"), None, stem
    src = next(iter(p.images([stem])), None)
    if src is None or not cutout.cached_cutout(src, p.cache_dir).exists():
        return empty, h.msg(f"No cut-out for {h.esc(stem)} yet. Run it first.", "warn"), None, stem
    import numpy as np
    from core import touchup
    view_img = touchup.editing_view(src, p.cache_dir, s, TU_VIEWS.get(view, "background"))
    st = p.load_status().get(stem, {})
    flags = []
    if st.get("touched"):
        flags.append(h.badge("✎ touched up", "info"))
    if st.get("review") == "needs_fix":
        flags.append(h.badge("⚠ needs fix", "warn"))
    elif st.get("review") == "approved":
        flags.append(h.badge("✓ approved", "ok"))
    info = h.join(
        h.heading(stem, mono=True), h.badges(*flags) if flags else h.para("not reviewed", "small muted"),
        h.note(f"<b>Note:</b> {h.esc(st['note'])}", "warn") if st.get("note") else "",
        h.para(f"Undo available: {'yes' if touchup.can_undo(p.cache_dir, stem) else 'no'} · Reset to AI cut-out: "
               f"{'yes' if touchup.has_ai_backup(p.cache_dir, stem) else 'nothing changed yet'}", "small muted"))
    info = f"<div class='gstack'>{info}</div>"
    result = None
    if st.get("ok") and st.get("out") and Path(st["out"]).exists():
        result = str(thumbnail(Path(st["out"]), thumbs_dir(p), 900))
    rgb = np.asarray(view_img.convert("RGBA"))
    return {"background": rgb, "layers": [], "composite": rgb}, info, result, stem


def _rebuild(p: Project, src: Path) -> None:
    """Re-make the final image from the edited cut-out (no AI), and record it."""
    s = p.get_settings()
    review = p.load_status().get(src.stem, {}).get("review", "")
    r = process_image(src, s, p.cache_dir, p.out_dir)
    p.record([r], s)
    if r.ok and review:  # keep 'needs fix' until you approve it here
        p.set_review([src.stem], review)
    if not r.ok:
        raise UserError(f"Couldn't re-make the image: {r.message}")


def tu_apply(stem, editor, view):
    p = need_project()
    if not stem:
        raise UserError("Choose an image first.")
    from core import touchup
    src = next(iter(p.images([stem])))
    layers = (editor or {}).get("layers") or []
    if not touchup.apply_strokes(src, p.cache_dir, layers):
        raise UserError("Nothing painted yet. Paint red to erase or green to restore, then Apply.")
    _rebuild(p, src)
    p.mark_touched(stem)
    gr.Info("Applied. The final image was re-made.")
    return tu_load(stem, view)


def tu_undo(stem, view):
    p = need_project()
    from core import touchup
    src = next(iter(p.images([stem])), None) if stem else None
    if src is None or not touchup.undo(src, p.cache_dir):
        raise UserError("Nothing to undo.")
    _rebuild(p, src)
    gr.Info("Last change undone.")
    return tu_load(stem, view)


def tu_reset(stem, view):
    p = need_project()
    from core import touchup
    src = next(iter(p.images([stem])), None) if stem else None
    if src is None or not touchup.reset(src, p.cache_dir):
        raise UserError("This cut-out hasn't been changed.")
    _rebuild(p, src)
    p.mark_touched(stem, False)
    gr.Info("Back to the original AI cut-out.")
    return tu_load(stem, view)


def tu_step(stem, only_fix, view, delta):
    stems = tu_order(only_fix)
    if not stems:
        return tu_choices(only_fix), *tu_load(None, view)
    i = stems.index(stem) if stem in stems else -1
    nxt = stems[(i + delta) % len(stems)]
    return tu_choices(only_fix, nxt), *tu_load(nxt, view)


def tu_approve_next(stem, only_fix, view):
    p = need_project()
    if not stem:
        raise UserError("Choose an image first.")
    before = tu_order(only_fix)
    p.set_review([stem], "approved")
    gr.Info(f"{stem} approved.")
    after = tu_order(only_fix)
    if stem in after:
        return tu_step(stem, only_fix, view, +1)
    i = before.index(stem) if stem in before else 0
    nxt = after[min(i, len(after) - 1)] if after else None
    return tu_choices(only_fix, nxt), *tu_load(nxt, view)


def open_in_touchup(stem, view):
    if not stem:
        raise UserError("Select an image first.")
    p = need_project()
    only_fix = p.load_status().get(stem, {}).get("review") == "needs_fix"
    return (gr.Tabs(selected="touchup"), only_fix, tu_choices(only_fix, stem), *tu_load(stem, view))


# ------------------------------------------------------------------ tab 6: export
def done_pairs(p: Project) -> list[tuple[Path, Path, dict]]:
    status = p.load_status()
    pairs = []
    for f in p.images():
        st = status.get(f.stem)
        if st and st["ok"] and Path(st["out"]).exists():
            pairs.append((f, Path(st["out"]), st))
    return pairs


def export_stats() -> str:
    p = APP.project
    if p is None:
        return h.note("Open a project first.")
    pairs = done_pairs(p)
    if not pairs:
        return h.note("No processed images yet. Run the batch first (tab 3).")
    orig = sum(f.stat().st_size for f, _, _ in pairs)
    new = sum(o.stat().st_size for _, o, _ in pairs)
    flagged = sum(1 for *_, st in pairs if st.get("review") == "needs_fix")
    smaller = h.span(f"{100 - new * 100 // max(orig, 1)}% smaller", "ok-t hl")
    return h.card(
        h.para(f"{h.b(len(pairs))} finished image(s) · total {h.b(kb(new))} (originals {kb(orig)}, {smaller})"
               + (f" · {h.span(h.b(flagged) + ' marked as needing a fix', 'warn-t')}" if flagged else ""),
               "muted big"),
        h.path_rows([("Output folder:", p.out_dir)]))


def make_sheets():
    p = need_project()
    pairs = [(f, o) for f, o, _ in done_pairs(p)]
    if not pairs:
        raise UserError("No processed images yet.")
    sheets = contact_sheets(pairs, p.dir / "review")
    gr.Info(f"{len(sheets)} contact sheet(s) created.")
    return [str(x) for x in sheets]


def export_csv():
    p = need_project()
    status = p.load_status()
    path = p.dir / "report.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "original file", "original KB", "output file", "output KB", "status", "review", "message"])
        for f in p.images():
            st = status.get(f.stem, {})
            out = Path(st["out"]) if st.get("out") else None
            w.writerow([f.stem, f.name, f.stat().st_size // 1024,
                        out.name if out and out.exists() else "",
                        out.stat().st_size // 1024 if out and out.exists() else "",
                        "done" if st.get("ok") else ("failed" if st else "not processed"),
                        st.get("review", ""), st.get("message", "") if not st.get("ok") else ""])
    gr.Info("Report saved.")
    return str(path)


# ------------------------------------------------------------------ tab 5: app settings
def model_info() -> str:
    on_disk = f"{MODEL_FILE.stat().st_size / 1024 / 1024:.0f} MB at {h.code(MODEL_FILE)}" if MODEL_FILE.exists() \
        else "not downloaded yet (it downloads once, about 1 GB, on first use)"
    loaded = cutout.model_loaded()
    status = (h.dot("ok") + "loaded in memory" if loaded
              else h.dot("warn" if MODEL_FILE.exists() else "err") + "not loaded yet")
    return h.card(h.kv([
        ("AI model:", "BiRefNet (general), runs locally on this PC's CPU. No internet needed after the "
                      "one-time download."),
        ("Model file:", on_disk), ("Status:", status), ("Projects folder:", h.code(PROJECTS_DIR)),
        ("Gradio:", h.span(gr.__version__, "mono")),
    ]), cls="kvcard")


def load_model_now():
    cutout.load_model()
    return model_info(), header_html()


# ------------------------------------------------------------------ layout
# Look and reusable pieces live in ui/: theme + tokens, icons, HTML helpers (h.*) and layout helpers (L.*).
HOW_TO_TOUCHUP = h.hint(
    "<b>How to use</b><ol>"
    "<li>Pick the <b class='red'>red</b> brush and paint over what should go (e.g. a reflection).</li>"
    "<li>Pick the <b class='green'>green</b> brush and paint over parts of the product that are missing.</li>"
    "<li>Click <b>Apply</b>. The cut-out is updated and the final image is re-made (about 2 s).</li></ol>"
    "Use the editor's eraser or undo to fix a stroke before applying. Zoom with the mouse wheel for small details.")
REVIEW_KEYS = h.hint(
    f"Shortcuts: {h.kbd('A')} approve · {h.kbd('F')} needs fix · {h.kbd('R')} redo · {h.kbd('T')} touch up · "
    f"{h.kbd('←')} {h.kbd('→')} previous / next. Approving or flagging moves on to the next image.")


def build() -> gr.Blocks:
    with gr.Blocks(title="Product Image Studio") as demo:
        header = L.html(header_html())

        with gr.Tabs() as tabs:
            # ---------------------------------------------------------- 1. Project
            with gr.Tab("1 · Project"):
                with gr.Row():
                    with L.side_panel(width=340):
                        project_dd = gr.Dropdown(project_names(), label="Open a project", value=None)
                        open_btn = L.button("Open project", variant="primary", full=True)
                        with gr.Accordion("New project", open=not project_names()):
                            np_name = gr.Textbox(label="Project name", placeholder="e.g. HiFi catalogue October")
                            with L.pair():
                                np_src = gr.Textbox(label="Source folder (original photos)", scale=4,
                                                    elem_classes=["mono-input"])
                                np_src_btn = L.button("Browse…", scale=0)
                            with L.pair():
                                np_out = gr.Textbox(label="Output folder (optional)", scale=4,
                                                    placeholder="default: inside the project folder",
                                                    elem_classes=["mono-input"])
                                np_out_btn = L.button("Browse…", scale=0)
                            np_preset = gr.Dropdown(list_presets(), value="Shopify product", label="Start from preset")
                            create_btn = L.button("Create project", variant="primary", full=True)
                        with L.actions(tall=False):
                            L.button("Open source folder", icon="folder", size="sm").click(
                                lambda: open_folder("source"))
                            L.button("Open output folder", icon="folder", size="sm").click(
                                lambda: open_folder("output"))
                    with L.column():
                        summary_md = L.html(project_summary(None))
                        gallery = gr.Gallery(label="Images in this project", columns=6, height=560,
                                             object_fit="contain", allow_preview=True, elem_classes=L.WELL)

            # ---------------------------------------------------------- 2. Settings
            with gr.Tab("2 · Settings"):
                with gr.Row():
                    with L.side_panel(scale=2, min_width=420):
                        with L.pair():
                            preset_dd = gr.Dropdown(list_presets(), label="Preset", scale=3)
                            apply_btn = L.button("Apply preset", scale=0)
                        with L.pair():
                            preset_name = gr.Textbox(placeholder="New preset name", show_label=False, scale=3)
                            save_preset_btn = L.button("Save as preset", scale=0)
                        steps = gr.CheckboxGroup(list(STEP_LABELS), label="Steps",
                                                 info="Remove background uses the AI (about 30 s per image, "
                                                      "cached). Everything else takes about 2 s.")
                        with gr.Accordion("Background", open=True):
                            bg = gr.Radio(list(BG_LABELS), label="Style")
                            with L.pair():
                                color = gr.ColorPicker(label="Custom colour", scale=0, min_width=120,
                                                       elem_classes=["swatch"])
                                shadow = gr.Checkbox(label="Soft shadow under the product", elem_classes=L.CHIP)
                            strength = gr.Slider(0, 2, step=0.1, label="Shadow strength")
                        with gr.Accordion("Size & framing", open=True):
                            with L.pair():
                                shape = gr.Radio(list(SHAPE_LABELS), label="Shape", scale=3)
                                size = gr.Dropdown(SIZES, label="Output size (px, long side)", scale=2,
                                                   allow_custom_value=True)
                            fill = gr.Slider(50, 100, step=1, label="Product size (% of the frame)")
                            upscale = gr.Slider(1, 4, step=0.1, label="Maximum enlargement",
                                                info="Limits how much small products are blown up (avoids blur).")
                            keep_edges = gr.Checkbox(label="Keep cut-off cables at the frame edge (close-up shots)",
                                                     elem_classes=L.CHIP)
                        with gr.Accordion("Format & quality", open=True):
                            fmt = gr.Radio(list(FMT_LABELS), label="Format",
                                           info="WebP is best for Shopify. AVIF is ~25% smaller. "
                                                "PNG keeps transparency losslessly.")
                            quality = gr.Slider(1, 100, step=1, label="Quality")
                            pattern = gr.Textbox(label="File name pattern", info="{name} = original file name",
                                                 elem_classes=["mono-input"])
                        valid_md = L.html()
                    with L.column(scale=3):
                        with L.pair():
                            sample_dd = gr.Dropdown(label="Preview image", scale=4, filterable=True)
                            refresh_prev = L.button("Refresh preview", icon="refresh", scale=0)
                        preview = gr.ImageSlider(label="Before / after (drag the handle)", type="filepath",
                                                 height=680, interactive=False, elem_classes=L.WELL)
                        preview_note = L.html()

            # ---------------------------------------------------------- 3. Run
            with gr.Tab("3 · Run") as run_tab:
                with gr.Row():
                    with L.side_panel(scale=2, min_width=380):
                        scope = gr.Radio(["All images", "Only images not done yet", "Selected images"],
                                         value="Only images not done yet", label="What to process")
                        selected = gr.Dropdown([], multiselect=True, label="Selected images",
                                               visible=False, filterable=True)
                        recut = gr.Checkbox(label="Redo AI cut-outs even if already saved", value=False,
                                            elem_classes=L.PLAIN_CHIP)
                        run_md = L.html()
                        with L.actions():
                            start_btn = L.button("Start", icon="play", variant="primary")
                            cancel_btn = L.button("Cancel", icon="stop", variant="stop", interactive=False)
                        L.button("Open output folder", icon="folder", full=True).click(lambda: open_folder("output"))
                    with L.column(scale=3):
                        prog = L.html(progress_html(0, 0, 0, 0, None, "Press Start to process the images."))
                        with gr.Row():
                            current_img = gr.Image(label="Last finished image", type="filepath", height=420,
                                                   interactive=False, scale=2, elem_classes=L.WELL)
                            with L.column(scale=3, min_width=300):
                                log_box = L.html(h.log([]))

            # ---------------------------------------------------------- 4. Review
            with gr.Tab("4 · Review", elem_id="review-panel") as review_tab:
                rv_items = gr.State([])
                rv_current = gr.State(None)
                with gr.Row():
                    with L.side_panel(scale=2, min_width=420):
                        rv_counts = L.html()
                        rv_filter = gr.Radio(list(REVIEW_FILTERS), value="Not reviewed", show_label=False)
                        with L.pair():
                            rv_search = gr.Textbox(placeholder="Search by name…", show_label=False, scale=3,
                                                   elem_classes=["search"])
                            rv_approve_all = L.button("Approve all shown", scale=0)
                        rv_gallery = gr.Gallery(show_label=False, columns=4, height=560, object_fit="contain",
                                                allow_preview=False, elem_id="rv-gallery", elem_classes=L.WELL)
                    with L.column(scale=3):
                        rv_view = gr.ImageSlider(label="Before / after (drag the handle)", type="filepath",
                                                 height=560, interactive=False, elem_classes=L.WELL)
                        rv_info = L.html(h.para("Click an image in the gallery to review it.", "muted"))
                        with L.actions():
                            rv_prev = L.button("Previous", icon="arrowl", elem_id="rv-prev")
                            rv_fix = L.button("⚠ Needs fix", kbd="F", tone="warn", elem_id="rv-fix")
                            rv_ok = L.button("✓ Approve", kbd="A", variant="primary", elem_id="rv-approve")
                            rv_next = L.button("Next", icon="arrowr", icon_end=True, elem_id="rv-next")
                        rv_note = gr.Textbox(label="Note (what needs fixing)", lines=2,
                                             placeholder="e.g. reflection left under the box")
                        with gr.Row(elem_classes=["gtools"]):
                            rv_redo = L.button("↻ Redo with current settings", kbd="R", elem_id="rv-redo", scale=0)
                            rv_touch = L.button("✎ Touch up", kbd="T", elem_id="rv-touch", scale=0)
                            rv_recut = gr.Checkbox(label="Also redo the AI cut-out (about 30 s)", value=False,
                                                   elem_classes=L.PLAIN_CHIP)
                        L.html(REVIEW_KEYS)

            # ---------------------------------------------------------- 5. Touch-up
            with gr.Tab("5 · Touch-up", id="touchup") as touchup_tab:
                tu_current = gr.State(None)
                with gr.Row():
                    with L.side_panel(width=300):
                        tu_only_fix = gr.Checkbox(label="Only images marked 'Needs fix'", value=True,
                                                  elem_classes=L.PLAIN_CHIP)
                        tu_image = gr.Dropdown(label="Image", filterable=True)
                        with L.actions(tall=False):
                            tu_prev = L.button("← Previous", size="sm")
                            tu_next = L.button("Next →", size="sm")
                        tu_view = gr.Radio(list(TU_VIEWS), value="On the background", label="Show the cut-out")
                        tu_info = L.html()
                        L.html(HOW_TO_TOUCHUP, elem_classes=["rule-top"])
                    with L.column():
                        tu_editor = gr.ImageEditor(
                            label="Paint: red = erase · green = restore", type="numpy", image_mode="RGBA",
                            sources=(), transforms=(), height=680, interactive=True, elem_classes=L.WELL,
                            layers=gr.LayerOptions(allow_additional_layers=False),
                            brush=gr.Brush(colors=[("#ff3b30", 0.6), ("#34c759", 0.6)],
                                           default_color=("#ff3b30", 0.6), color_mode="fixed", default_size=28),
                            eraser=gr.Eraser(default_size=28),
                        )
                        with L.actions():
                            tu_apply_btn = L.button("Apply", variant="primary")
                            tu_undo_btn = L.button("Undo last apply")
                            tu_reset_btn = L.button("Reset to AI cut-out", variant="stop")
                            tu_approve_btn = L.button("✓ Approve & next")
                    with L.column(width=280):
                        tu_result = gr.Image(label="Final image", type="filepath", interactive=False, height=360,
                                             elem_classes=L.WELL)
                        L.html(h.hint("The final image updates after each Apply, Undo or Reset."))

            # ---------------------------------------------------------- 6. Export
            with gr.Tab("6 · Export") as export_tab:
                export_md = L.html()
                with L.actions():
                    L.button("Open output folder", icon="folder", variant="primary").click(
                        lambda: open_folder("output"))
                    sheets_btn = L.button("Create before/after sheets", icon="compare")
                    csv_btn = L.button("Export CSV report", icon="table")
                    L.button("Open sheets folder", icon="folder").click(lambda: open_folder("sheets"))
                csv_file = gr.File(label="Report", interactive=False, height=130, elem_classes=[*L.WELL, "file"])
                sheets_gallery = gr.Gallery(label="Before/after sheets", columns=2, height=520,
                                            object_fit="contain", elem_classes=L.WELL)

            # ---------------------------------------------------------- ⚙ App
            with gr.Tab("⚙ App") as app_tab:
                app_md = L.html(model_info())
                load_btn = L.button("Load AI model now", icon="chip", tall=True, full=True)

        # ------------------------------------------------------------- wiring
        settings_widgets = [steps, bg, color, shadow, strength, shape, size, fill, upscale, keep_edges,
                            fmt, quality, pattern]
        project_outputs = [header, summary_md, gallery, project_dd, preset_dd, *settings_widgets, valid_md,
                           sample_dd, selected, run_md]

        open_btn.click(open_project, project_dd, project_outputs).then(render_preview, sample_dd,
                                                                       [preview, preview_note])
        create_btn.click(new_project, [np_name, np_src, np_out, np_preset], project_outputs).then(
            render_preview, sample_dd, [preview, preview_note])
        np_src_btn.click(browse_folder, np_src, np_src)
        np_out_btn.click(browse_folder, np_out, np_out)

        # settings: save on every user change, then refresh the preview
        for w in settings_widgets:
            event = w.release if isinstance(w, gr.Slider) else (w.blur if isinstance(w, gr.Textbox) else w.input)
            event(on_settings_input, settings_widgets, valid_md).then(render_preview, sample_dd,
                                                                      [preview, preview_note])
        fmt.input(on_format_input, fmt, quality).then(on_settings_input, settings_widgets, valid_md).then(
            render_preview, sample_dd, [preview, preview_note])
        apply_btn.click(apply_preset, preset_dd, [*settings_widgets, valid_md]).then(
            render_preview, sample_dd, [preview, preview_note])
        save_preset_btn.click(save_as_preset, preset_name, [preset_dd, preset_name])
        sample_dd.input(render_preview, sample_dd, [preview, preview_note])
        refresh_prev.click(lambda smp: render_preview(smp, allow_ai=True), sample_dd, [preview, preview_note])

        # run
        scope.input(lambda sc: gr.update(visible=sc == "Selected images"), scope, selected)
        for w in (scope, selected, recut):
            w.input(run_summary, [scope, selected, recut], run_md)
        run_tab.select(run_summary, [scope, selected, recut], run_md)
        start_btn.click(start_run, [scope, selected, recut],
                        [prog, current_img, log_box, start_btn, cancel_btn, header],
                        concurrency_id="run").then(
            lambda: (gr.update(interactive=True), gr.update(interactive=False)), None, [start_btn, cancel_btn]
        ).then(run_summary, [scope, selected, recut], run_md)
        cancel_btn.click(cancel_run, None, None, queue=False)

        # review
        rv_detail = [rv_view, rv_info, rv_note, rv_current]
        rv_full = [rv_gallery, rv_counts, rv_items, *rv_detail]
        review_tab.select(review_refresh, [rv_filter, rv_search, rv_current], rv_full)
        rv_filter.input(review_refresh, [rv_filter, rv_search, rv_current], rv_full)
        rv_search.submit(review_refresh, [rv_filter, rv_search, rv_current], rv_full)
        rv_gallery.select(review_select, rv_items, rv_detail)
        rv_prev.click(lambda c, i: review_step(c, i, -1), [rv_current, rv_items], [rv_gallery, *rv_detail])
        rv_next.click(lambda c, i: review_step(c, i, +1), [rv_current, rv_items], [rv_gallery, *rv_detail])
        rv_ok.click(lambda *a: review_mark("approved", *a),
                    [rv_current, rv_note, rv_filter, rv_search, rv_items], rv_full)
        rv_fix.click(lambda *a: review_mark("needs_fix", *a),
                     [rv_current, rv_note, rv_filter, rv_search, rv_items], rv_full)
        rv_note.blur(review_save_note, [rv_current, rv_note], None)
        rv_redo.click(review_redo, [rv_current, rv_recut, rv_filter, rv_search], rv_full)
        rv_approve_all.click(review_approve_shown, [rv_items, rv_filter, rv_search, rv_current], rv_full)

        # touch-up. The editor hangs if it receives a new image while it still holds strokes, so every
        # handler updates the other panels first; then the editor is cleared and reloaded separately.
        tu_side = [tu_info, tu_result, tu_current]

        def wire(event, fn, inputs, extra_outputs=()):
            """fn returns (*extra, editor, info, result, current); the editor part is reloaded after."""
            n = len(extra_outputs)

            def without_editor(*a):
                out = fn(*a)
                return (*out[:n], *out[n + 1:])

            event(without_editor, inputs, [*extra_outputs, *tu_side]).success(
                lambda: None, None, tu_editor).then(
                lambda c, v: tu_load(c, v)[0], [tu_current, tu_view], tu_editor)

        first = lambda o: (tu_order(o) or [None])[0]  # noqa: E731
        pick = lambda c, o: c if c in tu_order(o) else first(o)  # noqa: E731  (current if it's in the list)
        wire(touchup_tab.select, lambda c, o, v: (tu_choices(o, pick(c, o)), *tu_load(pick(c, o), v)),
             [tu_current, tu_only_fix, tu_view], [tu_image])
        wire(tu_only_fix.input, lambda o, v: (tu_choices(o), *tu_load(first(o), v)), [tu_only_fix, tu_view],
             [tu_image])
        wire(tu_image.input, tu_load, [tu_image, tu_view])
        wire(tu_view.input, tu_load, [tu_current, tu_view])
        wire(tu_prev.click, lambda c, o, v: tu_step(c, o, v, -1), [tu_current, tu_only_fix, tu_view], [tu_image])
        wire(tu_next.click, lambda c, o, v: tu_step(c, o, v, +1), [tu_current, tu_only_fix, tu_view], [tu_image])
        wire(tu_apply_btn.click, tu_apply, [tu_current, tu_editor, tu_view])
        wire(tu_undo_btn.click, tu_undo, [tu_current, tu_view])
        wire(tu_reset_btn.click, tu_reset, [tu_current, tu_view])
        wire(tu_approve_btn.click, tu_approve_next, [tu_current, tu_only_fix, tu_view], [tu_image])
        wire(rv_touch.click, open_in_touchup, [rv_current, tu_view], [tabs, tu_only_fix, tu_image])

        # export
        export_tab.select(export_stats, None, export_md)
        sheets_btn.click(make_sheets, None, sheets_gallery)
        csv_btn.click(export_csv, None, csv_file)

        # app
        app_tab.select(model_info, None, app_md)
        load_btn.click(load_model_now, None, [app_md, header])

        # reopen the most recent project on start
        def on_load():
            projects = list_projects()
            if not projects:
                return (header_html(), project_summary(None), [], gr.update(choices=[]), gr.update(),
                        *[gr.update()] * len(settings_widgets), "", gr.update(), gr.update(), run_summary())
            return load_into_ui(projects[0])

        demo.load(on_load, None, project_outputs).then(render_preview, sample_dd, [preview, preview_note])
    return demo


def free_port(start: int = 7860) -> int:
    for port in range(start, start + 50):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("no free port")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, help="port (default: first free port from 7860)")
    ap.add_argument("--no-browser", action="store_true", help="don't open the browser automatically")
    args = ap.parse_args()
    build().queue().launch(
        server_name="127.0.0.1", server_port=args.port or free_port(), inbrowser=not args.no_browser,
        theme=THEME, css=assets.css(), js=assets.js(), allowed_paths=[str(ROOT)], footer_links=[],
    )
