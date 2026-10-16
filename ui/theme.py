"""Darkroom design tokens (from Design/*/studio.css `.t-dark`) and the Gradio theme built from them.

TOKENS is the single source for colours: the Gradio theme uses them directly, and assets.py writes
them out as CSS variables (--bg, --panel, …) for studio.css and the HTML helpers."""
import gradio as gr

TOKENS = {
    "bg": "#141416", "panel": "#1d1d20", "panel2": "#26262a", "panel3": "#323238", "line": "#34343b",
    "text": "#ececef", "muted": "#a9a9b3", "faint": "#8e8e98",
    "accent": "#7aaeff", "accent-strong": "#9cc2ff", "on-accent": "#0a1424", "ai": "#8fbaff",
    "ok": "#62d394", "ok-bg": "rgba(98,211,148,.14)",
    "warn": "#f3b54e", "warn-bg": "rgba(243,181,78,.15)",
    "err": "#ff8a80", "err-bg": "rgba(255,128,119,.15)",
    "info-bg": "rgba(122,174,255,.15)", "focus": "#b5d0ff",
    "stage": "#0b0b0c", "tag-bg": "rgba(16,16,18,.88)",
    "font": "'IBM Plex Sans', system-ui, sans-serif",
    "mono": "'IBM Plex Mono', ui-monospace, Consolas, monospace",
}
T = TOKENS

# a check mark drawn in the dark "on accent" colour, for ticked boxes (as in gr.css)
_CHECK = ("url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' "
          "stroke='%230a1424' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'%3E"
          "%3Cpath d='M5 12.5l4.5 4.5L19 7'/%3E%3C/svg%3E\")")

_VARS = dict(
    body_background_fill=T["bg"], body_text_color=T["text"], body_text_color_subdued=T["muted"],
    body_text_size="13px",
    background_fill_primary=T["panel"], background_fill_secondary=T["panel2"],
    border_color_primary=T["line"], border_color_accent=T["accent"], border_color_accent_subdued=T["accent"],
    color_accent=T["accent"], color_accent_soft=T["info-bg"], loader_color=T["accent"],
    link_text_color=T["ai"], link_text_color_hover=T["accent-strong"], link_text_color_visited=T["ai"],
    code_background_fill=T["panel2"], accordion_text_color=T["text"],
    panel_background_fill=T["panel"], panel_border_color=T["line"],
    # blocks sit inside cards/side panels, so they carry no chrome of their own
    block_background_fill="transparent", block_border_width="0px", block_padding="0px",
    block_shadow="none", block_radius="8px", layout_gap="14px", form_gap_width="0px",
    block_title_text_size="11px", block_title_text_weight="600", block_title_text_color=T["muted"],
    block_title_background_fill="transparent", block_title_padding="0", block_title_radius="0",
    block_info_text_size="12px", block_info_text_color=T["faint"], block_info_text_weight="400",
    # the small tag in the top-left corner of image panels
    block_label_background_fill=T["tag-bg"], block_label_border_color=T["line"], block_label_border_width="1px",
    block_label_text_color=T["muted"], block_label_text_size="11px", block_label_text_weight="500",
    block_label_padding="6px 10px", block_label_radius="0 0 6px 0", block_label_right_radius="0 0 0 6px",
    block_label_margin="0", block_label_shadow="none",
    input_background_fill=T["panel2"], input_background_fill_focus=T["panel2"],
    input_background_fill_hover=T["panel2"], input_border_color=T["line"],
    input_border_color_focus=T["accent"], input_border_color_hover=T["faint"], input_border_width="1px",
    input_radius="6px", input_padding="8px 12px", input_text_size="13px", input_shadow="none",
    input_shadow_focus="none", input_placeholder_color=T["faint"],
    # radio / checkbox options drawn as chips
    checkbox_label_background_fill=T["panel2"], checkbox_label_background_fill_hover=T["panel3"],
    checkbox_label_background_fill_selected=T["panel3"], checkbox_label_border_color=T["line"],
    checkbox_label_border_color_hover=T["faint"], checkbox_label_border_color_selected=T["accent"],
    checkbox_label_border_width="1px", checkbox_label_gap="6px", checkbox_label_padding="7px 10px",
    checkbox_label_shadow="none", checkbox_label_text_color=T["text"],
    checkbox_label_text_color_selected=T["text"], checkbox_label_text_size="13px",
    checkbox_label_text_weight="400",
    checkbox_background_color="transparent", checkbox_background_color_hover="transparent",
    checkbox_background_color_focus="transparent", checkbox_background_color_selected=T["accent"],
    checkbox_border_color=T["faint"], checkbox_border_color_hover=T["muted"],
    checkbox_border_color_focus=T["accent"], checkbox_border_color_selected=T["accent"],
    checkbox_border_width="1.5px", checkbox_border_radius="3px", checkbox_shadow="none", checkbox_check=_CHECK,
    slider_color=T["accent"],
    button_border_width="1px", button_transition="background .12s", button_transform_hover="none",
    button_transform_active="none",
    button_large_padding="0 14px", button_large_radius="6px", button_large_text_size="13px",
    button_large_text_weight="500",
    button_medium_padding="0 14px", button_medium_radius="6px", button_medium_text_size="13px",
    button_medium_text_weight="500",
    button_small_padding="0 10px", button_small_radius="6px", button_small_text_size="12px",
    button_small_text_weight="500",
    button_primary_background_fill=T["accent"], button_primary_background_fill_hover=T["accent-strong"],
    button_primary_border_color=T["accent"], button_primary_border_color_hover=T["accent-strong"],
    button_primary_text_color=T["on-accent"], button_primary_text_color_hover=T["on-accent"],
    button_primary_shadow="none", button_primary_shadow_hover="none", button_primary_shadow_active="none",
    button_secondary_background_fill=T["panel2"], button_secondary_background_fill_hover=T["panel3"],
    button_secondary_border_color=T["line"], button_secondary_border_color_hover=T["line"],
    button_secondary_text_color=T["text"], button_secondary_text_color_hover=T["text"],
    button_secondary_shadow="none", button_secondary_shadow_hover="none", button_secondary_shadow_active="none",
    # variant="stop": a normal button with red text (Cancel, Reset to AI cut-out)
    button_cancel_background_fill=T["panel2"], button_cancel_background_fill_hover=T["panel3"],
    button_cancel_border_color=T["line"], button_cancel_border_color_hover=T["line"],
    button_cancel_text_color=T["err"], button_cancel_text_color_hover=T["err"],
    button_cancel_shadow="none", button_cancel_shadow_hover="none", button_cancel_shadow_active="none",
    error_background_fill=T["err-bg"], error_border_color=T["err"], error_text_color=T["err"],
    error_icon_color=T["err"], error_border_width="1px",
    table_border_color=T["line"], table_even_background_fill=T["panel"], table_odd_background_fill=T["panel2"],
    table_text_color=T["text"], table_radius="6px", stat_background_fill=T["accent"],
    shadow_drop="none", shadow_drop_lg="0 8px 24px rgba(0,0,0,.35)", shadow_spread="0px", shadow_inset="none",
)

# The app is always dark; set the light and dark variants alike so nothing depends on the body class.
THEME = gr.themes.Base(
    font=["IBM Plex Sans", "system-ui", "sans-serif"],
    font_mono=["IBM Plex Mono", "ui-monospace", "Consolas", "monospace"],
)
THEME.set(**_VARS, **{f"{k}_dark": v for k, v in _VARS.items() if hasattr(THEME, f"{k}_dark")})
