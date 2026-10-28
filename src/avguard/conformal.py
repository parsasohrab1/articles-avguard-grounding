"""One-sided split-conformal threshold on FALSE claims: accept a claim only if its support score >= t, where t is chosen so that
P(false claim accepted) <= alpha for a new false claim exchangeable with the calibration false claims."""
import numpy as np


def false_accept_threshold(false_scores, alpha):
    s = np.sort(false_scores); n = len(s)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return np.inf if k > n else s[k - 1]      # accept if score > t (strict), so k-th largest of n+1 bounds the rate


def rates(true_scores, false_scores, t):
    return dict(false_accept=float(np.mean(false_scores > t)), true_accept=float(np.mean(true_scores > t)))
