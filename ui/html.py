"""Reusable HTML pieces for the gr.HTML panels. Every page builds its panels from these, so a style
is defined once (in studio.css) and looks the same everywhere.

Arguments named `text` are plain text and get escaped; `body`/`*parts` are HTML (usually made with
these helpers). Use esc() for any other user or file-system text you put into HTML yourself."""
from html import escape

from .icons import icon

TONE_ICONS = {"info": "info", "ok": "checkcircle", "warn": "warn", "err": "xcircle"}


def esc(text) -> str:
    return escape(str(text), quote=True)


def join(*parts) -> str:
    return "".join(p for p in parts if p)


# ------------------------------------------------------------------ inline bits
def b(text) -> str:
    """Bold text in the full text colour (stands out inside muted lines)."""
    return f"<b class='hl'>{esc(text)}</b>"


def span(body: str, cls: str) -> str:
    return f"<span class='{cls}'>{body}</span>"


def code(text) -> str:
    """A path or file name in a mono chip."""
    return f"<span class='gcode'>{esc(text)}</span>"


def kbd(key: str) -> str:
    return f"<span class='kbd'>{esc(key)}</span>"


def dot(tone: str = "ok") -> str:
    return f"<span class='dot {tone}'></span>"


def badge(body: str, tone: str = "") -> str:
    """Rounded count/status badge. tone: '', ok, warn, err, info."""
    return f"<span class='badge {tone}'>{body}</span>"


def pill(body: str, tone: str = "ok") -> str:
    """Outlined status pill with a dot (header)."""
    return f"<span class='pill'>{dot(tone)}{body}</span>"


# ------------------------------------------------------------------ blocks
def para(body: str, cls: str = "") -> str:
    return f"<p class='{cls}'>{body}</p>"


def heading(text, mono: bool = False) -> str:
    return f"<h3 class='gh3{' mono' if mono else ''}'>{esc(text)}</h3>"


def badges(*items: str) -> str:
    return f"<div class='grc'>{join(*items)}</div>"


def note(body: str, tone: str = "info", ico: str | None = None) -> str:
    """Tinted message box with an icon. tone: info, ok, warn, err."""
    return (f"<div class='note {tone}'><span class='ic'>{icon(ico or TONE_ICONS[tone], 16)}</span>"
            f"<div>{body}</div></div>")


def msg(body: str, tone: str = "ok") -> str:
    """Compact one-line status (e.g. 'Settings saved')."""
    return f"<div class='gmsg {tone}'>{icon(TONE_ICONS[tone] if tone != 'ok' else 'check', 15)}{body}</div>"


def card(*parts: str, cls: str = "") -> str:
    """Panel with a border; the main container for page summaries."""
    return f"<section class='gcard {cls}'>{join(*parts)}</section>"


def inset(*parts: str) -> str:
    """Recessed box inside a side panel (e.g. the run summary)."""
    return f"<div class='ginset'>{join(*parts)}</div>"


def path_rows(rows: list[tuple[str, object]]) -> str:
    """Label + path chip per row (Source:, Output:, …)."""
    return "<div class='gpaths'>" + "".join(
        f"<div><span class='muted'>{esc(label)}</span>{code(path)}</div>" for label, path in rows) + "</div>"


def kv(rows: list[tuple[str, str]]) -> str:
    """Definition list: plain-text label, HTML value."""
    return "<dl class='gkv'>" + "".join(f"<dt>{esc(k)}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"


def hint(body: str) -> str:
    return f"<div class='ghint'>{body}</div>"


def tag(text, ico: str) -> str:
    """Corner label like the ones on image panels, for HTML panels."""
    return f"<span class='gtag'>{icon(ico, 13)}{esc(text)}</span>"


def empty(ico: str = "image", text: str = "") -> str:
    """Placeholder for a panel with nothing in it yet."""
    return f"<div class='gempty'>{icon(ico, 28)}{f'<span>{esc(text)}</span>' if text else ''}</div>"


def progress(pct: int, line: str, sub: str = "", busy: bool = False, tone: str = "") -> str:
    """Progress card: bar, a main line and an optional mono status line (with a spinner while busy)."""
    pct = max(0, min(100, int(pct)))
    sub_html = (f"<p class='gsub'>{'<span class=spin></span>' if busy else ''}{sub}</p>" if sub else "")
    return card(f"<div class='prog {tone}' role='progressbar' aria-valuenow='{pct}' aria-valuemin='0' "
                f"aria-valuemax='100'><i style='width:{pct}%'></i></div>",
                f"<p class='gline'>{line}</p>", sub_html, cls="gprog")


LOG_MARKS = {"ok": "✓", "err": "✕", "": "·"}


def log(lines: list[tuple[str, str]], title: str = "Log") -> str:
    """Log panel. lines are (tone, plain text) with tone 'ok', 'err' or ''. The list is drawn newest
    at the bottom and stays scrolled to the end (column-reverse), with no script needed."""
    rows = "".join(f"<div><span class='{t}-t'>{LOG_MARKS.get(t, '·')}</span> {esc(x)}</div>"
                   for t, x in reversed(lines))
    return f"<div class='glogwrap'><span class='gl'>{esc(title)}</span><div class='glog'>{rows}</div></div>"


def header(project: str | None, status: list[tuple[str, str]]) -> str:
    """App header: logo + title, project chip, status pills [(tone, text)] on the right."""
    proj = (f"<span class='proj'><small>PROJECT</small>{esc(project)}</span>" if project
            else "<span class='proj muted'>No project open</span>")
    pills = "".join(pill(esc(text), tone) for tone, text in status)
    return (f"<header class='ghdr'><div class='ttl'><span class='logo'>{icon('image', 15)}</span>"
            f"Product Image Studio</div>{proj}<span class='sp'></span>{pills}</header>")
