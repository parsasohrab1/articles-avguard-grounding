# TRL assessment

Level reached: **TRL 3**. A script has been run on a sample of real public narratives with a real language model. That is a proof of concept on public data, not validation in an investigation.

| Level | Status | Evidence |
|---|---|---|
| TRL 1–2 | done | Field values stated by a model are checked against the source record. |
| TRL 3 | reached | Code, tests, and one real model call on 200 of 27443 NTSB records. Among answered claims, 52.3% matched the structured field (350 of 669). |
| TRL 4 | not reached | No investigator-in-the-loop study, and the model was not run on the full corpus. |
| TRL 5+ | not reached | No use on a current investigation and no operational audit trail in an agency system. |

The match rate above is copied from `outputs/results.json` by `scripts/run_experiment.py`. A low or incomplete support-score cutoff is a limit of this sample, not a hidden success. See the README table.
