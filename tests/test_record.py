import json
from pathlib import Path

from avguard.record import registration_markdown

ROOT = Path(__file__).resolve().parents[1]


def test_registration_card_matches_the_results_file():
    payload = json.loads((ROOT / "outputs" / "results.json").read_text(encoding="utf-8"))
    card = (ROOT / "docs" / "REGISTRATION.md").read_text(encoding="utf-8")
    assert card == registration_markdown(payload)
    assert "ارسال نشده" in card
    assert "avguard" in card
    assert payload["provenance"]["model"] in card
    assert "0.013921" not in card
    assert "sk-ant-" not in card
