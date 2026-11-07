# Floor Copilot

Julian's personal tool for selling refrigerators as an appliance associate at the Home Depot Cumberland store (Atlanta, store 121). This is a personal project, not an official Home Depot product: never add Home Depot logos or wordmarks, and keep the "prepared by an associate" framing.

## What's here

| Path | What it is |
|---|---|
| `src/floor-copilot.template.html` | Julian's floor tool (phone-first). Tabs: Customer, Fridges, Options, Take-home. |
| `src/customer.template.html` | The customer's take-home planner (Your picks / Measure / Find more). Opened by QR code. |
| `src/vendor/qrcode-generator.js` | QR library (MIT), inlined into the floor tool at build time. |
| `tools/build.py` | Builds all pages. Run after any template change. |
| `tools/harvest.js` | Runs inside a browser tab on homedepot.com and builds catalog rows. |
| `tools/collect_rows.py` | Pulls harvested rows out of saved tool outputs. |
| `tools/apply_refresh.py` | Swaps a new catalog + price date into built pages. |
| `index.html` | Built customer page, served by GitHub Pages. **Also the single source of truth for the catalog and price date.** |
| `build/floor-copilot.html` | Built floor tool, published as a Claude artifact. |
| `build/customer-artifact.html` | Backup copy of the customer page as a Claude artifact. |
| `app/` | Built Floor Copilot home-screen web app (GitHub Pages `/app/`): `index.html`, `sw.js`, manifest, icons, `vendor/` decoder. Never hand-edit. |
| `src/app/` | Web app sources: `pwa.js` (inlined into `app/index.html`), `sw.template.js`, `manifest.webmanifest`, icons. |
| `src/vendor/zxing/` | zxing-wasm 3.1.6 reader (MIT; ZXing-C++ Apache 2.0). Barcode fallback for phones without `BarcodeDetector` (iPhone). Copied to `app/vendor/`. |
| `tools/make_icons.py` | Redraws the app icons (needs Pillow). Original art, no store logos. |
| `tools/check_picks.py` | Loads the built floor tool in headless Chrome (Playwright) and prints the top 3 auto picks, with score, rating, reviews, style, price and fit, for six sample customers. `--json out.json` saves them for before/after diffs, `--floor` seeds a few floor fridges first. Run it after any ranking change. |

## Where things are published

- Customer page (QR codes point here): https://odthakang-kai.github.io/fridge-picks/
- Floor Copilot home-screen app (offline, barcode scanning): https://odthakang-kai.github.io/fridge-picks/app/
- Floor Copilot (Claude artifact, private): https://claude.ai/artifact/LhFmDEy4Hphdtb9vsrbE35
- Customer page backup (Claude artifact): https://claude.ai/artifact/5xKymLy1PVZZWDDUAsejFz

To ship a change: edit a template, run `python3 tools/build.py`, commit and push (GitHub Pages updates `index.html` in about a minute), (this also ships `app/`), then publish `build/floor-copilot.html` and `build/customer-artifact.html` to their artifact URLs with the Artifact tool (pass `url`, never create a new artifact).

## Build rules

- Templates contain placeholders the build fills: `__CATALOG__`, `__QRLIB__` (floor tool) and `__CATALOG__`, `__SHARED__` (customer page). `const DATA_DATE=new Date("YYYY-MM-DDT12:00:00")` is overwritten from `index.html`.
- `__SHARED__` is cut from the floor-tool template between these markers, so keep them intact and keep shared functions inside them: `const STYLE=` … `function space(){`, `function fit(` … `/* ---------- list`, `const BAYES=` … `const DISP=`, `const people=` … `function optCard(`. Anything the customer page needs (fit, drawings, needs(), why/good-to-know lists, price helpers) must live in those ranges.
- Pages are single self-contained files. No external scripts, fonts or images. Artifact pages must not contain their own `<html>/<head>/<body>`; the build wraps the GitHub Pages copy.
- Copy style: plain words, no em dashes, no Home Depot branding. Fit results always pair an icon with words. Keep the fit disclaimer and the price-date notes on both pages.

## Catalog format

`const RAW` holds one fridge per line, 31 `|`-separated fields:

