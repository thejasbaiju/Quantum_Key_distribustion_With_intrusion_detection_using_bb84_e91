"""Asymptotic BB84 secret-key fraction utilities."""

import math


def binary_entropy(qber):
    """Return binary entropy h2(q) for 0 <= q <= 1."""

    if not 0 <= qber <= 1:
        raise ValueError("qber must be between 0 and 1")
    if qber in (0, 1):
        return 0.0
    return -qber * math.log2(qber) - (1 - qber) * math.log2(1 - qber)


def secret_key_fraction(qber):
    """Return the asymptotic BB84 fraction max(0, 1 - 2*h2(Q))."""

    if not 0 <= qber <= 0.5:
        raise ValueError("BB84 qber must be between 0 and 0.5")
    return max(0.0, 1 - 2 * binary_entropy(qber))
