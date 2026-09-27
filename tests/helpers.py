import math


def assert_qber_near(result, expected, sigmas=3):
    """
    Assert QBER is within `sigmas` binomial standard deviations of `expected`,
    using the sifted key length the run actually produced.
    """
    n = len(result["alice_key"])
    assert n > 0, "Empty sifted key"
    tol = sigmas * math.sqrt(expected * (1 - expected) / n)
    assert abs(result["qber"] - expected) <= tol, (
        f"QBER {result['qber']:.4f} not within {sigmas}σ (±{tol:.4f}) "
        f"of {expected:.4f} (sifted bits = {n})"
    )
