# AvGuard-Ground – Software Requirements (SRS)
1. Purpose: let safety investigators and maintenance engineers use AI-written summaries of occurrences without trusting them blindly: every claim is checked against the source narrative.
2. Users: accident investigators, airline safety departments, MRO quality engineers; regulators reading AI summaries.
3. Inputs: source narrative, structured metadata, AI summary (or claims).
4. Functional requirements
   - FR1 Represent each summary statement as a field-level claim (field, value).
   - FR2 Compute a support score per claim from the source narrative only.
   - FR3 Set the auto-accept threshold by conformal calibration so that the false-accept rate on calibration-like false claims is <= alpha.
   - FR4 Route: auto-accept / human review / flagged as contradicted; log every decision.
   - FR5 Report per-field false-accept and true-accept rates, split by random and temporal test.
5. Non-functional: runs on-premises, no narrative leaves the site; calibration in seconds; full reproducibility from the public NTSB release.
6. Out of scope: replacing the investigator, causal conclusions, certification credit.
7. Acceptance: reproduce outputs/results.json from the saved model replies (`python scripts/run_experiment.py`). Report the match rate of values the model stated. State a false-accept share only when that file marks the field as estimated.