`0 itemId (Internet #) | 1 store SKU | 2 model | 3 brand | 4 label (<=95 chars) | 5 type FD/SS/TF/BF/FL | 6 price | 7 was price | 8 rating | 9 reviews | 10 width | 11 height to hinge top | 12 depth with handles | 13 depth without doors | 14 depth with doors open 90° | 15 capacity cu ft | 16 kWh/yr | 17 dispenser (None/Water Only/Ice Only/Both/Beverage Center) | 18 C counter or S standard depth | 19 Energy Star 1/0 | 20 water filter # | 21 R returnable or N | 22 garage ready 1/0 | 23 smart 1/0 | 24 warranty (short) | 25 promo flags B=Spend More Save More, S=Special Buy | 26 availability O online only, S store & online, B store only | 27 depth excluding handles | 28 zero-clearance 1/0 | 29 reversible door 1/0 | 30 earliest delivery date (unused in UI)`

Inches for all dimensions. Prices are for store 121.

## Weekly price refresh

A Claude scheduled task ("Floor Copilot weekly price refresh", Sundays 9:13 PM ET, runs on Julian's computer) uses the built-in browser to run `tools/harvest.js` on homedepot.com, then `tools/apply_refresh.py` on the two artifacts and this repo's `index.html`, and pushes. `apply_refresh.py` automatically updates `app/index.html` too whenever the repo's `index.html` is in the list, so the task does not need to name it. The service worker loads the page network-first, so the installed app picks up new prices the next time it opens online. It never touches templates. If Home Depot changes its page structure, `harvest.js` is the file to fix.

## Customer link format (QR)

`index.html#q1-<itemId>-<itemId>-...-w<width×100>-h<height×100>-c<wall to counter edge×100>-i<wall to island×100>-g<gap to side wall×100>-e<nook depth×100>-d<doorway×100>-z<letters of measurements that don't apply: h,c,i,g,e>-p<s|t|x path>-r<y|n|u water>-a<adults>-k<kids>-b<budget max>-l<budget min>-f<habit letters c,b,o,d,f,r,g>-o<1-based indexes of picks on our floor>-x<estimated width×100>-s<picked style: f French door, s side by side, b bottom freezer, t top freezer>-m1-n<associate name>`

- `x` is the quick-path width estimate (never treated as measured), `s` the style they picked, `l` the low end of a budget chip.
- `m1` = "Send home to measure": the page opens on the Measure tab, picks say "Not checked yet", and once anything is measured `rerank()` replaces the list with the best 3 that fit (original picks get a small bonus so they stay if they still fit). Adding or removing a pick turns `m1` off and the list stays put.

Only letters, digits and hyphens. Nothing personal about the customer goes in the link. Old links without `e`/`z`/`x`/`s`/`l`/`m` still work, and older copies of the page ignore the new tokens.

## Measurements and fit

- Fields (floor ids / customer keys): `ow` width, `oh` height, `door` narrowest doorway + `path`, `cab` wall to counter edge, `island` wall to island, `hinge` gap to side wall (one wall), `nook` nook depth (walls on both sides), `water` yes/no/unsure.
- In the floor tool, typing or tapping **None** in oh/cab/island/hinge/nook marks it "doesn't apply" (`sp.na`), which the customer page shows as covered.
- Nook: the fridge is pulled forward so its body front lines up with the side walls (`pull = nook - (depth without doors + 1)`). The island and counter checks use that real position; the one-wall hinge check is skipped when a nook depth is given.
- Estimated width: the Customer tab's "What width are they replacing?" chips (30/33/36) set `S.est`. `space()` uses it as `ow` only when no width is typed, with `sp.est=true`. The width check then only says yes/no (never tight), every fit label says "(estimate)", drawings say "Estimated opening, not measured", and the QR sends it as `x`, never as a measured `w`.
- `fit()` checks carry `kind`: `fit` (how it fits the space), `todo` (sort out before delivery: handles/doors off, water line), `pref` (flush look). Labels come from `fitKey/fitWord/fitCls`: Fits / Fits, check N things / Tight, double check (a `fit`-kind check is close) / Won't fit / Not checked.
- Ranking lives in one shared function, `scoreCore(u,f,o)` (inside the `const BAYES=` … `const DISP=` range), used by `sorter` best/`autoPicks` on the floor tool and `score`/`rerank` on the customer page. Points: fit Fits +3 / check +2.5 / tight +0.5; no returns −2; in the size box +3 (close +1); rating `(BAYES−4.2)×6` (about 4.8 points between a 4.0 and a 4.8) and −2.5 under 20 reviews; picked style +3, otherwise the styles the size box recommends (`needs().types`) +1.5; habits (dispenser, reliable, flush, garage) as before; over budget −4, under a picked budget floor −2; width gap 0.25–2" +2, over 4" −2.5; no price −3; price sanity: with no "$3k+"-style minimum, `−6×log2(price / typical price)` when it costs more than the median standard-depth fridge within 3 cu ft (counter depth allowed 1.5×), see `medPrice()`; on our floor +4 unless tight, won't fit, too small or over budget. Online only gets no penalty (it is just a tag). Ties break by more reviews, then lower price per cu ft (`tieBreak`). Auto picks skip tight fits when 3 roomier ones exist and skip near-duplicates (same brand, style, cu ft and width).
- "Why this one": when the dearest other pick costs more than 1.5× this one, it says "Lowest price of these three" with no dollar gap.

## Customer page layout

Floor tool Customer tab: quick path first (adults/kids, style chips, budget chips Under $1k / $1–2k / $2–3k / $3k+ / No limit, optional "What width are they replacing?"), extra habits and an exact budget under "More about them", then "Walk them to these" (the 3 picks, floor models first with their aisle, "Send home to measure" QR), then the full measurement form folded under "They have measurements" (opens by itself once any measurement is filled). Header bar: "Not measured yet · N fridges", "N fit their space" once anything is measured, or `Estimated 36" width · N could fit` with only the estimate.

Floor tool Fridges tab: "On our floor" view on top, floor fridges grouped by aisle note with each one's fit for the current customer, last seen date, "Mark seen today" and "No longer on display". "Walk the aisle" asks for the aisle note once, then every scan (or typed code) adds that fridge to the floor list with the note and today's date and keeps the camera open; unmatched codes offer the usual link-by-hand flow, and linking during a walk also adds the fridge and goes back to scanning. Picks on the Customer and Options tabs show "On the floor, <aisle>" or "Not on display". The customer page only says "On display in store".

Customer page: Your picks: What we checked box (8 items: covered, doesn't apply, or not yet), Cards or Compare view, verdict-first cards with "Checked / Not checked yet", details folded under More details, Before you buy checklist, come-back box. Measure: Step 1 always measure (width, height, doorway), Step 2 yes/no questions that reveal optional fields (No counts as covered), Step 3 household; one fraction bar follows the focused field; sticky status shows how many picks fit. Find more: style chips plus a Filters and sort button, 20 at a time.

## Local-only data (lives on Julian's phone, not in the repo)

- Floor list: `localStorage["fc_floor_v2"]` = `{itemId: {a: "aisle note", s: "YYYY-MM-DD last seen" or null}}`. `fc_floor_v1` (`{itemId: "aisle note"}`) is still written alongside on every save, and on load any v1 entries missing from v2 are migrated in (last seen unknown), so nothing is lost and an older cached app still sees the list. Use `floorSet(id, aisle)` / `floorDel(id)` / `floorAisle(u)`.
- Text size: `localStorage["fc_z"]`
- Linked barcodes: `localStorage["fc_codes_v1"]` = `{codeKey: itemId}` (codes Julian linked by hand, e.g. box UPCs; numeric keys drop leading zeros)
- The artifact and the home-screen app are different origins, so their storage is separate. The Take-home tab's "Saved on this phone" panel copies and restores a backup (`FC1:` + base64 JSON of `{f: {itemId: "aisle"}, f2: {itemId: {a, s}}, c: {code: itemId}}`) to move the floor list and linked codes between them. Restore reads old backups (only `f`) and new ones, adds to what's there, and keeps the newer last-seen date.

## Barcode scanning

Search bar scan button. Uses native `BarcodeDetector` when present (Android Chrome), otherwise the vendored zxing-wasm reader (home-screen app only; the artifact falls back to typing). Matching order in `matchCode()`: homedepot.com product URL in a QR (9-digit itemId), linked codes, exact itemId / store SKU / model, digit windows inside longer numbers, model inside the text. Unmatched codes can be linked to a fridge from its detail sheet. The catalog has no UPCs, so box barcodes only work after linking.
