"""Route a support score to accept, review, or flag, and append a JSONL audit row."""

import json
import time


def route(score, t_accept, t_reject):
    if score > t_accept:
        return "auto_accept"
    if score < t_reject:
        return "flag_contradicted"
    return "human_review"


def audit_record(claim_id, field, value, score, decision, evidence=None):
    return dict(
        ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        claim_id=claim_id,
        field=field,
        value=value,
        score=round(float(score), 4),
        decision=decision,
        evidence=evidence,
        reviewer=None,
        final=None,
    )


def write_audit(path, rows):
    with open(path, "a", encoding="utf8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
