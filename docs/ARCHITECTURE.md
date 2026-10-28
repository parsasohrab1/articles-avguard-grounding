# Architecture
source narrative + AI summary -> `claims` (field-level claims) -> `verifier` (TF-IDF + logistic regression per field, trained on past narratives) -> support score ->
`conformal.false_accept_threshold` (calibration false claims) -> `workflow.route` -> auto-accept | human review | flagged -> JSONL audit trail.
- `scripts/prepare_data.py` builds data/records.csv from the public NTSB database; `scripts/run_experiment.py` evaluates (random and temporal split).
- Claims in the evaluation are built from the database's structured fields (true) and by replacing the value with a different one (false); no language model was run.
- See `workflow/grounding_audit.yaml` for the operating procedure.
