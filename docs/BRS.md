# Business Requirements Specification (BRS)

**Product:** AvGuard-Ground (articles-avguard-grounding)
*Written from the README, `docs/SRS.md` and the measured results of this repository. Not reviewed by the owner. A patent attorney must review before publication of method details.*

## 1. Business problem
Investigators and maintenance engineers begin to use AI-written summaries of occurrence reports. A fluent summary can state a wrong value, drop a negation or invent a fact, and a reader cannot see it without re-reading the source narrative.

## 2. Business objectives
| ID | Objective |
|----|-----------|
| BO-1 | Check each claim of a summary against the source narrative and route it: auto-accept, human review, or flag as contradicted |
| BO-2 | Cap the share of false claims that are accepted at a stated level (alpha) by conformal calibration |
| BO-3 | Keep an audit trail of every decision |
| BO-4 | Report the result separately for a random split and a temporal split, so that drift is visible |
| BO-5 | Run on site, with no narrative leaving the operator |

## 3. Users (from the SRS)
Accident investigators, airline safety departments, MRO quality engineers; regulators who read AI summaries.

## 4. Scope
In scope: field-level claims (injury level, weather, light, mid-air collision), a text model that re-derives each value, a one-sided conformal threshold, routing, a JSONL audit trail, reproduction from the public NTSB pre-2008 release.
Out of scope: replacing the investigator, causal conclusions, certification credit, real language-model summaries, other fields and languages.

## 5. Constraints and assumptions
- Claims are constructed from NTSB structured fields (true) and value-swapped copies (false); no language model was run and no real AI summary was audited (README, Limits).
- US, mostly general-aviation records up to 2007; the guarantee is marginal and holds under exchangeability.
- Maturity: component validated on constructed claims; no operational claim.

## 6. Success measures (to be measured on real summaries)
False-accept rate within alpha + 0.01 on the random split for every field (SRS acceptance criterion); true-accept and contradiction-flag rates on summaries written by language models; agreement with human reviewers.
