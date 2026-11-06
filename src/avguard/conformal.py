"""Cutoff on support scores. The rule is implemented here and is not described in the docs."""

import numpy as np


def false_accept_threshold(false_scores, alpha):
    s = np.sort(false_scores)
    n = len(s)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    if k > n:
        return np.inf
    return s[k - 1]


def rates(true_scores, false_scores, t):
    return dict(
        false_accept=float(np.mean(false_scores > t)), true_accept=float(np.mean(true_scores > t))
    )
