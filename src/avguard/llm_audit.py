"""Parse language-model replies and count claim matches. No cutoff recipe is stated here."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter

import numpy as np

from avguard.claims import FIELDS
from avguard.conformal import false_accept_threshold, rates
from avguard.workflow import route

SEED = 0
ALPHA = 0.05
T_REJECT = 0.05
MIN_FALSE_CAL = 20
NARRATIVE_CHARS = 3000

_ALIASES = {
    "injury": {
        "none": "NONE",
        "no injury": "NONE",
        "uninjured": "NONE",
        "minr": "MINR",
        "minor": "MINR",
        "sers": "SERS",
        "serious": "SERS",
        "fatl": "FATL",
        "fatal": "FATL",
        "killed": "FATL",
    },
    "weather": {
        "vmc": "VMC",
        "visual": "VMC",
        "imc": "IMC",
        "instrument": "IMC",
    },
    "light": {
        "day": "day",
        "daylight": "day",
        "night": "night",
        "dark": "night",
    },
    "midair": {
        "yes": "yes",
        "y": "yes",
        "true": "yes",
        "no": "no",
        "n": "no",
        "false": "no",
    },
}
_UNKNOWN = {"", "unknown", "n/a", "na", "unclear", "not stated", "not mentioned", "none stated"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_indices(n: int, seed: int = SEED):
    idx = np.random.default_rng(seed).permutation(n)
    a, b = int(0.6 * n), int(0.8 * n)
    return idx[:a], idx[a:b], idx[b:]


def normalize_value(field: str, value) -> str:
    if value is None:
        return "unknown"
    text = re.sub(r"\s+", " ", str(value).strip().lower())
    if text in _UNKNOWN:
        return "unknown"
    mapped = _ALIASES[field].get(text)
    if mapped in FIELDS[field]:
        return mapped
    return "unknown"


def parse_reply(raw: str) -> dict | None:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fence:
        text = fence.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def claims_from_reply(raw: str) -> list[dict]:
    parsed = parse_reply(raw)
    rows = []
    for field in FIELDS:
        value = "unknown" if parsed is None else normalize_value(field, parsed.get(field))
        rows.append({"field": field, "value": value, "answered": value != "unknown"})
    return rows


def label_claims(claim_rows: list[dict], truth: dict) -> list[dict]:
    labeled = []
    for row in claim_rows:
        correct = bool(row["answered"] and row["value"] == truth[row["field"]])
        labeled.append({**row, "correct": correct})
    return labeled


def _rate(num: int, den: int):
    if den == 0:
        return None
    return round(num / den, 6)


def field_counts(claims: list[dict]) -> dict:
    out = {}
    for field in FIELDS:
        rows = [c for c in claims if c["field"] == field]
        n_answered = sum(1 for c in rows if c["answered"])
        n_match = sum(1 for c in rows if c["correct"])
        n_mismatch = sum(1 for c in rows if c["answered"] and not c["correct"])
        out[field] = {
            "n": len(rows),
            "n_answered": n_answered,
            "n_abstain": len(rows) - n_answered,
            "n_match": n_match,
            "n_mismatch": n_mismatch,
            "match_rate_answered": _rate(n_match, n_answered),
        }
    n_slots = len(claims)
    n_answered = sum(1 for c in claims if c["answered"])
    n_match = sum(1 for c in claims if c["correct"])
    n_mismatch = sum(1 for c in claims if c["answered"] and not c["correct"])
    return {
        "n_slots": n_slots,
        "n_answered": n_answered,
        "n_abstain": n_slots - n_answered,
        "n_match": n_match,
        "n_mismatch": n_mismatch,
        "match_rate_answered": _rate(n_match, n_answered),
        "by_field": out,
    }


def support_report(test_claims: list[dict], cal_claims: list[dict], alpha: float = ALPHA) -> dict:
    """test_claims and cal_claims need keys correct, answered, score, and only answered rows."""
    by_field = {}
    for field in FIELDS:
        cal = [c for c in cal_claims if c["field"] == field]
        te = [c for c in test_claims if c["field"] == field]
        false_cal = [c["score"] for c in cal if not c["correct"]]
        false_te = [c for c in te if not c["correct"]]
        true_te = [c for c in te if c["correct"]]
        rec = {
            "status": "not_estimated",
            "reason": "",
            "n_false_cal": len(false_cal),
            "n_false_test": len(false_te),
            "n_true_test": len(true_te),
            "mean_score_true_test": _mean([c["score"] for c in true_te]),
            "mean_score_false_test": _mean([c["score"] for c in false_te]),
            "alpha": alpha,
            "threshold": None,
            "false_accept": None,
            "true_accept": None,
            "flagged_false": None,
            "flagged_true": None,
        }
        if len(false_cal) < MIN_FALSE_CAL:
            rec["reason"] = f"fewer than {MIN_FALSE_CAL} mismatched calibration claims"
        elif not false_te or not true_te:
            rec["reason"] = "held-out split has no matched or no mismatched claim"
        else:
            threshold = float(false_accept_threshold(np.asarray(false_cal, dtype=float), alpha))
            got = rates(
                np.asarray([c["score"] for c in true_te], dtype=float),
                np.asarray([c["score"] for c in false_te], dtype=float),
                threshold,
            )
            rec.update(
                {
                    "status": "estimated",
                    "reason": "",
                    "threshold": None if np.isinf(threshold) else round(threshold, 6),
                    "false_accept": round(got["false_accept"], 6),
                    "true_accept": round(got["true_accept"], 6),
                    "flagged_false": _rate(
                        sum(
                            1
                            for c in false_te
                            if route(c["score"], threshold, T_REJECT) == "flag_contradicted"
                        ),
                        len(false_te),
                    ),
                    "flagged_true": _rate(
                        sum(
                            1
                            for c in true_te
                            if route(c["score"], threshold, T_REJECT) == "flag_contradicted"
                        ),
                        len(true_te),
                    ),
                }
            )
        by_field[field] = rec
    return by_field


def _mean(values: list[float]):
    if not values:
        return None
    return round(float(np.mean(values)), 6)


def load_jsonl(path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def last_by_id(rows: list[dict]) -> dict[str, dict]:
    out = {}
    for row in rows:
        out[str(row["ev_id"])] = row
    return out


def response_digest(sample_ids: list[str], replies: dict[str, dict]) -> str:
    blob = "\n".join(replies[i]["raw"] for i in sample_ids)
    return sha256_bytes(blob.encode("utf-8"))


def model_name(replies: dict[str, dict]) -> str:
    names = Counter(r.get("model", "") for r in replies.values())
    return names.most_common(1)[0][0]
