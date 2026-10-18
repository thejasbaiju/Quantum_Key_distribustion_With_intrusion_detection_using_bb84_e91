import math
import random

import pytest

from detection.key_rate import binary_entropy, secret_key_fraction
from detection.probability import simulate_detection_probability, theoretical_detection_probability
from detection.statistical import ABORT, INCONCLUSIVE, SECURE, bb84_statistical_test, e91_statistical_test, sample_check_bits


def test_check_bits_are_removed_without_mutating_inputs():
    alice = [0, 1] * 10
    bob = alice.copy()
    result = sample_check_bits(alice, bob, 6, rng=random.Random(7))

    assert len(result["alice_check"]) == 6
    assert len(result["alice_remaining"]) == 14
    assert len(set(result["check_indices"])) == 6
    assert alice == [0, 1] * 10
    assert bob == alice
    for index, alice_bit, bob_bit in zip(
        result["check_indices"], result["alice_check"], result["bob_check"]
    ):
        assert alice_bit == alice[index]
        assert bob_bit == bob[index]


def test_check_bit_validation():
    with pytest.raises(ValueError):
        sample_check_bits([0], [0, 1], 1)
    with pytest.raises(ValueError):
        sample_check_bits([0], [0], 0)
    with pytest.raises(ValueError):
        sample_check_bits([0], [0], 2)


def test_bb84_clean_sample_is_secure_with_enough_bits():
    result = bb84_statistical_test([0] * 600, [0] * 600, 500)
    assert result["decision"] == SECURE
    assert result["operational_decision"] == SECURE
    assert result["upper_bound"] < 0.11
    assert result["remaining_key_length"] == 100


def test_bb84_disclosing_the_whole_key_cannot_operationally_pass():
    result = bb84_statistical_test([0] * 500, [0] * 500, 500)
    assert result["decision"] == SECURE
    assert result["operational_decision"] == ABORT
    assert result["remaining_key_length"] == 0


def test_bb84_high_qber_aborts():
    alice = [0] * 500
    bob = [1] * 150 + [0] * 350
    result = bb84_statistical_test(alice, bob, 500)
    assert result["decision"] == ABORT
    assert result["lower_bound"] > 0.11


def test_bb84_small_sample_is_inconclusive_and_operationally_aborts():
    result = bb84_statistical_test([0] * 20, [0] * 20, 20)
    assert result["decision"] == INCONCLUSIVE
    assert result["operational_decision"] == ABORT


def test_e91_clean_correlation_is_secure_with_enough_shots():
    c = math.sqrt(0.5)
    result = e91_statistical_test([c, -c, c, c], 10000)
    assert result["decision"] == SECURE
    assert result["lower_bound"] > 2


def test_e91_full_intercept_aborts():
    # Correlations with CHSH = sqrt(2), the repository's full-intercept theory.
    c = math.sqrt(2) / 4
    result = e91_statistical_test([c, -c, c, c], 10000)
    assert result["decision"] == ABORT
    assert result["upper_bound"] <= 2


def test_detection_probability_matches_formula():
    assert theoretical_detection_probability(0) == 0
    assert theoretical_detection_probability(1) == 0.25
    assert theoretical_detection_probability(10) == pytest.approx(1 - (3 / 4) ** 10)
    simulated = simulate_detection_probability(8, trials=50000, seed=9)
    assert simulated == pytest.approx(theoretical_detection_probability(8), abs=0.01)


def test_secret_key_fraction_explains_eleven_percent_threshold():
    assert binary_entropy(0) == 0
    assert secret_key_fraction(0) == 1
    assert secret_key_fraction(0.11) > 0
    assert secret_key_fraction(0.111) == 0
    assert secret_key_fraction(0.5) == 0


def test_security_metric_validation():
    with pytest.raises(ValueError):
        binary_entropy(-0.01)
    with pytest.raises(ValueError):
        secret_key_fraction(0.51)
    with pytest.raises(ValueError):
        theoretical_detection_probability(-1)
    with pytest.raises(ValueError):
        bb84_statistical_test([0], [0], 1, alpha=0)
    with pytest.raises(ValueError):
        e91_statistical_test([0, 0, 0, 0], 100, alpha=1)
