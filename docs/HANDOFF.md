# Floor Copilot handoff

Status, decisions and open questions. Read this after `CLAUDE.md` when picking up work. Keep it current: update it at the end of any session that changes behavior or settles a decision.

Julian's personal fridge-selling tool (Home Depot Cumberland, store 121). Personal project, not an official Home Depot product.

## Where everything lives
- **Source code (source of truth):** this repo, `odthakang-kai/fridge-picks`. `CLAUDE.md` covers layout, build, data format, QR link format, measurements and fit labels, ranking, floor list, scanning, and rules.
- **Customer page (QR codes open this):** https://odthakang-kai.github.io/fridge-picks/
- **Floor Copilot home-screen app (offline + barcode scanning):** https://odthakang-kai.github.io/fridge-picks/app/
- **Claude artifacts (backups, optional):** floor tool https://claude.ai/artifact/LhFmDEy4Hphdtb9vsrbE35 and customer page https://claude.ai/artifact/5xKymLy1PVZZWDDUAsejFz. Only a claude.ai session with the Artifact tool can republish these. GitHub Pages is the real version.
- **Weekly price refresh:** scheduled task "Floor Copilot weekly price refresh", Sundays 9:13 PM ET, runs on Julian's computer. `apply_refresh.py` updates `app/index.html` automatically.

## To make a change (Claude Code)
1. Pull first: `git pull`.
2. Edit `src/floor-copilot.template.html`, `src/customer.template.html`, or the web app files in `src/app/`. Never hand-edit `index.html`, `app/` or `build/`.
3. Run `python3 tools/build.py`. If you touched ranking, also run `python3 tools/check_picks.py` (top 3 picks for six sample customers, run through the real page in headless Chrome).
4. Commit and push (GitHub Pages updates the customer page and `/app/` in about a minute).
5. Update this file if anything changed.

On Julian's Windows computer, `python3` is the Microsoft Store placeholder; run the tools with `python` (3.14). `check_picks.py` needs `pip install playwright` (installed Nov 8) and uses the installed Chrome. `.gitattributes` keeps every file LF and the tools write LF, so a build with no source changes leaves the tree clean (the `app/sw.js` version hash would otherwise change on every Windows build).

