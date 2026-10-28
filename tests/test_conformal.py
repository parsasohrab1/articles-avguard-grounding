import numpy as np
from avguard.conformal import false_accept_threshold, rates


def test_false_accept_controlled():
    rng = np.random.default_rng(0)
    cal, test = rng.random(3000), rng.random(20000)
    t = false_accept_threshold(cal, 0.05)
    assert rates(rng.random(10) + 1, test, t)["false_accept"] <= 0.06
