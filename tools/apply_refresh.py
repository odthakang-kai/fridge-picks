#!/usr/bin/env python3
"""Swap a freshly harvested catalog into one or more built pages.

usage: python3 tools/apply_refresh.py ROWS_FILE YYYY-MM-DD FILE [FILE ...]
ROWS_FILE has one fridge per line, 31 pipe-separated fields (see CLAUDE.md).
Changes nothing and exits non-zero if the data looks wrong."""
import re, sys

import os
rows_f, day, files = sys.argv[1], sys.argv[2], sys.argv[3:]
# The home-screen app (app/index.html) rides along whenever this repo's index.html is refreshed,
# so the weekly task does not need to list it.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_page = os.path.join(ROOT, "app", "index.html")
if any(os.path.abspath(f) == os.path.join(ROOT, "index.html") for f in files) and os.path.exists(app_page) \
        and all(os.path.abspath(f) != app_page for f in files):
    files.append(app_page)
rows = [l.strip() for l in open(rows_f, encoding="utf-8") if l.strip()]
bad = [r for r in rows if r.count("|") != 30]
ids = [r.split("|")[0] for r in rows]
problems = []
if not files: problems.append("no files given")
if len(rows) < 600: problems.append(f"only {len(rows)} rows (expected 700+)")
if bad: problems.append(f"{len(bad)} rows with the wrong field count")
if len(set(ids)) != len(ids): problems.append("duplicate item ids")
if any("`" in r or "${" in r for r in rows): problems.append("unsafe characters in rows")
if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day): problems.append("bad date")
if problems:
    print("ABORT:", "; ".join(problems)); sys.exit(1)
cat = "\n".join(rows)
out = {}
for f in files:
    s = open(f, encoding="utf-8").read()
    s2, n1 = re.subn(r"const RAW=`[\s\S]*?`;", lambda m: "const RAW=`" + cat + "`;", s, count=1)
    s2, n2 = re.subn(r'const DATA_DATE=new Date\("\d{4}-\d{2}-\d{2}T12:00:00"\)',
                     f'const DATA_DATE=new Date("{day}T12:00:00")', s2, count=1)
    if n1 != 1 or n2 != 1:
        print(f"ABORT: could not find the catalog or date in {f}"); sys.exit(1)
    out[f] = s2
for f, s2 in out.items():
    open(f, "w", encoding="utf-8").write(s2)
print(f"OK: {len(rows)} fridges, prices dated {day}, {len(files)} files updated")
