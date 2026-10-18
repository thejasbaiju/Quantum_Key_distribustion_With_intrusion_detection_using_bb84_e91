"""Statistical intrusion detection and QKD security metrics."""

from .key_rate import binary_entropy, secret_key_fraction
from .probability import simulate_detection_probability, theoretical_detection_probability
from .basis_diagnostic import diagnose_basis_errors
from .statistical import (
    ABORT,
    INCONCLUSIVE,
    SECURE,
    bb84_statistical_test,
    e91_statistical_test,
    sample_check_bits,
)

__all__ = [
    "ABORT",
    "INCONCLUSIVE",
    "SECURE",
    "bb84_statistical_test",
    "binary_entropy",
    "diagnose_basis_errors",
    "e91_statistical_test",
    "sample_check_bits",
    "simulate_detection_probability",
    "secret_key_fraction",
    "theoretical_detection_probability",
]