## Decisions so far
- Sales tracking stays out of this app (Julian will build a separate tracker).
- Delivery dates removed from the UI.
- No Home Depot logos or wordmarks. Fit disclaimer and price-date notes stay on both pages.
- Home-screen web app shipped Nov 7, 2026: installable, works offline, scan button reads QR and 1D barcodes (native BarcodeDetector, zxing-wasm fallback for iPhone). Unknown barcodes (box UPCs) can be linked to a fridge by hand.
- Artifact and home-screen app keep separate phone storage; move the floor list with Take-home > Saved on this phone > Copy backup / Restore backup.
- Nov 7 (afternoon): measurement fields renamed (wall to counter edge, wall to island, gap to side wall) and an optional nook depth added. "None" marks a measurement as not applying.
- Fit labels are Fits / Fits, check N things / Tight, double check / Won't fit.
- Customer page redesigned: What we checked box, verdict-first pick cards with Cards/Compare views, Before you buy checklist, guided Measure tab, Filters button on Find more.
- Returning-customer scan was considered and dropped: customers who come back are usually ready to buy.
- **Nov 7 (evening) ranking fix.** One shared `scoreCore()` for both pages. Ratings now swing about 4.8 points between 4.0 and 4.8 stars; under 20 reviews costs 2.5. Online only has no penalty (everything ships). No returns costs 2. The styles the size box recommends get +1.5; a picked style gets +3 and wins. Price sanity: a fridge priced well above similar-size standard fridges loses points unless the customer picked "$3k+". Wide gaps (over 4") cost 2.5. Ties go to more reviews, then better $/cu ft. "Why this one" says "Lowest price of these three" when the gap is over 1.5x.
- **On our floor.** Floor list stores aisle note + last seen date (`fc_floor_v2`; v1 still written and migrated, FC1 backups old and new both restore). Fridges tab opens with an On our floor view grouped by aisle with fit badges for the current customer, Mark seen today and No longer on display. Walk the aisle: set the aisle once, scan tags back to back, camera stays open. Floor fridges get +4 in Best match and auto picks when they fit and are big enough and in budget. Picks show "On the floor, <aisle>" or "Not on display"; the customer page says "On display in store".
- **Quick path for walk-ins.** Customer tab opens on adults/kids, style chips, budget chips, optional "What width are they replacing?" (an estimate, labeled as such everywhere). "Walk them to these" shows 3 picks, floor models first. "Send home to measure" QR opens the customer page on Measure with picks marked Not checked yet; once they measure, the page re-ranks. QR tokens `x` (estimate), `s` (style), `l` (budget low end), `m1` (re-rank mode). Full measurement form folds under "They have measurements".
- **Header** reads "Not measured yet · 745 fridges", "N fit their space", or "Estimated 36" width · N could fit".
- **Nov 8: moved development to Claude Code** on Julian's computer. This file replaced the claude.ai project doc as the handoff.

- **Nov 8: pro look + missing-fridge cross-reference.** One shared `src/theme.css` for both pages: charcoal header, white surfaces, orange only for actions/deals/current place, selected choices solid charcoal, sentence-case labels, fit verdicts as shelf tags (colored edge), and the header meter drawn as a tape measure. The LG LF30S8210S (item 326917144) was missing: Home Depot lists it under French Door, so the old harvest most likely lost it when its spec page failed to load (failures were silently dropped). `harvest.js` now retries spec pages, has no 480 cap, reports every dropped fridge with a reason (`HV.reportText()`), and looks up anything on `data/watchlist.txt` directly. Catalog refreshed Nov 8 with the new harvest: 763 fridges (was 745), no spec-page failures, 7 legit drops (4 portable gas fridges with no width, 3 unbranded). Save harvested rows with `tools/receive_rows.py` (fetch to other hosts is blocked on homedepot.com; navigating the tab to localhost with the rows in the URL fragment works, but read `HV.reportText()` first since leaving the page loses the harvest). The app saves unmatched scans to a "Not in the catalog" list (Take-home) that travels in the backup; `tools/check_catalog.py` cross-references it.

- **Nov 8: cleanup before new features.** Julian felt both pages had too many words for customers. Plan, in order: (1) customer Your picks shows fridges first, (2) one shared pick card on both pages, (3) a "Show customer" full-screen view on the floor tool, (4) a wording pass with a word budget. **Step 1 done:** the 8-row What we checked box became a compact status strip (progress bar, one line, one button, checks folded); cards cut to brand + style, price, 3 key facts, verdict, 2 reasons, See today's price, with the rest under More details; pick tabs no longer read "Whirlpool / Whirlpool / Whirlpool"; Before you buy moved to the end of Measure as "Before delivery day" without the duplicated measure items; come-back box shortened. Product photos would help most but need outside images (homedepot.com), which breaks the self-contained rule; ask the supervisor along with the QR question.

- **Nov 8: floor tool cleanup (cleanup steps 2 and 3).** One shared card top, `pickTop()`, now draws picks on both the floor tool's Options view and the customer page, styled in `theme.css`. Options cards trimmed the same way (2 reasons, Good to know folded, no power-cost line). New "Show customer" full-screen view for turning the phone around (Customer tab button and Options bar; Done returns). Customer tab: no intro text, plain step labels, the big "Walk them to this size" callout became a slim dark strip above the picks with talking points folded, quick-pick rows lead with brand + style and price, and the redundant "See the fridges that fit" button is gone (the dock has Fridges). Budget chips now cover a range (Under $1k + $1–2k = under $2,000), per Julian's ask.

## Open questions / next up
- Cleanup step 4: wording pass with a word budget across both pages (Fridges tab list and Take-home tab not touched yet).
- The scheduled task "Floor Copilot weekly price refresh" (id `floor-copilot-weekly-price-refresh`, cron `13 21 * * 0` local ET, a few minutes of dispatch jitter) was recreated on Nov 8. It checks out `main` (skips if the tree is dirty), pulls, sets `HV_WATCH` from `check_catalog.py --js`, harvests in the built-in browser, reads `HV.reportText()`, saves rows with `receive_rows.py`, runs `apply_refresh.py` + `build.py`, commits as Julian and pushes `main`, then switches back. It skips with a note if `main` lacks `check_catalog.py` / `receive_rows.py` (they reached `main` with PR #2 on Nov 8). Not yet run once by hand; do a "Run now" from the app to pre-approve its browser and shell tools.
- Talk to the department supervisor before handing out many more QR codes (customer page names Julian and the store, and shows scraped prices and promos).
- Which code Home Depot shelf tags actually carry. Test on the floor (walk-the-aisle mode is a good first test) and adjust `matchCode()` if needed.
- Promo tiers and end date (Spend More Save More, through Dec 2) are hard-coded; make them data-driven before Black Friday promos change.
- Catalog gaps: 744 of 745 fridges lack kWh/yr, 26 have no price, 5 have no brand (Cafe and a few others), no UPCs. Fix in `harvest.js`.
- Returnability skews the ranking: almost every Whirlpool, GE, Samsung, LG, KitchenAid fridge is non-returnable, while ZLINE, Summit, Avanti, Koolmore and other online brands are returnable. The -2 no-returns penalty therefore favors those brands; price sanity offsets ZLINE. Revisit if off-brand picks show up too often.
- 648 of 745 fridges are tagged online only by the harvest, including some on display; the tag is info only now.
