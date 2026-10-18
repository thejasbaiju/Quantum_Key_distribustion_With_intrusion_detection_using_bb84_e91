import math

import pytest

from attacks.breidbart import run_breidbart_bb84
from backends.protocols import run_bb84_batched
from backends.runners import get_runner
from detection.basis_diagnostic import (
    BIT_FLIP_LIKE,
    LOW_DISTURBANCE,
    PHASE_FLIP_LIKE,
    SYMMETRIC_OR_UNRESOLVED,
    diagnose_basis_errors,
)
from experiments.partial_interception import ideal_bb84_interception_limit, ideal_e91_interception_limit


def _diagnostic(z_errors, x_errors, bits_per_basis=1000):
    alice = [0] * (2 * bits_per_basis)
    bob = (
        [1] * z_errors
        + [0] * (bits_per_basis - z_errors)
        + [1] * x_errors
        + [0] * (bits_per_basis - x_errors)
    )
    bases = ["Z"] * bits_per_basis + ["X"] * bits_per_basis
    return diagnose_basis_errors(alice, bob, bases)


def test_basis_diagnostic_recognises_clean_data():
    assert _diagnostic(0, 0)["classification"] == LOW_DISTURBANCE


def test_basis_diagnostic_recognises_bit_flip_signature():
    assert _diagnostic(200, 0)["classification"] == BIT_FLIP_LIKE


def test_basis_diagnostic_recognises_phase_flip_signature():
    assert _diagnostic(0, 200)["classification"] == PHASE_FLIP_LIKE


def test_basis_diagnostic_does_not_call_symmetric_errors_eve():
    result = _diagnostic(250, 250)
    assert result["classification"] == SYMMETRIC_OR_UNRESOLVED
    assert "potentially adversarial" in result["security_note"]


def test_batched_bb84_returns_one_basis_per_sifted_bit():
    result = run_bb84_batched(500, get_runner("aer"))
    assert len(result["sifted_bases"]) == result["key_length"]
    assert set(result["sifted_bases"]) <= {"Z", "X"}


def test_full_breidbart_intercept_has_expected_information_disturbance():
    result = run_breidbart_bb84(8000, get_runner("aer"), eve_prob=1.0)
    sifted = result["key_length"]
    qber_tolerance = 4 * math.sqrt(0.25 * 0.75 / sifted)
    eve_expected = math.sin(math.pi / 8) ** 2
    eve_tolerance = 4 * math.sqrt(eve_expected * (1 - eve_expected) / result["intercepted"])
    assert result["qber"] == pytest.approx(0.25, abs=qber_tolerance)
    assert result["eve_bit_error_rate"] == pytest.approx(eve_expected, abs=eve_tolerance)


def test_partial_interception_theoretical_limits():
    assert ideal_bb84_interception_limit() == pytest.approx(0.44)
    assert ideal_e91_interception_limit() == pytest.approx(2 - math.sqrt(2))
