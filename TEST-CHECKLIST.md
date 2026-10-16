# Product Image Studio: test checklist

Each line says what to do, and after the → what you should see. Tick each box as you go. To keep the real **HiFi Catalogue** project untouched, most tests use a small **Test** project; section 0 sets it up.

If anything doesn't match the expected result, note the step number and what you saw.

---

## 0. Setup
- [ ] **1.** In File Explorer, make a folder `C:\Users\Muhammad\Hifi-Consultant-Shopify\Test Photos`. Copy in 5 photos from `Original Images`: one Transparent cable, one Transparent box (e.g. `transparent-powerwave`), one Audience close-up (e.g. `audience-au24-sx-speaker-cable`), one Black Cat and the Jewel cube.
- [ ] **2.** Double-click `Image Processing\Start.bat` → a black window opens and your browser shows **Product Image Studio** in the dark theme.
- [ ] **3.** Look at the header → "Offline" and "AI model on disk" badges, and **HiFi Catalogue** is open.

## 1 · Project
- [ ] **4.** The summary for HiFi Catalogue → "172 images found · 172 already cut out · 172 done with the current settings", and a thumbnail gallery.
- [ ] **5.** Open **New project**. Enter the name `Test`, click **Browse…** next to Source folder and pick `Test Photos`, leave Output empty, then click **Create project**.
  - The Browse dialog may open *behind* the browser; check the taskbar.
  - → You see a "Project 'Test' created" message, "5 images found · 0 already cut out", and a note that about 2:30 of AI work is needed.
- [ ] **6.** Click **Open source folder** → File Explorer opens `Test Photos`.
- [ ] **7.** Try **Create project** again with the same name → error: "A project called 'Test' already exists".

## 2 · Settings
- [ ] **8.** The preview shows "This image hasn't been cut out yet. Click Refresh preview…" → this is correct; the AI never starts by itself.
- [ ] **9.** Click **Refresh preview** → after about 40 s the first time (loading the model plus the cut-out), a before/after slider appears. Drag the handle.
- [ ] **10.** Click each background style: **Studio grey, Light grey, White, Transparent, Custom colour**. Pick a colour for Custom → the preview updates within a few seconds each time.
- [ ] **11.** Untick **Soft shadow**, then move **Shadow strength** → the shadow disappears, then gets stronger or weaker.
- [ ] **12.** Switch **Shape** to Original shape, set **Output size** to 1024, and move **Product size** → the preview's shape and size change.
- [ ] **13.** Choose **Transparent**, then format **JPG** → a red error saying "JPG can't be transparent", and the preview stops.
- [ ] **14.** Click each format: **WebP / AVIF / JPG / PNG** → Quality jumps to 85, 60, 90 or 100.
- [ ] **15.** Type `My test` in "New preset name" and click **Save as preset** → it appears in the Preset dropdown.
- [ ] **16.** Choose **Shopify product** and click **Apply preset** → all the settings go back to the defaults.

## 3 · Run
- [ ] **17.** Choose "All images" → the summary says 5 images, 4 or 5 need the AI, and gives an estimated time.
- [ ] **18.** Click **Start** → the progress bar moves, the time left counts down, the last finished image shows and the log fills. Start is greyed out and Cancel is active.
- [ ] **19.** Click **Start** again (All images), then **Cancel** after 1–2 images → "Cancelled after N image(s)", and the buttons reset.
- [ ] **20.** Choose "Only images not done yet" and click **Start** → only the unfinished ones run.
- [ ] **21.** Choose "Selected images", pick 1 image, tick **Redo AI cut-outs**, and click Start → that image takes about 30 s and the log says ", AI".
- [ ] **22.** Click **Open output folder** → the folder `projects\test\output` holds 5 `.webp` files.

## 4 · Review
- [ ] **23.** Open the tab → counts read "5 not reviewed", and the first image opens in a large before/after view with its details.
- [ ] **24.** Click somewhere outside the text boxes, then press **A** → it's approved and the next image opens, and the counts update.
- [ ] **25.** Type a note, click outside the box, then press **F** → it's flagged "needs fix" and moves on.
- [ ] **26.** Press **←** and **→** → you move between images.
- [ ] **27.** Filter by **Needs fix** → only the flagged image shows, with your note.
- [ ] **28.** Press **R** → a "Redone" message, the image stays visible and is reset to "Not reviewed".
- [ ] **29.** Type part of a name in the search box and press Enter → the gallery filters.
- [ ] **30.** Click **Approve all shown** → all shown images are approved.
- [ ] **31.** Go to the **Settings** tab and press **A** there → nothing happens, because the shortcuts only work on Review.

## 5 · Touch-up
- [ ] **32.** In Review, select `transparent-powerwave` and press **T** → the Touch-up tab opens with that image loaded.
- [ ] **33.** Pick the **red** brush (the colour dot in the editor toolbar) and paint over the reflection under the box. Click **Apply** → after about 2–5 s the "Final image" on the right shows the reflection gone, and the editor reloads with the edited cut-out.
- [ ] **34.** Click **Undo last apply** → the reflection is back.
- [ ] **35.** Paint again, Apply, then click **Reset to AI cut-out** → back to the original AI result, and the info no longer says "touched up".
- [ ] **36.** Pick the **green** brush and paint over an empty area next to the product, then Apply → part of the old background reappears. Undo it.
- [ ] **37.** Switch "Show the cut-out" to **On a checkerboard** → the transparent areas show as a checkerboard.
- [ ] **38.** Click **Apply** without painting anything → error: "Nothing painted yet".
- [ ] **39.** Flag 2 images in Review, tick **Only images marked 'Needs fix'**, then click **✓ Approve & next** → the image is approved and the next flagged one loads.

## 6 · Export
- [ ] **40.** Open the tab → "5 finished image(s) · total … (originals …, …% smaller)".
- [ ] **41.** Click **Create before/after sheets** → after a few seconds a sheet appears. **Open sheets folder** shows `review-01.jpg`.
- [ ] **42.** Click **Export CSV report** → `report.csv` appears to download. Opened in Excel, it has columns for name, sizes, status, review and message.

## ⚙ App
- [ ] **43.** The page shows the model file (about 931 MB on disk), whether it's loaded, and the projects folder.

## General checks
- [ ] **44.** Close the browser tab and open `http://127.0.0.1:7860` again → everything is still there: settings, reviews and notes.
- [ ] **45.** Close the black window, then run `Start.bat` again → the app reopens the project you used last.
- [ ] **46.** With your internet disconnected, run steps 9 and 18 → everything still works.
- [ ] **47.** Open **HiFi Catalogue** again → it still shows 172 done and 12 "Needs fix" in Review. The test project didn't change it.

## Clean up afterwards
- [ ] Delete `Image Processing\projects\test` and the `Test Photos` folder.
- [ ] Optional: delete `Image Processing\presets\my-test.json`.

---

### Notes / issues found
| Step | What happened | Expected |
|---|---|---|
|  |  |  |
