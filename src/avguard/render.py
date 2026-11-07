"""Write README, TRL and the abstract from results.json. Measured figures are formatted here only."""

from __future__ import annotations

import json
from pathlib import Path

from avguard.record import registration_markdown

FIELDS = ("injury", "weather", "light", "midair")


def _pct(rate) -> str:
    if rate is None:
        return "n/a"
    return f"{100 * rate:.1f}%"


def _score(value) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}"


def _words(text: str) -> int:
    return len(text.split())


def _support_sentence(support: dict) -> str:
    estimated = [
        (name, row) for name, row in support["by_field"].items() if row["status"] == "estimated"
    ]
    if not estimated:
        return (
            "None of the four fields had enough mismatched calibration claims to fit a cutoff, "
            "so no false-accept share is stated."
        )
    if len(estimated) == 1:
        name, row = estimated[0]
        return (
            f"For {name}, {_pct(row['false_accept'])} of {row['n_false_test']} mismatched held-out claims "
            f"were above the cutoff, and {_pct(row['true_accept'])} of {row['n_true_test']} matched claims were."
        )
    lo = min(row["false_accept"] for _, row in estimated)
    hi = max(row["false_accept"] for _, row in estimated)
    return (
        f"Across {len(estimated)} fields with enough mismatched calibration claims, "
        f"the held-out share of mismatched claims above the cutoff ranged from {_pct(lo)} to {_pct(hi)}."
    )


def abstract_text(results: dict) -> str:
    prov = results["provenance"]
    claims = results["claims"]
    by = claims["by_field"]
    text = (
        "Language models can summarise an aviation occurrence and still state a fact the source narrative "
        "does not support. This study measured that risk on public records rather than on invented claims. "
        f"One language model ({prov['model']}) read a random sample of {prov['sample_n']} narratives from the "
        f"NTSB pre-2008 aviation database ({prov['corpus_n']} records, {prov['years'][0]}–{prov['years'][1]}) "
        "and was asked to state four values: highest injury, basic weather, light, and whether the event was "
        "a mid-air collision. It was instructed to answer unknown when the narrative did not say. Each answer "
        "was compared with the structured field stored for the same event. "
        f"Of {claims['n_slots']} field slots, the model gave a code for {claims['n_answered']} and abstained on "
        f"{claims['n_abstain']}. Among the codes it gave, {claims['n_match']} matched the structured field "
        f"({_pct(claims['match_rate_answered'])}) and {claims['n_mismatch']} did not. "
        f"Matched rates by field, among answered claims, were {_pct(by['injury']['match_rate_answered'])} for injury, "
        f"{_pct(by['weather']['match_rate_answered'])} for weather, {_pct(by['light']['match_rate_answered'])} for light "
        f"and {_pct(by['midair']['match_rate_answered'])} for mid-air. "
        "On a held-out part of the sample, a separate text classifier trained only on other narratives assigned "
        f"a support score to each stated code. {_support_sentence(results['support'])} "
        "The language model saw only the sample, so these rates are not a performance figure for the full database. "
        "No investigator reviewed the statements. Nothing here is a basis for accepting a summary in an investigation, "
        "and the calibration rule that turns a support score into a cutoff is not described in this abstract."
    )
    count = _words(text)
    if not 150 <= count <= 250:
        raise RuntimeError(f"abstract length {count} is outside 150–250 words")
    return text


