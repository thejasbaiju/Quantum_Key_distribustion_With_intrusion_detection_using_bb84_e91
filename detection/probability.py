"""BB84 intercept-resend detection-probability utilities."""

import random


def theoretical_detection_probability(check_bits):
    """Full intercept-resend: each disclosed sifted bit catches Eve with p=1/4."""

    if not isinstance(check_bits, int) or isinstance(check_bits, bool) or check_bits < 0:
        raise ValueError("check_bits must be a non-negative integer")
    return 1 - (3 / 4) ** check_bits


def simulate_detection_probability(check_bits, trials=10000, seed=1234):
    """Monte Carlo estimate of observing at least one error in the check bits."""

    if not isinstance(trials, int) or isinstance(trials, bool) or trials <= 0:
        raise ValueError("trials must be a positive integer")
    theoretical_detection_probability(check_bits)  # validates check_bits
    rng = random.Random(seed)
    detected = sum(
        any(rng.random() < 0.25 for _ in range(check_bits))
        for _ in range(trials)
    )
    return detected / trials
