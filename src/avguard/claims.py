"""Claim model. A claim asserts one value of one structured field about an occurrence; it is checked against the narrative."""
import numpy as np

FIELDS = {          # field -> allowed values
    "injury": ["NONE", "MINR", "SERS", "FATL"],
    "weather": ["VMC", "IMC"],
    "light": ["day", "night"],
    "midair": ["no", "yes"],
}


def make_claims(true_values, field, rng):
    """For every record return (true claim value, perturbed claim value). The perturbed value is a different value drawn at random."""
    vals = FIELDS[field]
    wrong = np.array([rng.choice([v for v in vals if v != t]) for t in true_values])
    return np.asarray(true_values), wrong
