"""Confidence-aware decisions for BB84 and E91 parameter estimation.

The bounds use Hoeffding's inequality.  They are intentionally conservative,
require no fitted distribution, and expose an inconclusive state rather than
silently treating a small sample as secure.
"""

import math
import random
from collections.abc import Sequence


SECURE = "SECURE"
ABORT = "ABORT"
INCONCLUSIVE = "INCONCLUSIVE"


def _validate_probability(value, name):
    if not 0 < value < 1:
        raise ValueError(f"{name} must be strictly between 0 and 1")


def sample_check_bits(alice_key, bob_key, sample_size, rng=None):
    """Reveal a random subset and remove it from the candidate secret key.

    Returns the revealed positions/bits and the undisclosed remainder.  The
    input lists are not mutated.
    """

    if len(alice_key) != len(bob_key):
        raise ValueError("Alice and Bob keys must have the same length")
    if not isinstance(sample_size, int) or isinstance(sample_size, bool):
        raise TypeError("sample_size must be an integer")
    if not 1 <= sample_size <= len(alice_key):
        raise ValueError("sample_size must be between 1 and the sifted key length")

    generator = rng if rng is not None else random
    check_indices = sorted(generator.sample(range(len(alice_key)), sample_size))
    check_set = set(check_indices)

    alice_check = [alice_key[i] for i in check_indices]
    bob_check = [bob_key[i] for i in check_indices]
    alice_remaining = [bit for i, bit in enumerate(alice_key) if i not in check_set]
    bob_remaining = [bit for i, bit in enumerate(bob_key) if i not in check_set]

    return {
        "check_indices": check_indices,
        "alice_check": alice_check,
        "bob_check": bob_check,
        "alice_remaining": alice_remaining,
        "bob_remaining": bob_remaining,
    }


def bb84_statistical_test(
    alice_key,
    bob_key,
    sample_size,
    threshold=0.11,
    alpha=0.01,
    rng=None,
):
    """Estimate BB84 QBER from disclosed check bits and make a decision.

    A one-sided Hoeffding radius is used on each side.  SECURE means the upper
    confidence bound is below ``threshold``; ABORT means the lower bound is
    above it.  Values whose interval crosses the threshold are INCONCLUSIVE
    and must be treated as aborts by an operational system.
    """

    _validate_probability(threshold, "threshold")
    _validate_probability(alpha, "alpha")
    sample = sample_check_bits(alice_key, bob_key, sample_size, rng=rng)

    errors = sum(a != b for a, b in zip(sample["alice_check"], sample["bob_check"]))
    estimate = errors / sample_size
    radius = math.sqrt(math.log(1 / alpha) / (2 * sample_size))
    lower = max(0.0, estimate - radius)
    upper = min(1.0, estimate + radius)

    if upper < threshold:
        decision = SECURE
        reason = "upper confidence bound is below the QBER threshold"
    elif lower > threshold:
        decision = ABORT
        reason = "lower confidence bound is above the QBER threshold"
    else:
        decision = INCONCLUSIVE
        reason = "confidence interval overlaps the QBER threshold"

    remaining_key_length = len(sample["alice_remaining"])
    operational_decision = SECURE if decision == SECURE and remaining_key_length > 0 else ABORT
    if decision == SECURE and remaining_key_length == 0:
        reason += "; however, all sifted bits were disclosed, so no usable key remains"

    return {
        **sample,
        "protocol": "BB84",
        "decision": decision,
        "operational_decision": operational_decision,
        "reason": reason,
        "sample_size": sample_size,
        "errors": errors,
        "qber": estimate,
        "threshold": threshold,
        "alpha": alpha,
        "confidence": 1 - alpha,
        "bound_method": "one-sided Hoeffding",
        "lower_bound": lower,
        "upper_bound": upper,
        "remaining_key_length": remaining_key_length,
    }


def e91_statistical_test(correlations, shots_per_setting, alpha=0.01):
    """Test whether a CHSH violation remains after statistical uncertainty.

    ``correlations`` must be ordered as E(a,b), E(a,b'), E(a',b), E(a',b').
    Each correlation is the mean of outcomes in [-1, 1].  A union bound gives
    simultaneous one-sided Hoeffding bounds across all four settings.
    """

    _validate_probability(alpha, "alpha")
    values = list(correlations)
    if len(values) != 4:
        raise ValueError("exactly four CHSH correlations are required")
    if any(not -1 <= value <= 1 for value in values):
        raise ValueError("correlations must be between -1 and 1")

    if isinstance(shots_per_setting, int) and not isinstance(shots_per_setting, bool):
        shots = [shots_per_setting] * 4
    else:
        shots = list(shots_per_setting)
    if len(shots) != 4 or any(not isinstance(n, int) or isinstance(n, bool) or n <= 0 for n in shots):
        raise ValueError("shots_per_setting must contain four positive integers")

    # The correlation samples lie in [-1, 1] (range length 2).  Allocate the
    # total error probability equally across the four CHSH settings.
    radii = [math.sqrt(2 * math.log(4 / alpha) / n) for n in shots]
    chsh = values[0] - values[1] + values[2] + values[3]
    uncertainty = sum(radii)
    lower = max(0.0, abs(chsh) - uncertainty)
    upper = min(4.0, abs(chsh) + uncertainty)

    if lower > 2:
        decision = SECURE
        reason = "CHSH lower confidence bound exceeds the classical limit"
    elif upper <= 2:
        decision = ABORT
        reason = "CHSH upper confidence bound does not exceed the classical limit"
    else:
        decision = INCONCLUSIVE
        reason = "CHSH confidence interval overlaps the classical limit"

    return {
        "protocol": "E91",
        "decision": decision,
        "operational_decision": SECURE if decision == SECURE else ABORT,
        "reason": reason,
        "correlations": values,
        "shots_per_setting": shots,
        "chsh": chsh,
        "alpha": alpha,
        "confidence": 1 - alpha,
        "bound_method": "simultaneous one-sided Hoeffding",
        "setting_radii": radii,
        "uncertainty": uncertainty,
        "lower_bound": lower,
        "upper_bound": upper,
        "classical_limit": 2.0,
    }
