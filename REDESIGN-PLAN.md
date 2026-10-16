# Product Image Studio: redesign plan

Source: `Design/` (7 HTML mockups and `Product Image Studio — 3 Variants.pdf`, 8 pages; page 6 is the Export empty state).

## What the design is

The mockups are a **restyle of the current Gradio app**, not a new app. `gr.css` begins *"Redesign of the current Gradio app in the Darkroom look"*. Every screen keeps the components, labels and layout that `app.py` already has. The Gradio parts are drawn as they are: the block-label tags, the image toolbars, the slider ↺ reset buttons, the ImageEditor's "Layer 1" pill, and the "Gradio: 6.30.0" row on the App page.

**Approach:** keep Gradio and all the logic in `core/` and `app.py`. Change the theme, the CSS, a few HTML helpers and some layout. No new framework, and the event wiring stays as it is.

## Design tokens (from `studio.css` `.t-dark` and `gr.css`)

| Token | Value | Replaces (current app) |
|---|---|---|
| bg / panel / panel2 / panel3 | `#141416` / `#1d1d20` / `#26262a` / `#323238` | `#121212` / `#1b1b1b` / … |
| line | `#34343b` | `#2a2a2a` |
| text / muted / faint | `#ececef` / `#a9a9b3` / `#8e8e98` | |
| accent / accent-strong / on-accent | `#7aaeff` / `#9cc2ff` / `#0a1424` | amber `#d9a441` |
| ok / warn / err (+ 14–15% bg) | `#62d394` / `#f3b54e` / `#ff8a80` | |
| info-bg | `rgba(122,174,255,.15)` | |
| stage (image wells) | `#0b0b0c` | |
| Fonts | IBM Plex Sans 400–700, IBM Plex Mono 400–600 | Segoe UI / Cascadia Mono |
| Base size / radius | 13px; 6px controls, 8px cards | |
| Labels | 11px, 600, uppercase, letter-spacing .07em | |

## Phase 0: Foundation
1. **Move styling out of `app.py`.** Create `ui/` with `studio.css` (all custom CSS), `fonts/` and `icons/`. Load it with `launch(css_paths=…)` and serve it with `gr.set_static_paths`.
2. **Theme.** Rebuild `THEME` with the tokens above (blue accent, Plex fonts, sm radius), so most Gradio parts look right before any CSS is added.
3. **Fonts offline.** The app must run without internet, so the design's Google Fonts link can't be used. I'll bundle the IBM Plex Sans and Mono `.woff2` files (OFL licence) in `ui/fonts/` and load them with `gr.themes.LocalFont` or `@font-face`. *This needs a one-time font download; I'll ask before doing it.*
4. **Icons.** Port the SVG paths from `Icon.dc.html` into an `ICONS` dict and an `icon(name, size)` helper for the HTML parts. For `gr.Button(icon=…)`, write a small SVG file for each icon used (folder, play, stop, refresh, compare, table, chip, arrows), in a light stroke for normal buttons and a dark stroke for primary ones.
5. **Header** (`header_html`): blue logo square with the image icon, "Product Image Studio", a `PROJECT · <name>` chip, and on the right the **Offline** and **AI model** pills with a status dot (green ready, amber on disk, red missing).
6. **Tabs:** 13px tab labels, a 2px blue underline on the active tab, and the "1 ·" number shown in faint mono (accent when active). Gradio tab labels are plain text, so a few lines in `JS` wrap the number in a `<span class="n">` on load.

## Phase 1: Shared component styles (CSS only)
- **Side panels:** the left column on each page becomes a card (`panel` background, 1px line, 8px radius, 14px padding), using `elem_classes="gside"`.
- **Inputs, dropdowns, textboxes:** 36px high on `panel2` with a 6px radius. Path fields use the mono font.
- **Radio and CheckboxGroup as chips:** 34px chips with a ring or box marker; the selected chip gets an accent border and `panel3` fill. A single checkbox is a borderless chip (for example "Redo AI cut-outs…").
- **Sliders:** label and number box with ↺ on one row, then min, track and max underneath. The track is 6px with an accent fill and a white 16px thumb.
- **Accordions:** headers in 11px uppercase with a bottom rule and a chevron.
- **Buttons:** `primary` is the accent with dark text, secondary is `panel2`, and `stop` becomes **red text on a normal button** (Cancel, Reset to AI cut-out) instead of a red fill.
- **Image wells** (Image, ImageSlider, Gallery, ImageEditor): `stage` background, the label as a top-left tag, a dark translucent toolbar on the right, 1px square-ish thumbnails, captions in mono 11px, and an accent outline on the selected image.
- **Messages:** `.gmsg` (ok), `.note.info/.warn/.err` with icons, `.badge` counts, `.kbd` keys, `.gcode` path chips.