def _field_table(claims: dict) -> str:
    lines = [
        "| field | slots | answered | matched | mismatched | abstained | match rate among answered |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in FIELDS:
        row = claims["by_field"][name]
        lines.append(
            f"| {name} | {row['n']} | {row['n_answered']} | {row['n_match']} | {row['n_mismatch']} | "
            f"{row['n_abstain']} | {_pct(row['match_rate_answered'])} |"
        )
    return "\n".join(lines)


def _support_table(support: dict) -> str:
    lines = [
        "| field | status | mismatched in calibration | false-accept on held-out | true-accept on held-out | mean score matched | mean score mismatched |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for name in FIELDS:
        row = support["by_field"][name]
        lines.append(
            f"| {name} | {row['status']} | {row['n_false_cal']} | {_pct(row['false_accept'])} | "
            f"{_pct(row['true_accept'])} | {_score(row['mean_score_true_test'])} | {_score(row['mean_score_false_test'])} |"
        )
    return "\n".join(lines)


def readme_text(results: dict) -> str:
    prov = results["provenance"]
    claims = results["claims"]
    return f"""# AvGuard-Ground (articles-avguard-grounding)

A language model reads a public NTSB narrative and states four field values. Each stated value is compared with the structured field on the same record. A text classifier trained on other narratives assigns a support score. The rule that turns that score into a cutoff is implemented in code and is not written out in this file. A patent attorney must review it before any public description or submission.

## Run

```
pip install -e ".[dev]"
pip install access-parser
python scripts/prepare_data.py data/Pre2008.mdb
python scripts/make_sample.py
python scripts/call_llm.py
python scripts/fit_support.py
python scripts/run_experiment.py
```

`call_llm.py` uses `ANTHROPIC_API_KEY` from the environment when it is set. Do not put the key in the repository, in a commit, or in `results.json`. When the key is unset, the same script runs a local model (`AVGUARD_LOCAL_MODEL`, default `Qwen/Qwen2.5-0.5B-Instruct`). `run_experiment.py` does not call the model. It rebuilds `outputs/results.json` from the saved replies and the saved support scores.

## Measured result

Corpus: {prov["corpus_n"]} NTSB pre-2008 records, years {prov["years"][0]}–{prov["years"][1]}. Language model `{prov["model"]}` on a random sample of {prov["sample_n"]} narratives (seed {prov["seed"]}). Narratives sent to the model were cut at {prov["narrative_chars"]} characters; {prov["n_truncated"]} sample rows were longer than that. Reply digest `{prov["response_sha256"][:12]}`.

Of {claims["n_slots"]} field slots, {claims["n_answered"]} were answered and {claims["n_abstain"]} were abstentions. Among answered claims, {claims["n_match"]} matched and {claims["n_mismatch"]} did not ({_pct(claims["match_rate_answered"])} matched).

{_field_table(claims)}

Support scores use a 60/20/20 split of the same sample (train {results["support"]["n_train"]}, calibration {results["support"]["n_cal"]}, held-out {results["support"]["n_test"]}). A cutoff is reported only when the calibration split has at least {prov["min_false_cal"]} mismatched claims for that field. Target level for that cutoff: alpha = {prov["alpha"]}.

{_support_table(results["support"])}

{_support_sentence(results["support"])}

Full numbers: `outputs/results.json`, rebuilt by `python scripts/run_experiment.py`.

## Limits

- One model and one sample. The model was not run on the full corpus.
- Four fields only. Abstaining is counted separately from a wrong code.
- The narratives are the public probable-cause text, mostly US general aviation, through 2007, and long ones were cut before the call.
- No investigator labelled the model’s wording. The structured NTSB field is the reference, and it can itself be coarse.
- A cutoff fit on this sample is not an operational guarantee.

## Journal

The Advanced Engineering Informatics special issue on large language models in aviation safety closed on 31 March 2026. This repository does not submit a manuscript. The basket card for article registration and achievements is `docs/REGISTRATION.md` (product id `avguard`). It is regenerated from `outputs/results.json`. The article status on that card is unsubmitted. See `docs/JOURNAL_FIT.md` and `docs/TRL.md`.
"""


def trl_text(results: dict) -> str:
    prov = results["provenance"]
    claims = results["claims"]
    return f"""# TRL assessment

Level reached: **TRL 3**. A script has been run on a sample of real public narratives with a real language model. That is a proof of concept on public data, not validation in an investigation.

| Level | Status | Evidence |
|---|---|---|
| TRL 1–2 | done | Field values stated by a model are checked against the source record. |
| TRL 3 | reached | Code, tests, and one real model call on {prov["sample_n"]} of {prov["corpus_n"]} NTSB records. Among answered claims, {_pct(claims["match_rate_answered"])} matched the structured field ({claims["n_match"]} of {claims["n_answered"]}). |
| TRL 4 | not reached | No investigator-in-the-loop study, and the model was not run on the full corpus. |
| TRL 5+ | not reached | No use on a current investigation and no operational audit trail in an agency system. |

The match rate above is copied from `outputs/results.json` by `scripts/run_experiment.py`. A low or incomplete support-score cutoff is a limit of this sample, not a hidden success. See the README table.
"""


def journal_fit_text() -> str:
    return """# Journal fitness — Advanced Engineering Informatics

Call: special issue “AI Trustworthiness and Applications of Large Language Models in Aviation Safety, Accident Investigation and Aircraft Engineering” (Advanced Engineering Informatics; guest editors Kam K.H. Ng, Wen-Chin Li, Chia-Fen Chi, Jens Schiefele).

Deadline on the call: 31 March 2026. As of this branch, that date has passed.

Earlier gate: mismatch. The call is about language models, and the previous write-up used value-swapped claims and did not run a language model.

This branch: a language model was run on a sample of public NTSB narratives. Claims are the values it stated, checked against the structured fields. That topic sits inside the call (trustworthiness of model statements used in accident investigation). The mismatch on “no language model” is closed by the run recorded in `outputs/results.json`.

Submission: not made, and not to be made to this special issue. The deadline has passed. Before any later submission to another call, complete the journal fitness gate in the Articles tab for that call, and have a patent attorney confirm that the cutoff rule is not disclosed.

The cutoff rule is in code so the saved scores can be aggregated. It is not described in the README, the abstract, or `docs/REGISTRATION.md`.

The internal filing card is [REGISTRATION.md](REGISTRATION.md). It is regenerated from `outputs/results.json`. The article status on that card is unsubmitted.
"""


def write_docs(root: Path, results: dict) -> None:
    (root / "README.md").write_text(readme_text(results), encoding="utf-8", newline="\n")
    (root / "docs").mkdir(exist_ok=True)
    (root / "docs" / "REGISTRATION.md").write_text(
        registration_markdown(results), encoding="utf-8", newline="\n"
    )
    (root / "docs" / "TRL.md").write_text(trl_text(results), encoding="utf-8", newline="\n")
    (root / "docs" / "JOURNAL_FIT.md").write_text(
        journal_fit_text(), encoding="utf-8", newline="\n"
    )
    abstract_dir = root / "article"
    abstract_dir.mkdir(exist_ok=True)
    body = abstract_text(results)
    keywords = "aviation safety; large language models; accident narratives; claim check; NTSB"
    title = (
        "What share of field values stated by a language model match the NTSB record? "
        "A sample of public occurrence narratives"
    )
    doc = f"# Abstract draft\n\n**Title:** {title}\n\n{body}\n\n**Keywords:** {keywords}\n\nWords in abstract: {_words(body)}\n"
    (abstract_dir / "abstract.md").write_text(doc, encoding="utf-8", newline="\n")


def load_results(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
