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

`index.html#q1-<itemId>-<itemId>-...-w<width×100>-h<height×100>-c<cabinet depth×100>-i<to island×100>-g<hinge gap×100>-d<doorway×100>-p<s|t|x path>-r<y|n|u water>-a<adults>-k<kids>-b<budget>-f<habit letters c,b,o,d,f,r,g>-o<1-based indexes of picks on our floor>-n<associate name>`

Only letters, digits and hyphens. Nothing personal about the customer goes in the link.

## Local-only data (lives on Julian's phone, not in the repo)

- Floor list: `localStorage["fc_floor_v1"]` = `{itemId: "aisle note"}`
- Text size: `localStorage["fc_z"]`
- Linked barcodes: `localStorage["fc_codes_v1"]` = `{codeKey: itemId}` (codes Julian linked by hand, e.g. box UPCs; numeric keys drop leading zeros)
- The artifact and the home-screen app are different origins, so their storage is separate. The Take-home tab's "Saved on this phone" panel copies and restores a backup (`FC1:` + base64 JSON) to move the floor list and linked codes between them.

## Barcode scanning

Search bar scan button. Uses native `BarcodeDetector` when present (Android Chrome), otherwise the vendored zxing-wasm reader (home-screen app only; the artifact falls back to typing). Matching order in `matchCode()`: homedepot.com product URL in a QR (9-digit itemId), linked codes, exact itemId / store SKU / model, digit windows inside longer numbers, model inside the text. Unmatched codes can be linked to a fridge from its detail sheet. The catalog has no UPCs, so box barcodes only work after linking.
