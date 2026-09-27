import pytest
import sys
sys.path.insert(0, '..')

from noise.noise_models import bit_flip_noise, phase_flip_noise, depolarizing_noise, amplitude_damping_noise, readout_error_noise
from bb84.bb84 import run_bb84, prepare_qubit, sift_key, calculate_qber, generate_alice_data
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import numpy as np


def test_bit_flip_qber():
    """Bit-flip noise on |0> gives P(1)=p."""
    model = bit_flip_noise(0.1)
    sim = AerSimulator(noise_model=model)
    qc = QuantumCircuit(1, 1)
    qc.id(0)
    qc.measure(0, 0)
    counts = sim.run(qc, shots=10000).result().get_counts()
    p1 = counts.get("1", 0) / 10000
    assert abs(p1 - 0.1) < 0.02, f"Expected p1~0.1, got {p1}"


def test_phase_flip_qber():
    """Phase-flip on |+> gives P(|->)=p."""
    model = phase_flip_noise(0.1)
    sim = AerSimulator(noise_model=model)
    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.id(0)
    qc.h(0)
    qc.measure(0, 0)
    counts = sim.run(qc, shots=10000).result().get_counts()
    p1 = counts.get("1", 0) / 10000
    assert abs(p1 - 0.1) < 0.02, f"Expected p~0.1, got {p1}"


def test_depolarizing_qber():
    """Depolarizing gives P(1)=p/2 for |0>."""
    model = depolarizing_noise(0.3)
    sim = AerSimulator(noise_model=model)
    qc = QuantumCircuit(1, 1)
    qc.id(0)
    qc.measure(0, 0)
    counts = sim.run(qc, shots=10000).result().get_counts()
    p1 = counts.get("1", 0) / 10000
    assert abs(p1 - 0.15) < 0.02, f"Expected p/2=0.15, got {p1}"


def test_readout_error():
    """Readout error adds X with prob p_readerr on measurement."""
    model = readout_error_noise(0.1)
    sim = AerSimulator(noise_model=model)
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)
    counts = sim.run(qc, shots=10000).result().get_counts()
    p1 = counts.get("1", 0) / 10000
    assert abs(p1 - 0.1) < 0.02, f"Expected p_readerr=0.1, got {p1}"


def test_bit_flip_qber_bb84():
    """Full BB84 with bit-flip noise: QBER should be close to p."""
    result = run_bb84(500, bit_flip_noise(0.1))
    assert 0.03 < result["qber"] < 0.17, f"QBER {result['qber']} not in expected range"


def test_phase_flip_qber_bb84():
    """Full BB84 with phase-flip noise: QBER should be close to p/2."""
    result = run_bb84(500, phase_flip_noise(0.1))
    assert 0.03 < result["qber"] < 0.08, f"QBER {result['qber']} not in expected range"


def test_amplitude_damping_qber_bb84():
    """Full BB84 with amplitude damping: QBER ~ gamma/2."""
    result = run_bb84(500, amplitude_damping_noise(0.2))
    assert 0.05 < result["qber"] < 0.15, f"QBER {result['qber']} not in expected range"


def test_depolarizing_qber_bb84():
    """Full BB84 with depolarizing noise: QBER ~ p/3."""
    result = run_bb84(500, depolarizing_noise(0.15))
    assert 0.03 < result["qber"] < 0.15, f"QBER {result['qber']} not in expected range"


def test_readout_error_qber_bb84():
    """Full BB84 with readout error: QBER ~ p_readerr."""
    result = run_bb84(500, readout_error_noise(0.1))
    assert 0.05 < result["qber"] < 0.20, f"QBER {result['qber']} not in expected range"


def test_sift_key():
    """Sifting keeps only matching bases."""
    alice_bits = [0, 1, 0, 1]
    alice_bases = ["Z", "X", "Z", "X"]
    bob_bases = ["Z", "X", "X", "Z"]
    bob_bits = [0, 1, 0, 1]
    key_a, key_b = sift_key(alice_bits, alice_bases, bob_bases, bob_bits)
    assert key_a == [0, 1]
    assert key_b == [0, 1]


def test_calculate_qber():
    """QBER = mismatches / total."""
    assert calculate_qber([0, 1, 0, 1], [0, 0, 0, 1]) == 0.25
    assert calculate_qber([], []) == 0.0


def test_generate_alice_data():
    """Alice generates valid bits and bases."""
    bits, bases = generate_alice_data(100)
    assert len(bits) == 100
    assert len(bases) == 100
    assert all(b in (0, 1) for b in bits)
    assert all(ba in ("Z", "X") for ba in bases)


def test_prepare_qubit():
    """Prepare qubit produces valid circuit."""
    qc = prepare_qubit(0, "Z")
    assert isinstance(qc, QuantumCircuit)
    qc2 = prepare_qubit(1, "X")
    assert isinstance(qc2, QuantumCircuit)


def test_invalid_noise_prob():
    """Noise probabilities must be in [0,1]."""
    with pytest.raises(ValueError):
        bit_flip_noise(1.5)
    with pytest.raises(ValueError):
        phase_flip_noise(-0.1)


def test_invalid_amplitude_damping():
    """Gamma must be in [0,1]."""
    with pytest.raises(ValueError):
        amplitude_damping_noise(1.5)


def test_invalid_readout():
    """Readout error must be in [0,0.5]."""
    with pytest.raises(ValueError):
        readout_error_noise(0.6)