## Phase 2: Pages
| Page | Changes |
|---|---|
| **1 · Project** | Left column 340px fixed. `project_summary` becomes a `gr.HTML` card with a 16px title, bold counts, aligned Source / Output / Cut-out cache rows as `.gcode` chips, and an info note with the sparkle icon for the remaining AI time. Gallery has 6 columns, the tag "Images in this project" and mono captions. "Open source / output folder" are small buttons with a folder icon. |
| **2 · Settings** | Columns 2 : 3. Steps and options as chips. The custom colour is a 56×32 swatch next to the shadow chip. Size and Output size share a row. The validation message is the green "✓ Settings saved" bar, or the warn/err notes. The preview dropdown and Refresh button (with icon) share a row, the ImageSlider is about 680px high, and the note below it is small and muted. |
| **3 · Run** | Summary in a `panel2` box: the bold counts line, the muted steps line, and the output folder as a code block. Start (play icon, primary, lg) and Cancel (stop icon, red text) side by side, then a full-width "Open output folder". `progress_html`: 12px bar, a "**1 of 11** (9%) · elapsed · about … left" line, then a spinner and "Working on <file>…" in mono. The last image and the log sit side by side (2 : 3). The log uses mono with a green ✓ and a red ✕; see question 2. |
| **4 · Review** | `review_counts_md` uses badges: grey not reviewed, amber needs fix, green approved, grey not processed. The search field has a search icon and "Approve all shown" next to it. Gallery has 4 columns and an accent outline on the current image. `review_detail` shows the name in mono 16px, the status in bold with format, size and KB, and the original's details. The 4-button row has equal widths, with Needs fix in amber and Approve as primary, and the **F / A / R / T** keys drawn as `kbd` chips with CSS `::after` (the button text stays plain). The shortcut hint uses `kbd` chips. |
| **5 · Touch-up** | Three columns: 300px, flexible, 280px. "How to use" is an ordered list with **red** and **green** in colour. The editor is about 680px high on the dark checkerboard, with its tool rail and toolbar styled. Apply, Undo last apply, Reset (red text) and Approve & next form a 4-column grid. "Final image" well on the right. |
| **6 · Export** | `export_stats` becomes a card: "**N** finished image(s) · total **X** (originals Y, <green>Z% smaller</green>)" and the output folder chip. The 4 action buttons are equal width with icons. The Report file is a row with the table icon, `report.csv` and its size with a download link. The sheets gallery has a dark well. **Empty state:** an info note, "No processed images yet. Run the batch first (tab 3).", with placeholder icons in empty wells. |
| **⚙ App** | `model_info` becomes a key–value list (170px labels) for AI model, Model file (size and path chip), Status (dot and text), Projects folder, and Gradio version. Full-width "Load AI model now" with the chip icon. |

## Phase 3: Packaging and docs
- `build_portable.py`: copy the new `ui/` folder into the package (it copies named files and folders today, so this must be added).
- README: update the screenshots/wording only if something visible changed (e.g. badge names).

## Phase 4: Verification
- Run the app in the browser pane and compare each tab with the matching PDF page at 1440px wide, for layout, colours, fonts and states.
- Check the states the mockups don't show: no project open, model missing, validation errors, failed images, a run that was cancelled, and the Export empty state.
- Go through `TEST-CHECKLIST.md` on the **Test** project so the HiFi Catalogue project stays untouched. The logic doesn't change, but the HTML helpers and the Review keyboard shortcuts must keep working.
- Rebuild the portable folder (`--no-zip`) and check that the fonts and icons load with no internet.

## Out of scope
- No changes to `core/` processing or to project or status file formats.
- The light and "Workflow" variants in `studio.css` (`.t-light` / `.t-flow`) are not used. The mockups use only the dark one.

## Open questions
1. **Fonts:** may I download IBM Plex Sans and Mono once (Google Fonts / IBM's GitHub, about 400 KB) and bundle them? The other option is system fonts (Segoe UI / Consolas), which look close but not exact.
2. **Run log:** keep it a plain Textbox in mono, which is simple and selectable, or switch it to HTML so the ✓ and ✕ marks are coloured as in the mockup?
3. **Run default:** the mockup shows "All images" selected, but the app defaults to "Only images not done yet". Keep the current default?
