#!/usr/bin/env python3
"""Cross-reference fridges you know exist against the catalog in index.html.

Checks data/watchlist.txt, plus (optionally) a Floor Copilot backup code and any models you type.
Reports what is in the catalog and what is missing, so the next harvest can look the missing ones up.

usage:
  python tools/check_catalog.py                      # watchlist only
  python tools/check_catalog.py LF30S8210S WRT518SZFM # also these models / Internet #s / store SKUs
  python tools/check_catalog.py --backup FC1:...      # also the phone's floor list and "Not in the catalog" scans
  python tools/check_catalog.py --add ...             # append missing models to data/watchlist.txt
  python tools/check_catalog.py --js                  # print the window.HV_WATCH line for tools/harvest.js
Exits 1 when anything on the watchlist is missing.
"""
import argparse, base64, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WATCH = os.path.join(ROOT, "data", "watchlist.txt")


def norm(v):
    return re.sub(r"[^A-Z0-9]", "", str(v or "").upper())


def read_watchlist(path=WATCH):
    """Entries from the watchlist: one per line, '#' starts a comment."""
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path, encoding="utf-8"):
        e = line.split("#", 1)[0].strip()
        if e:
            out.append(e)
    return out


def read_catalog(page=os.path.join(ROOT, "index.html")):
    s = open(page, encoding="utf-8").read()
    m = re.search(r"const RAW=`([\s\S]*?)`;", s)
    if not m:
        sys.exit(f"could not find the catalog in {page}")
    return [l.split("|") for l in m.group(1).split("\n") if l.strip()]


def finder(rows):
    by_id = {r[0]: r for r in rows}
    by_sku = {r[1].lstrip("0"): r for r in rows if r[1]}
    by_model = {norm(r[2]): r for r in rows if r[2]}

    def find(code):
        n = norm(code)
        if not n:
            return None
        if n in by_id:
            return by_id[n]
        if n.isdigit() and n.lstrip("0") in by_sku:
            return by_sku[n.lstrip("0")]
        if n in by_model:
            return by_model[n]
        if len(n) >= 7:  # model inside a longer scanned string
            for k, r in by_model.items():
                if len(k) >= 7 and k in n:
                    return r
        return None
    return find


def read_backup(code):
    """Decode an FC1 backup from the app's Take-home tab."""
    t = code.strip()
    if t.startswith("FC1:"):
        t = t[4:]
    t += "=" * (-len(t) % 4)
    return json.loads(base64.b64decode(t).decode("utf-8"))


def looks_like_model(code):
    """True for model numbers; False for bare UPC/EAN barcodes, which the harvest cannot search for."""
    n = norm(code)
    return bool(n) and not (n.isdigit() and len(n) in (8, 12, 13, 14))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codes", nargs="*", help="model numbers, Internet #s or store SKUs to check")
    ap.add_argument("--backup", help="FC1 backup code from Take-home > Saved on this phone")
    ap.add_argument("--add", action="store_true", help="append missing models to data/watchlist.txt")
    ap.add_argument("--js", action="store_true", help="print the window.HV_WATCH line and exit")
    a = ap.parse_args()

    watch = read_watchlist()
    if a.js:
        print("window.HV_WATCH=" + json.dumps(watch) + ";")
        return 0

    rows = read_catalog()
    find = finder(rows)
    checks = [(c, "watchlist") for c in watch] + [(c, "typed") for c in a.codes]
    floor_ids = []
    if a.backup:
        b = read_backup(a.backup)
        for k, v in (b.get("m") or {}).items():
            raw = v.get("raw", k) if isinstance(v, dict) else k
            aisle = v.get("a") if isinstance(v, dict) else ""
            checks.append((raw, "scanned, not found" + (f" ({aisle})" if aisle else "")))
        floor_ids = list((b.get("f2") or b.get("f") or {}).keys())

    print(f"Catalog: {len(rows)} fridges in index.html\n")
    missing, barcodes, seen = [], [], set()
    for code, src in checks:
        if norm(code) in seen:
            continue
        seen.add(norm(code))
        r = find(code)
        if r:
            print(f"  ok       {code:<22} {r[3]} {r[2]} (#{r[0]})  [{src}]")
        elif looks_like_model(code):
            missing.append((code, src))
            print(f"  MISSING  {code:<22} [{src}]")
        else:
            barcodes.append((code, src))
            print(f"  barcode  {code:<22} [{src}]  box barcode: find the model on the tag, or link it by hand in the app")
    gone = [i for i in floor_ids if not find(i)]
    for i in gone:
        print(f"  GONE     #{i:<21} [on the floor list, no longer in the catalog]")

    print(f"\n{len(missing)} missing, {len(barcodes)} barcode only, {len(gone)} floor fridges gone from the catalog")
    if a.add and missing:
        known = {norm(w) for w in watch}
        new = [c for c, _ in missing if norm(c) not in known]
        if new:
            with open(WATCH, "a", encoding="utf-8", newline="\n") as f:
                for c in new:
                    f.write(f"{c.strip().upper()}\n")
            print(f"added to data/watchlist.txt: {', '.join(new)}")
    return 1 if any(src == "watchlist" for _, src in missing) else 0


if __name__ == "__main__":
    sys.exit(main())
