from avguard.render import abstract_text


def _field(match_rate=0.5, false_accept=None, status="not_estimated"):
    return {
        "n": 10,
        "n_answered": 8,
        "n_abstain": 2,
        "n_match": 4,
        "n_mismatch": 4,
        "match_rate_answered": match_rate,
    }, {
        "status": status,
        "reason": "",
        "n_false_cal": 20 if status == "estimated" else 2,
        "n_false_test": 5,
        "n_true_test": 5,
        "mean_score_true_test": 0.8,
        "mean_score_false_test": 0.3,
        "alpha": 0.05,
        "threshold": 0.4,
        "false_accept": false_accept,
        "true_accept": 0.9 if false_accept is not None else None,
        "flagged_false": None,
        "flagged_true": None,
    }


def _results(status="not_estimated", false_accept=None):
    claims = {}
    support = {}
    for name in ("injury", "weather", "light", "midair"):
        claim, audit = _field(status=status, false_accept=false_accept)
        claims[name] = claim
        support[name] = audit
    return {
        "provenance": {
            "model": "example-model",
            "sample_n": 10,
            "corpus_n": 100,
            "years": [1974, 2007],
        },
        "claims": {
            "n_slots": 40,
            "n_answered": 32,
            "n_abstain": 8,
            "n_match": 16,
            "n_mismatch": 16,
            "match_rate_answered": 0.5,
            "by_field": claims,
        },
        "support": {"n_train": 6, "n_cal": 2, "n_test": 2, "by_field": support},
    }


def test_abstract_length_when_cutoff_missing():
    text = abstract_text(_results())
    assert 150 <= len(text.split()) <= 250
    assert "example-model" in text
    assert "no false-accept share is stated" in text


def test_abstract_length_when_cutoff_estimated():
    text = abstract_text(_results(status="estimated", false_accept=0.25))
    assert 150 <= len(text.split()) <= 250
    assert "25.0%" in text
