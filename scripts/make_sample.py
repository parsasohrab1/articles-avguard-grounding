"""Draw the language-model sample from data/records.csv. Writes outputs/llm_sample.csv and corpus_meta.json."""

import csv
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from avguard.llm_audit import NARRATIVE_CHARS, SEED  # noqa: E402

N_SAMPLE = 200
csv.field_size_limit(10**8)


def main():
    source = ROOT / "data" / "records.csv"
    rows = list(csv.DictReader(source.open(encoding="utf-8", newline="")))
    if len(rows) < N_SAMPLE:
        raise SystemExit(f"need at least {N_SAMPLE} records, found {len(rows)}")
    years = [int(r["year"]) for r in rows]
    meta = {
        "n_records": len(rows),
        "year_min": min(years),
        "year_max": max(years),
        "source": "NTSB Pre2008",
    }
    pick = np.random.default_rng(SEED).choice(len(rows), size=N_SAMPLE, replace=False)
    pick.sort()
    out_dir = ROOT / "outputs"
    out_dir.mkdir(exist_ok=True)
    fieldnames = [
        "ev_id",
        "year",
        "narrative",
        "injury",
        "weather",
        "light",
        "midair",
        "n_chars_full",
    ]
    with (out_dir / "llm_sample.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for i in pick:
            row = rows[int(i)]
            full = row["narrative"]
            writer.writerow(
                {
                    "ev_id": row["ev_id"],
                    "year": row["year"],
                    "narrative": full[:NARRATIVE_CHARS],
                    "injury": row["injury"],
                    "weather": row["weather"],
                    "light": row["light"],
                    "midair": row["midair"],
                    "n_chars_full": len(full),
                }
            )
    (out_dir / "corpus_meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")
    print(
        "sample", N_SAMPLE, "corpus", meta["n_records"], "years", meta["year_min"], meta["year_max"]
    )


if __name__ == "__main__":
    main()
