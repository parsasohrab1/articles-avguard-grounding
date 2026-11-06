from avguard.llm_audit import (
    claims_from_reply,
    field_counts,
    label_claims,
    normalize_value,
    support_report,
)


def test_normalize_known_codes_and_unknown():
    assert normalize_value("injury", "fatal") == "FATL"
    assert normalize_value("weather", "VMC") == "VMC"
    assert normalize_value("light", "Night") == "night"
    assert normalize_value("midair", "maybe") == "unknown"
    assert normalize_value("injury", None) == "unknown"


def test_claims_from_fenced_json():
    raw = (
        '```json\n{"injury":"MINR","weather":"imc","light":"day","midair":"no","summary":"x"}\n```'
    )
    rows = claims_from_reply(raw)
    assert [r["value"] for r in rows] == ["MINR", "IMC", "day", "no"]
    assert all(r["answered"] for r in rows)


def test_unparseable_reply_abstains():
    rows = claims_from_reply("I cannot tell.")
    assert len(rows) == 4
    assert all(not r["answered"] for r in rows)


def test_field_counts_match_rate():
    claims = label_claims(
        [
            {"field": "injury", "value": "NONE", "answered": True},
            {"field": "injury", "value": "FATL", "answered": True},
            {"field": "injury", "value": "unknown", "answered": False},
        ],
        {"injury": "NONE"},
    )
    stats = field_counts(claims)["by_field"]["injury"]
    assert stats["n_match"] == 1
    assert stats["n_mismatch"] == 1
    assert stats["n_abstain"] == 1
    assert stats["match_rate_answered"] == 0.5


def test_support_not_estimated_when_few_mismatches():
    cal = [{"field": "injury", "answered": True, "correct": False, "score": 0.2}]
    test = [
        {"field": "injury", "answered": True, "correct": True, "score": 0.9},
        {"field": "injury", "answered": True, "correct": False, "score": 0.1},
    ]
    report = support_report(test, cal)
    assert report["injury"]["status"] == "not_estimated"
    assert report["injury"]["false_accept"] is None


def test_sources_do_not_embed_a_key():
    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    for path in list(root.joinpath("src").rglob("*.py")) + list(
        root.joinpath("scripts").rglob("*.py")
    ):
        text = path.read_text(encoding="utf-8")
        assert "sk-ant-" not in text
        assert "ANTHROPIC_API_KEY=" not in text
