"""Build data/records.csv from the public NTSB aviation accident database (pre-2008 release, MS Access).
Usage: python scripts/prepare_data.py PATH/Pre2008.mdb   (download: data.ntsb.gov/avdata, file 'pre2008.zip')
Keeps one narrative per event (probable-cause narrative 'narr_accp') and four structured fields used as ground truth."""
import csv, os, sys
from access_parser import AccessParser

LIGHT = {"DAYL": "day", "NITE": "night", "NDRK": "night", "NBRT": "night", "DUSK": "twilight", "DAWN": "twilight"}
db = AccessParser(sys.argv[1])
nar, ev = db.parse_table("narratives"), db.parse_table("events")
text = {}
for i, e in enumerate(nar["ev_id"]):
    t = nar["narr_accp"][i]
    if isinstance(t, str) and len(t) >= 120 and e not in text:
        text[e] = " ".join(t.split())
os.makedirs("data", exist_ok=True)
n = 0
with open("data/records.csv", "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["ev_id", "year", "narrative", "injury", "weather", "light", "midair"])
    for i, e in enumerate(ev["ev_id"]):
        if e not in text: continue
        inj, wx, lc = ev["ev_highest_injury"][i], ev["wx_cond_basic"][i], LIGHT.get(ev["light_cond"][i])
        if inj not in ("NONE", "MINR", "SERS", "FATL") or wx not in ("VMC", "IMC") or lc not in ("day", "night"): continue
        w.writerow([e, ev["ev_year"][i], text[e], inj, wx, lc, "yes" if ev["mid_air"][i] in ("Y", "YES", 1, True) else "no"]); n += 1
print("records", n)
