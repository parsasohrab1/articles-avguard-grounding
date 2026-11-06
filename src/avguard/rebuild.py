"""Rebuild results.json from saved model replies and saved support scores. Does not call a model."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from avguard.llm_audit import (
    ALPHA,
    MIN_FALSE_CAL,
    NARRATIVE_CHARS,
    SEED,
    T_REJECT,
    claims_from_reply,
    field_counts,
    label_claims,
    last_by_id,
    load_jsonl,
    model_name,
    response_digest,
    sha256_bytes,
    split_indices,
    support_report,
)


def _root_files(root: Path) -> tuple[Path, Path, Path, Path]:
    out = root / "outputs"
    return (
        out / "llm_sample.csv",
        out / "llm_responses.jsonl",
        out / "support_scores.jsonl",
        out / "corpus_meta.json",
    )


def load_sample(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def rebuild(root: Path) -> dict:
    sample_path, reply_path, score_path, meta_path = _root_files(root)
    sample = load_sample(sample_path)
    replies = last_by_id(load_jsonl(reply_path))
    scores = {}
    for row in load_jsonl(score_path):
        scores[(str(row["ev_id"]), row["field"])] = row
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    missing = [row["ev_id"] for row in sample if row["ev_id"] not in replies]
    if missing:
        raise SystemExit(f"{len(missing)} sample rows have no model reply")
    ids = [row["ev_id"] for row in sample]
    labeled = []
    for row in sample:
        claims = label_claims(claims_from_reply(replies[row["ev_id"]]["raw"]), row)
        for claim in claims:
            claim["ev_id"] = row["ev_id"]
        labeled.extend(claims)
    train, cal, test = split_indices(len(sample), SEED)
    cal_ids = {sample[i]["ev_id"] for i in cal}
    test_ids = {sample[i]["ev_id"] for i in test}
    heldout = [c for c in labeled if c["answered"] and c["ev_id"] in cal_ids | test_ids]
    absent = [c for c in heldout if (c["ev_id"], c["field"]) not in scores]
    if absent:
        raise SystemExit(f"{len(absent)} held-out claims have no support-score row")

    def _with_score(id_set):
        rows = []
        for claim in labeled:
            if claim["ev_id"] not in id_set or not claim["answered"]:
                continue
            saved = scores[(claim["ev_id"], claim["field"])]
            if saved.get("score") is None:
                continue
            rows.append({**claim, "score": float(saved["score"])})
        return rows

    blocked = {}
    for claim in heldout:
        saved = scores[(claim["ev_id"], claim["field"])]
        if saved.get("score") is None:
            blocked[claim["field"]] = saved.get("reason") or "support score missing"
    report = support_report(_with_score(test_ids), _with_score(cal_ids), ALPHA)
    for field, reason in blocked.items():
        cal_rows = [
            c for c in labeled if c["field"] == field and c["ev_id"] in cal_ids and c["answered"]
        ]
        test_rows = [
            c for c in labeled if c["field"] == field and c["ev_id"] in test_ids and c["answered"]
        ]
        report[field] = {
            "status": "not_estimated",
            "reason": reason,
            "n_false_cal": sum(1 for c in cal_rows if not c["correct"]),
            "n_false_test": sum(1 for c in test_rows if not c["correct"]),
            "n_true_test": sum(1 for c in test_rows if c["correct"]),
            "mean_score_true_test": None,
            "mean_score_false_test": None,
            "alpha": ALPHA,
            "threshold": None,
            "false_accept": None,
            "true_accept": None,
            "flagged_false": None,
            "flagged_true": None,
        }
    n_truncated = sum(1 for row in sample if int(row["n_chars_full"]) > len(row["narrative"]))
    return {
        "provenance": {
            "corpus_n": int(meta["n_records"]),
            "years": [int(meta["year_min"]), int(meta["year_max"])],
            "sample_n": len(sample),
            "seed": SEED,
            "model": model_name({i: replies[i] for i in ids}),
            "narrative_chars": NARRATIVE_CHARS,
            "n_truncated": n_truncated,
            "response_sha256": response_digest(ids, replies),
            "sample_sha256": sha256_bytes(sample_path.read_bytes().replace(b"\r\n", b"\n")),
            "alpha": ALPHA,
            "t_reject": T_REJECT,
            "min_false_cal": MIN_FALSE_CAL,
            "api_key_in_repo": False,
        },
        "claims": field_counts(labeled),
        "support": {
            "n_train": int(len(train)),
            "n_cal": int(len(cal)),
            "n_test": int(len(test)),
            "by_field": report,
        },
    }
