import math

from e91.e91 import run_e91
from experiments.eve_attack import eve_intercept_resend_bb84, eve_intercept_resend_e91
from noise.noise_models import bit_flip_noise

from tests.helpers import assert_qber_near


def test_bb84_no_eve_no_noise():
    """Without Eve or noise, Alice's and Bob's sifted keys match exactly."""
    result = eve_intercept_resend_bb84(500, 0.0)
    assert result["qber"] == 0.0


def test_bb84_full_intercept_qber():
    """Full intercept-resend: Eve picks the wrong basis half the time, Bob errs half of those -> QBER = 1/4."""
    result = eve_intercept_resend_bb84(1000, 1.0)
    assert_qber_near(result, 0.25)


def test_bb84_half_intercept_qber():
    """Intercepting a fraction f of qubits gives QBER = f/4."""
    result = eve_intercept_resend_bb84(1000, 0.5)
    assert_qber_near(result, 0.125)


def test_bb84_eve_attack_applies_channel_noise():
    """
    Regression: noise_model must act on Bob's channel (it was silently ignored,
    giving QBER = 0). Bit-flip p only affects Z-basis bits, so QBER = p/2.
    """
    result = eve_intercept_resend_bb84(1000, 0.0, noise_model=bit_flip_noise(0.1))
    assert_qber_near(result, 0.05)
    assert result["qber"] > 0


def test_e91_clean_chsh():
    """Clean channel reaches Tsirelson's bound S = 2*sqrt(2)."""
    S = run_e91(shots=20000)["chsh"]
    assert abs(S - 2 * math.sqrt(2)) < 0.05, f"Expected S ~ 2.828, got {S}"


def test_e91_eve_zero_matches_clean():
    """The Eve-attack path with probability 0 is the clean experiment."""
    result = eve_intercept_resend_e91(0.0, shots=2000)
    assert abs(result["chsh"] - 2 * math.sqrt(2)) < 0.05, f"Expected S ~ 2.828, got {result['chsh']}"
    assert result["bell_violation"]


def test_e91_full_intercept_chsh():
    """
    Full intercept on Bob's qubit breaks entanglement. Averaged over Eve's four
    angles, E(x,y) = <cos2(x-e) cos2(y-e)> which gives S = sqrt(2) exactly.
    """
    result = eve_intercept_resend_e91(1.0, shots=2000)
    assert abs(result["chsh"] - math.sqrt(2)) < 0.1, f"Expected S ~ 1.414, got {result['chsh']}"
    assert not result["bell_violation"]
