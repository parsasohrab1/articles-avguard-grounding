"""Rebuild outputs/results.json and the measured docs from the saved model run. Does not call a model."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from avguard.rebuild import rebuild  # noqa: E402
from avguard.render import write_docs  # noqa: E402


def main():
    results = rebuild(ROOT)
    out = ROOT / "outputs" / "results.json"
    out.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    write_docs(ROOT, results)
    claims = results["claims"]
    print(
        "slots",
        claims["n_slots"],
        "answered",
        claims["n_answered"],
        "matched",
        claims["n_match"],
        "rate",
        claims["match_rate_answered"],
    )


if __name__ == "__main__":
    main()
