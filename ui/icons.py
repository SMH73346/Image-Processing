"""Line icons from the design (Design/*/Icon.dc.html): 24×24 viewBox, stroked with currentColor.

- icon("folder", 16) gives inline SVG for HTML.
- For a Gradio button, add the class from btn_icon("folder") (see layout.button); the CSS that
  icons_css() writes draws the icon in the button's own text colour."""
from urllib.parse import quote

PATHS = {
    "grid": "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
    "sliders": "M4 7h9M17 7h3M4 17h3M11 17h9M15 5v4M9 15v4",
    "play": "M7 4.8v14.4a.6.6 0 0 0 .9.5l11.4-7.2a.6.6 0 0 0 0-1L7.9 4.3a.6.6 0 0 0-.9.5z",
    "review": "M4 5h16v14H4zM4 15l4.5-4.5 4 4 3-3L20 16M15.5 9h.01",
    "brush": "M14.5 4.5l5 5L11 18H6v-5zM12 7l5 5",
    "export": "M12 15V3M7 8l5-5 5 5M4 14v5a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-5",
    "folder": "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
    "plus": "M12 5v14M5 12h14",
    "search": "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4",
    "check": "M5 12.5l4.5 4.5L19 7",
    "checkcircle": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM8 12.5l3 3 5-6",
    "warn": "M12 4l9 16H3zM12 10v4M12 17h.01",
    "x": "M6 6l12 12M18 6L6 18",
    "xcircle": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM9 9l6 6M15 9l-6 6",
    "stop": "M6 6h12v12H6z",
    "left": "M15 6l-6 6 6 6",
    "right": "M9 6l6 6-6 6",
    "down": "M6 9l6 6 6-6",
    "undo": "M9 14L4 9l5-5M4 9h10a6 6 0 0 1 0 12h-3",
    "redo": "M15 14l5-5-5-5M20 9H10a6 6 0 0 0 0 12h3",
    "eraser": "M8 20h12M5.5 14.5l8-8a2 2 0 0 1 2.8 0l2.2 2.2a2 2 0 0 1 0 2.8L12 18H9z",
    "restore": "M15 3v6M12 6h6M4 20l2.5-.5 9-9-2-2-9 9z",
    "chip": "M7 7h10v10H7zM10 10h4v4h-4zM9 3v4M15 3v4M9 17v4M15 17v4M3 9h4M3 15h4M17 9h4M17 15h4",
    "sparkle": "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z",
    "layers": "M12 3l9 5-9 5-9-5zM3 13l9 5 9-5",
    "frame": "M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4M9 9h6v6H9z",
    "file": "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M9 14h6M9 17h4",
    "eye": "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
    "refresh": "M20 11a8 8 0 0 0-14.9-3M4 4v4h4M4 13a8 8 0 0 0 14.9 3M20 20v-4h-4",
    "info": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 8h.01",
    "download": "M12 3v12M7 10l5 5 5-5M4 19h16",
    "table": "M4 5h16v14H4zM4 10h16M4 15h16M10 5v14",
    "compare": "M12 3v18M4 6h5v12H4zM15 6h5v12h-5z",
    "save": "M5 4h11l3 3v13H5zM8 4v5h7M8 20v-6h8v6",
    "trash": "M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3",
    "clock": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",
    "arrowr": "M5 12h14M13 6l6 6-6 6",
    "arrowl": "M19 12H5M11 6l-6 6 6 6",
    "image": "M4 5h16v14H4zM4 16l5-5 4 4 2-2 5 5M15 9h.01",
    "external": "M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5",
}


def icon(name: str, size: int = 16, cls: str = "") -> str:
    """Inline SVG icon for HTML."""
    return (f"<svg class='ico {cls}' viewBox='0 0 24 24' width='{size}' height='{size}' aria-hidden='true'>"
            f"<path d='{PATHS[name]}'/></svg>")


def btn_icon(name: str) -> str:
    """CSS class that puts this icon in front of a Gradio button's label."""
    if name not in PATHS:
        raise KeyError(f"unknown icon: {name}")
    return f"i-{name}"


def icons_css() -> str:
    """One mask rule per icon, so `.i-<name>` buttons show the icon in currentColor."""
    rules = []
    for name, d in PATHS.items():
        svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
               f"stroke-width='1.9' stroke-linecap='round' stroke-linejoin='round'><path d='{d}'/></svg>")
        url = f'url("data:image/svg+xml,{quote(svg)}")'
        rules.append(f".i-{name}::before{{-webkit-mask-image:{url};mask-image:{url}}}")
    return "\n".join(rules)
