"""Builds the CSS and JS handed to Gradio's launch(): colour variables from theme.TOKENS, the bundled
IBM Plex fonts (served locally, so the app stays offline), the icon rules and studio.css."""
from pathlib import Path
from urllib.parse import quote

from .icons import PATHS, icons_css
from .theme import TOKENS

UI_DIR = Path(__file__).resolve().parent
FONTS_DIR = UI_DIR / "fonts"

FONTS = {"IBM Plex Sans": ("ibm-plex-sans", (400, 500, 600, 700)),
         "IBM Plex Mono": ("ibm-plex-mono", (400, 500, 600))}
# unicode ranges from the fontsource package: basic latin, and the latin-ext supplement
RANGES = {"latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,"
                   "U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD",
          "latin-ext": "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,"
                       "U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,"
                       "U+A720-A7FF"}


def file_url(path: Path) -> str:
    """URL Gradio serves a local file at (the folder must be in allowed_paths / set_static_paths)."""
    return "/gradio_api/file=" + quote(path.as_posix())


def fonts_css() -> str:
    rules = []
    for family, (stem, weights) in FONTS.items():
        for w in weights:
            for subset, rng in RANGES.items():
                f = FONTS_DIR / f"{stem}-{subset}-{w}-normal.woff2"
                if f.exists():
                    rules.append(f"@font-face{{font-family:'{family}';font-style:normal;font-weight:{w};"
                                 f"font-display:swap;src:url('{file_url(f)}') format('woff2');"
                                 f"unicode-range:{rng}}}")
    return "\n".join(rules)


def vars_css() -> str:
    search = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23a9a9b3' "
              f"stroke-width='1.9' stroke-linecap='round'><path d='{PATHS['search']}'/></svg>")
    vars_ = ";".join(f"--{k}:{v}" for k, v in TOKENS.items())
    return f":root{{{vars_};--search-ico:url(\"data:image/svg+xml,{search.replace('<', '%3C').replace('>', '%3E')}\")}}"


def css() -> str:
    return "\n".join([vars_css(), fonts_css(), icons_css(), (UI_DIR / "studio.css").read_text(encoding="utf-8")])


def js() -> str:
    return (UI_DIR / "studio.js").read_text(encoding="utf-8")
