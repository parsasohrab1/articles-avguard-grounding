# AvGuard-Ground (articles-avguard-grounding)

Claim-level grounding audit for AI summaries of aviation occurrence narratives. A text model re-derives each claimed field value from the source narrative; a one-sided split-conformal threshold, calibrated on false claims, caps the share of false claims that are accepted. Claims are routed to auto-accept, human review, or flag-as-contradicted, and every decision is written to a JSONL audit trail.

## Run
```
pip install -r requirements.txt
python scripts/prepare_data.py     # builds data/records.csv from the public NTSB Pre2008.mdb
python -m pytest -q tests
python scripts/run_experiment.py   # writes outputs/results.json
```

## Measured results (27,443 NTSB records, 1974-2007; alpha = 0.05)
| split | field | false claims accepted | true claims accepted | contradicted flags on false claims |
|---|---|---|---|---|
| random 60/20/20 (3 seeds) | injury | 0.050 | 0.976 | 0.84 |
| | weather | 0.048 | 0.985 | 0.88 |
| | light | 0.053 | 0.938 | 0.75 |
| | midair | 0.053 | 1.000 | 0.99 |
| temporal (train <=1994, test >=2000) | injury | 0.056 | 0.911 | 0.63 |
| | weather | 0.047 | 0.969 | 0.81 |
| | light | 0.041 | 0.878 | 0.58 |
| | midair | 0.059 | 1.000 | 0.99 |

Full numbers: `outputs/results.json`.

## Limits
- Claims are **constructed** from NTSB structured fields (true) and value-swapped copies (false). No language model was run and no real AI summaries were audited.
- Four simple fields only; mid-air is almost trivially detectable from the text.
- US, mostly general-aviation records up to 2007; narratives are short.
- The false-accept guarantee is marginal and holds under exchangeability; the temporal split shows deviations of about one percentage point and lower true-accept rates.
