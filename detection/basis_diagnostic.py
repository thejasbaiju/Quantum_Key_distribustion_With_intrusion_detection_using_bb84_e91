"""Diagnostic classification from BB84 Z- and X-basis error patterns.

This module is deliberately diagnostic only.  QKD security must continue to
attribute unexplained errors to an adversary, even when their pattern resembles
a physical noise channel.
"""

import math


LOW_DISTURBANCE = "LOW_DISTURBANCE"
BIT_FLIP_LIKE = "BIT_FLIP_LIKE"
PHASE_FLIP_LIKE = "PHASE_FLIP_LIKE"
SYMMETRIC_OR_UNRESOLVED = "SYMMETRIC_OR_UNRESOLVED"


def _basis_statistics(alice_bits, bob_bits, bases, basis, alpha):
    pairs = [(a, b) for a, b, used_basis in zip(alice_bits, bob_bits, bases) if used_basis == basis]
    if not pairs:
        return {"bits": 0, "errors": 0, "qber": None, "lower_bound": 0.0, "upper_bound": 1.0, "radius": 1.0}

    errors = sum(a != b for a, b in pairs)
    qber = errors / len(pairs)
    # Split alpha across the Z and X bounds.
    radius = math.sqrt(math.log(2 / alpha) / (2 * len(pairs)))
    return {
        "bits": len(pairs),
        "errors": errors,
        "qber": qber,
        "lower_bound": max(0.0, qber - radius),
        "upper_bound": min(1.0, qber + radius),
        "radius": radius,
    }


def diagnose_basis_errors(alice_bits, bob_bits, bases, alpha=0.05, security_threshold=0.11):
    """Classify the measured basis asymmetry without making a security claim."""

    if not (len(alice_bits) == len(bob_bits) == len(bases)):
        raise ValueError("Alice bits, Bob bits and bases must have the same length")
    if not alice_bits:
        raise ValueError("at least one checked bit is required")
    if any(basis not in ("Z", "X") for basis in bases):
        raise ValueError("bases must contain only 'Z' and 'X'")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be strictly between 0 and 1")
    if not 0 < security_threshold < 1:
        raise ValueError("security_threshold must be strictly between 0 and 1")

    z = _basis_statistics(alice_bits, bob_bits, bases, "Z", alpha)
    x = _basis_statistics(alice_bits, bob_bits, bases, "X", alpha)

    if z["bits"] == 0 or x["bits"] == 0:
        classification = SYMMETRIC_OR_UNRESOLVED
        explanation = "both bases need checked bits before their error patterns can be compared"
    elif z["qber"] - x["qber"] > z["radius"] + x["radius"]:
        classification = BIT_FLIP_LIKE
        explanation = "Z-basis errors are significantly higher than X-basis errors"
    elif x["qber"] - z["qber"] > z["radius"] + x["radius"]:
        classification = PHASE_FLIP_LIKE
        explanation = "X-basis errors are significantly higher than Z-basis errors"
    elif z["upper_bound"] < security_threshold and x["upper_bound"] < security_threshold:
        classification = LOW_DISTURBANCE
        explanation = "both basis-specific upper bounds are below the security threshold"
    else:
        classification = SYMMETRIC_OR_UNRESOLVED
        explanation = "the bases are statistically similar or the sample is too small to separate them"

    return {
        "classification": classification,
        "explanation": explanation,
        "z_basis": z,
        "x_basis": x,
        "alpha": alpha,
        "confidence": 1 - alpha,
        "security_note": "Diagnostic only: all unexplained errors must still be treated as potentially adversarial.",
    }
