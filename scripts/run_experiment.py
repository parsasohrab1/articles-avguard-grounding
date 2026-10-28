"""Reproduces outputs/results.json from data/records.csv (see prepare_data.py)."""
import csv, json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from avguard import claims, conformal, verifier
from avguard.workflow import route

csv.field_size_limit(10**8)
rows = list(csv.DictReader(open(os.path.join(os.path.dirname(__file__), "..", "data", "records.csv"), encoding="utf8")))
text = np.array([r["narrative"] for r in rows]); year = np.array([int(r["year"]) for r in rows])
ALPHAS, T_REJECT = (0.05, 0.10), 0.05
out = {"n_records": len(rows), "years": [int(year.min()), int(year.max())], "alphas": list(ALPHAS), "t_reject": T_REJECT, "splits": {}}


def run(tr, ca, te, field, seed):
    lab = np.array([r[field] for r in rows]); rng = np.random.default_rng(seed)
    v = verifier.Verifier(field).fit(text[tr], lab[tr]); Pca, Pte = v.proba(text[ca]), v.proba(text[te])
    res = {"verifier_accuracy": float(np.mean(v.clf.classes_[Pte.argmax(1)] == lab[te]))}
    ct, cf = claims.make_claims(lab[ca], field, rng); tt, tf = claims.make_claims(lab[te], field, rng)
    sc_t, sc_f = v.score(None, ct, Pca), v.score(None, cf, Pca); st_t, st_f = v.score(None, tt, Pte), v.score(None, tf, Pte)
    for a in ALPHAS:
        t = conformal.false_accept_threshold(sc_f, a); r = conformal.rates(st_t, st_f, t)
        r["review_share_true"] = float(np.mean([route(s, t, T_REJECT) == "human_review" for s in st_t]))
        r["flagged_false"] = float(np.mean(st_f < T_REJECT)); r["flagged_true"] = float(np.mean(st_t < T_REJECT)); r["threshold"] = float(t)
        res[f"alpha_{a}"] = r
    return res


def avg(runs):
    def m(d):
        keys = d[0].keys(); return {k: ({kk: [float(np.mean([x[k][kk] for x in d])), float(np.std([x[k][kk] for x in d]))] for kk in d[0][k]} if isinstance(d[0][k], dict) else [float(np.mean([x[k] for x in d])), float(np.std([x[k] for x in d]))]) for k in keys}
    return m(runs)


for field in claims.FIELDS:
    runs = []
    for s in range(3):
        idx = np.random.default_rng(s).permutation(len(rows)); a, b = int(.6 * len(idx)), int(.8 * len(idx))
        runs.append(run(idx[:a], idx[a:b], idx[b:], field, s))
    out["splits"].setdefault("random", {})[field] = avg(runs)
    tr, ca, te = np.where(year <= 1994)[0], np.where((year >= 1995) & (year <= 1999))[0], np.where(year >= 2000)[0]
    out["splits"].setdefault("temporal", {})[field] = {"n_train": int(len(tr)), "n_cal": int(len(ca)), "n_test": int(len(te)),
                                                       **avg([run(tr, ca, te, field, s) for s in range(3)])}
    print(field, out["splits"]["random"][field]["alpha_0.05"]["false_accept"], out["splits"]["temporal"][field]["alpha_0.05"]["false_accept"], flush=True)
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "outputs"), exist_ok=True)
json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "outputs", "results.json"), "w"), indent=1)
