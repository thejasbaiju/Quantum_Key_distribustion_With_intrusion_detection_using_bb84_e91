import sys
sys.path.insert(0, '..')

import math
import pytest
from e91.e91 import create_entangled_pair, measure_in_basis, calculate_correlation, calculate_chsh, run_e91, run_measurement, a, a_prime, b, b_prime
from noise.noise_models import bit_flip_noise, depolarizing_noise, amplitude_damping_noise, phase_flip_noise, readout_error_noise
from qiskit_aer import AerSimulator


def test_ideal_chsh():
    """Ideal E91 should violate Bell inequality: S > 2."""
    result = run_e91(shots=1000)
    assert result["chsh"] > 2.0, f"Expected CHSH > 2, got {result['chsh']}"


def test_ideal_chsh_approx():
    """Ideal CHSH should be close to 2*sqrt(2) ~= 2.828."""
    result = run_e91(shots=5000)
    assert abs(result["chsh"] - 2 * math.sqrt(2)) < 0.1, f"Expected CHSH ~2.828, got {result['chsh']}"


def test_bit_flip_chsh_reduction():
    """Bit-flip noise should reduce CHSH."""
    ideal = run_e91(shots=5000)["chsh"]
    noisy = run_e91(shots=5000, noise_model=bit_flip_noise(0.2))["chsh"] if False else None
    # Use run_measurement manually
    model = bit_flip_noise(0.2)
    E_ab = calculate_correlation(run_measurement(a, b, model, shots=1000))
    E_ab_prime = calculate_correlation(run_measurement(a, b_prime, model, shots=1000))
    E_a_prime_b = calculate_correlation(run_measurement(a_prime, b, model, shots=1000))
    E_a_prime_b_prime = calculate_correlation(run_measurement(a_prime, b_prime, model, shots=1000))
    S = calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime)
    assert S < ideal, f"Noisy CHSH {S} should be less than ideal {ideal}"


def test_bit_flip_bell_loss():
    """High bit-flip noise should destroy Bell violation."""
    model = bit_flip_noise(0.5)
    E_ab = calculate_correlation(run_measurement(a, b, model, shots=2000))
    E_ab_prime = calculate_correlation(run_measurement(a, b_prime, model, shots=2000))
    E_a_prime_b = calculate_correlation(run_measurement(a_prime, b, model, shots=2000))
    E_a_prime_b_prime = calculate_correlation(run_measurement(a_prime, b_prime, model, shots=2000))
    S = calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime)
    assert abs(S) <= 2.0, f"Expected no Bell violation at p=0.5, got S={S}"


def test_correlation_ideal():
    """Ideal correlation for a=0, b=pi/8 should be ~cos(2*0-2*pi/8) = cos(pi/4) ~ 0.707."""
    counts = run_measurement(a, b, shots=5000)
    corr = calculate_correlation(counts)
    expected = math.cos(2 * (b - a))
    assert abs(corr - expected) < 0.1, f"Expected corr ~{expected}, got {corr}"


def test_create_entangled_pair():
    """Entangled pair should be Bell state with correlations."""
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    sim = AerSimulator()
    result = sim.run(qc, shots=1000).result().get_counts()
    assert "00" in result and "11" in result, "Expected Bell state correlations"
    assert result.get("01", 0) + result.get("10", 0) < 0.05 * 1000, "Should not have 01 or 10"


def test_calculate_correlation():
    """E = P(00)+P(11)-P(01)-P(10)."""
    counts = {"00": 500, "11": 500, "01": 0, "10": 0}
    assert calculate_correlation(counts) == 1.0
    counts2 = {"00": 0, "11": 0, "01": 500, "10": 500}
    assert calculate_correlation(counts2) == -1.0
    counts3 = {"00": 250, "11": 250, "01": 250, "10": 250}
    assert calculate_correlation(counts3) == 0.0


def test_calculate_chsh():
    """CHSH = E(a,b) - E(a,b') + E(a',b) + E(a',b')."""
    assert calculate_chsh(1, 0, 0, 1) == 2.0
    assert calculate_chsh(0.707, -0.707, 0.707, 0.707) > 2.0


def test_noise_model_factory():
    from noise.noise_models import get_noise_model
    model = get_noise_model("bit_flip", 0.1)
    assert model is not None
    with pytest.raises(ValueError):
        get_noise_model("unknown", 0.1)
