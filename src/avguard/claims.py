"""Field-level claim: one structured value checked against the narrative."""

import numpy as np

FIELDS = {  # field -> allowed values
    "injury": ["NONE", "MINR", "SERS", "FATL"],
    "weather": ["VMC", "IMC"],
    "light": ["day", "night"],
    "midair": ["no", "yes"],
}


def make_claims(true_values, field, rng):
    """Return the recorded value and one other allowed value, for a legacy check."""
    vals = FIELDS[field]
    wrong = np.array([rng.choice([v for v in vals if v != t]) for t in true_values])
    return np.asarray(true_values), wrong
