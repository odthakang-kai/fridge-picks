#!/usr/bin/env python3
"""Print Floor Copilot's top 3 auto picks for sample customers.

Loads the built floor tool in headless Chrome (Playwright), sets up each sample
customer through the page's own state and inputs, and runs the page's real
autoPicks() and match score. Nothing is re-implemented here, so what this prints
is what the phone shows on the Options tab.

usage:
  python3 tools/check_picks.py                    # build/floor-copilot.html
  python3 tools/check_picks.py --page other.html  # any built copy
  python3 tools/check_picks.py --json out.json    # also save results for diffing
  python3 tools/check_picks.py --floor            # seed a few floor fridges first

Needs: pip install playwright, and Google Chrome (or run `playwright install chromium`).
"""
import argparse, json, os, sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Each customer: household, habits, budget, measurements, quick-path answers.
CUSTOMERS = [
    ("Example kitchen (3 people, no budget)", dict(adults=2, kids=1, example=True)),
    ("Couple, $1,500 budget", dict(adults=2, kids=0, budget=1500)),
    ("Family of 5", dict(adults=2, kids=3)),
    ("Garage fridge", dict(adults=2, kids=0, habits=["garage"])),
    ("Wants a flush look, 36\" opening", dict(adults=2, kids=1, habits=["flush"], meas={"ow": "36"})),
    ("Tight 30\" doorway, 36\" opening", dict(adults=2, kids=1, meas={"ow": "36", "door": "30"})),
]

SETUP = """(cfg)=>{
  resetCustomer();
  if(cfg.example) document.getElementById('loadEx').click();
  S.adults=cfg.adults; S.kids=cfg.kids;
  document.getElementById('adults').textContent=cfg.adults; document.getElementById('kids').textContent=cfg.kids;
  for(const k of (cfg.habits||[])){const c=document.querySelector(`#habits .chip[data-k="${k}"]`); if(c) c.click();}
  if(cfg.budget) document.getElementById('budget').value=cfg.budget;
  for(const [id,v] of Object.entries(cfg.meas||{})) document.getElementById(id).value=v;
  all();
  const c=ctx(), a=autoPicks();
  const floorLbl=u=>typeof floorPickTxt==='function'?floorPickTxt(u):(onFloor(u)?'On the floor':'');
  return {size:`${c.n.lo}-${c.n.hi} cu ft`, relaxed:a.relaxed, picks:a.us.map(u=>{const f=fit(u,c.sp);
    return {brand:u.brand, model:u.model, style:STYLE[u.type], price:u.price, eff:effPrice(u), rating:u.rating, reviews:u.reviews||0,
      cap:u.cap, fit:fitWord(f), returnable:u.returnable, online:u.av==='O', floor:floorLbl(u),
      score:Math.round(matchScore({u,f},c)*100)/100};})};
}"""

SEED_FLOOR = """()=>{const pick=t=>CAT.filter(u=>u.type===t&&u.price&&u.reviews>200).sort((a,b)=>b.reviews-a.reviews)[0];
  const ids=[[pick('FD'),'Aisle 12, end cap'],[pick('BF'),'Aisle 12'],[pick('SS'),'Aisle 13'],[pick('TF'),'Aisle 13']].filter(x=>x[0]);
  for(const [u,a] of ids){ if(typeof floorSet==='function') floorSet(u.id,a); else {FLOOR[u.id]=a; saveFloor();} }
  return ids.map(([u,a])=>u.brand+' '+u.model+' @ '+a);}"""


def run(page_path, seed_floor):
    url = "file://" + os.path.abspath(page_path)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome")
        except Exception:
            browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 390, "height": 844})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url)
        pg.wait_for_function("typeof autoPicks==='function' && CAT.length>0")
        seeded = pg.evaluate(SEED_FLOOR) if seed_floor else []
        out = []
        for name, cfg in CUSTOMERS:
            r = pg.evaluate(SETUP, cfg)
            r["name"] = name
            out.append(r)
        browser.close()
        if errs:
            print("Page errors:", *errs, sep="\n  ", file=sys.stderr)
        return out, seeded


def money(v):
    return "no price" if v is None else f"${v:,.0f}"


def show(results, seeded):
    if seeded:
        print("Floor list seeded for this run:", *seeded, sep="\n  ")
        print()
    for r in results:
        print(f"== {r['name']}  (size box {r['size']}){'  relaxed: ' + ', '.join(r['relaxed']) if r['relaxed'] else ''}")
        for i, u in enumerate(r["picks"], 1):
            notes = [x for x in ("no returns" if not u["returnable"] else "", "online only" if u["online"] else "", u["floor"]) if x]
            price = money(u["price"]) + (f" ({money(u['eff'])} promo)" if u["eff"] != u["price"] and u["price"] else "")
            print(f"  {i}. {u['brand']} {u['model']:<16} score {u['score']:>6.2f}  "
                  f"{(u['rating'] or 0):.1f}* x{u['reviews']:<5} {u['style']:<15} {price:<22} {u['cap']} cu ft  {u['fit']}"
                  + (f"  [{', '.join(notes)}]" if notes else ""))
        if not r["picks"]:
            print("  (no picks)")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default=os.path.join(ROOT, "build", "floor-copilot.html"))
    ap.add_argument("--json")
    ap.add_argument("--floor", action="store_true", help="seed four floor fridges before running")
    a = ap.parse_args()
    res, seeded = run(a.page, a.floor)
    show(res, seeded)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(res, f, indent=1)
