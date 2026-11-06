"""Fit the support-score model on the training split and write outputs/support_scores.jsonl."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from avguard.claims import FIELDS  # noqa: E402
from avguard.llm_audit import (
    SEED,
    claims_from_reply,
    label_claims,
    last_by_id,
    load_jsonl,
    split_indices,
)  # noqa: E402
from avguard.rebuild import load_sample  # noqa: E402
from avguard.verifier import Verifier  # noqa: E402


def main():
    sample = load_sample(ROOT / "outputs" / "llm_sample.csv")
    replies = last_by_id(load_jsonl(ROOT / "outputs" / "llm_responses.jsonl"))
    texts = [row["narrative"] for row in sample]
    train, cal, test = split_indices(len(sample), SEED)
    cal_ids = {sample[i]["ev_id"] for i in cal}
    test_ids = {sample[i]["ev_id"] for i in test}
    models = {}
    for field in FIELDS:
        labels = [row[field] for row in sample]
        try:
            models[field] = Verifier(field, min_df=1, max_features=20000).fit(
                [texts[i] for i in train], [labels[i] for i in train]
            )
        except ValueError as exc:
            models[field] = str(exc)
    dest = ROOT / "outputs" / "support_scores.jsonl"
    n = 0
    with dest.open("w", encoding="utf-8") as handle:
        for row in sample:
            if row["ev_id"] not in cal_ids and row["ev_id"] not in test_ids:
                continue
            claims = label_claims(claims_from_reply(replies[row["ev_id"]]["raw"]), row)
            answered = [c for c in claims if c["answered"]]
            if not answered:
                continue
            model = None
            for claim in answered:
                model = models[claim["field"]]
                if isinstance(model, str):
                    rec = {
                        "ev_id": row["ev_id"],
                        "field": claim["field"],
                        "score": None,
                        "reason": model,
                    }
                else:
                    score = float(model.score([row["narrative"]], [claim["value"]])[0])
                    rec = {"ev_id": row["ev_id"], "field": claim["field"], "score": round(score, 6)}
                handle.write(json.dumps(rec) + "\n")
                n += 1
    print("scores", n, dest)


if __name__ == "__main__":
    main()
