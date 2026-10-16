"""Reusable Gradio building blocks: the same side panel, button, button row and image panel on every
page. Each one only adds the right classes; studio.css does the styling."""
import gradio as gr

from .icons import btn_icon

WIDTHS = (280, 300, 340)  # fixed column widths used by the design (studio.css has a .w-<n> rule each)


def side_panel(width: int | None = None, scale: int = 1, min_width: int = 320, **kw) -> gr.Column:
    """The card-style left column (`.gside`). width= fixes it to one of WIDTHS."""
    return column(width, scale, min_width, extra=["gside"], **kw)


def column(width: int | None = None, scale: int = 1, min_width: int = 320, extra=(), **kw) -> gr.Column:
    """A plain column, optionally fixed to one of WIDTHS."""
    classes = list(extra)
    if width:
        if width not in WIDTHS:
            raise ValueError(f"add a .w-{width} rule to studio.css and WIDTHS first")
        classes.append(f"w-{width}")
        min_width = width
    return gr.Column(scale=0 if width else scale, min_width=min_width, elem_classes=classes, **kw)


def button(label: str, icon: str | None = None, kbd: str | None = None, tone: str | None = None,
           tall: bool = False, full: bool = False, icon_end: bool = False, extra=(), **kw) -> gr.Button:
    """gr.Button with the design's extras.
    icon: name from icons.PATHS (icon_end puts it after the label) · kbd: shortcut key drawn as a key cap ·
    tone: 'warn' for amber text (use variant='stop' for red) · tall: 44px row button · full: full width."""
    classes = list(extra)
    if icon:
        classes += ["ico-btn", btn_icon(icon)] + (["ico-end"] if icon_end else [])
    if kbd:
        classes.append(f"k-{kbd.lower()}")
    if tone:
        classes.append(f"t-{tone}")
    if tall:
        classes.append("tall")
    if full:
        classes.append("full")
    return gr.Button(label, elem_classes=classes, **kw)


def actions(tall: bool = True) -> gr.Row:
    """A row of equal-width buttons (the 4-button bars on Review, Touch-up and Export)."""
    return gr.Row(elem_classes=["actions"] + (["tall"] if tall else []), equal_height=True)


def pair() -> gr.Row:
    """Field + button side by side, bottoms aligned (Source folder + Browse…, Preset + Apply)."""
    return gr.Row(elem_classes=["gpair"], equal_height=False)


def html(value: str = "", **kw) -> gr.HTML:
    """gr.HTML without Gradio's own padding/box, for panels made with ui.html."""
    return gr.HTML(value, padding=False, container=False, **kw)


WELL = ["well"]          # image panels: dark stage, corner tag, toolbar (Image, Gallery, ImageSlider, …)
CHIP = ["chip"]          # a single checkbox drawn as a bordered chip (Settings)
PLAIN_CHIP = ["chip", "plain"]  # … or as a borderless one (Run, Review, Touch-up)
