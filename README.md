# AvGuard-Ground (articles-avguard-grounding)

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

Corpus: 27443 NTSB pre-2008 records, years 1974–2007. Language model `Qwen/Qwen2.5-0.5B-Instruct` on a random sample of 200 narratives (seed 0). Narratives sent to the model were cut at 3000 characters; 66 sample rows were longer than that. Reply digest `b743d137dd01`.

Of 800 field slots, 669 were answered and 131 were abstentions. Among answered claims, 350 matched and 319 did not (52.3% matched).

| field | slots | answered | matched | mismatched | abstained | match rate among answered |
|---|---:|---:|---:|---:|---:|---:|
| injury | 200 | 197 | 115 | 82 | 3 | 58.4% |
| weather | 200 | 187 | 149 | 38 | 13 | 79.7% |
| light | 200 | 88 | 74 | 14 | 112 | 84.1% |
| midair | 200 | 197 | 12 | 185 | 3 | 6.1% |

Support scores use a 60/20/20 split of the same sample (train 120, calibration 40, held-out 40). A cutoff is reported only when the calibration split has at least 20 mismatched claims for that field. Target level for that cutoff: alpha = 0.05.

| field | status | mismatched in calibration | false-accept on held-out | true-accept on held-out | mean score matched | mean score mismatched |
|---|---|---:|---:|---:|---:|---:|
| injury | not_estimated | 16 | n/a | n/a | 0.608 | 0.168 |
| weather | not_estimated | 8 | n/a | n/a | 0.902 | 0.058 |
| light | not_estimated | 2 | n/a | n/a | 0.889 | 0.822 |
| midair | estimated | 38 | 0.0% | 100.0% | 0.991 | 0.009 |

For midair, 0.0% of 37 mismatched held-out claims were above the cutoff, and 100.0% of 3 matched claims were.

Full numbers: `outputs/results.json`, rebuilt by `python scripts/run_experiment.py`.

## Limits

- One model and one sample. The model was not run on the full corpus.
- Four fields only. Abstaining is counted separately from a wrong code.
- The narratives are the public probable-cause text, mostly US general aviation, through 2007, and long ones were cut before the call.
- No investigator labelled the model’s wording. The structured NTSB field is the reference, and it can itself be coarse.
- A cutoff fit on this sample is not an operational guarantee.

## Journal

The Advanced Engineering Informatics special issue on large language models in aviation safety closed on 31 March 2026. This repository does not submit a manuscript. See `docs/JOURNAL_FIT.md` and `docs/TRL.md`.
