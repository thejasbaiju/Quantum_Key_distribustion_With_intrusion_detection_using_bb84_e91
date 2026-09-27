from qiskit_aer.noise import NoiseModel, pauli_error, depolarizing_error, amplitude_damping_error, thermal_relaxation_error
import numpy as np


def bit_flip_noise(p):
    """
    Create a bit-flip channel with probability p.
    """

    if not 0 <= p <= 1:
        raise ValueError(
            "Noise probability must be between 0 and 1."
        )

    noise_model = NoiseModel()

    error = pauli_error([
        ("X", p),
        ("I", 1 - p)
    ])

    noise_model.add_all_qubit_quantum_error(
        error,
        ["id"]
    )

    return noise_model


def phase_flip_noise(p):
    """
    Create a phase-flip (Z) channel with probability p.
    """

    if not 0 <= p <= 1:
        raise ValueError(
            "Noise probability must be between 0 and 1."
        )

    noise_model = NoiseModel()

    error = pauli_error([
        ("Z", p),
        ("I", 1 - p)
    ])

    noise_model.add_all_qubit_quantum_error(
        error,
        ["id"]
    )

    return noise_model


def depolarizing_noise(p):
    """
    Create a depolarizing channel with probability p.
    """

    if not 0 <= p <= 1:
        raise ValueError(
            "Noise probability must be between 0 and 1."
        )

    noise_model = NoiseModel()

    error = depolarizing_error(p, 1)

    noise_model.add_all_qubit_quantum_error(
        error,
        ["id"]
    )

    return noise_model


def amplitude_damping_noise(gamma):
    """
    Create an amplitude damping channel with parameter gamma.
    """

    if not 0 <= gamma <= 1:
        raise ValueError(
            "Damping parameter must be between 0 and 1."
        )

    noise_model = NoiseModel()

    error = amplitude_damping_error(gamma)

    noise_model.add_all_qubit_quantum_error(
        error,
        ["id"]
    )

    return noise_model


def readout_error_noise(p_readerr):
    """
    Create a readout error model with symmetric bit-flip probability.
    """

    if not 0 <= p_readerr <= 0.5:
        raise ValueError(
            "Readout error probability must be between 0 and 0.5."
        )

    noise_model = NoiseModel()

    # Readout error: confusion matrix
    # P(0|1) = P(1|0) = p_readerr
    error = pauli_error([
        ("X", p_readerr),
        ("I", 1 - p_readerr)
    ])

    noise_model.add_all_qubit_quantum_error(
        error,
        ["measure"]
    )

    return noise_model


def combined_bit_phase_flip(p_bit, p_phase):
    """
    Combine bit-flip and phase-flip noise.
    """

    noise_model = NoiseModel()

    bit_error = pauli_error([
        ("X", p_bit),
        ("I", 1 - p_bit)
    ])
    phase_error = pauli_error([
        ("Z", p_phase),
        ("I", 1 - p_phase)
    ])

    noise_model.add_all_qubit_quantum_error(bit_error, ["id"])
    noise_model.add_all_qubit_quantum_error(phase_error, ["id"])

    return noise_model


def get_noise_model(noise_type, param):
    """
    Factory function to get a noise model by type.
    
    noise_type: 'bit_flip', 'phase_flip', 'depolarizing', 'amplitude_damping', 'readout_error'
    param: the noise parameter (p, gamma, etc.)
    """
    factories = {
        "bit_flip": bit_flip_noise,
        "phase_flip": phase_flip_noise,
        "depolarizing": depolarizing_noise,
        "amplitude_damping": amplitude_damping_noise,
        "readout_error": readout_error_noise,
    }

    if noise_type not in factories:
        raise ValueError(
            f"Unknown noise type: {noise_type}. "
            f"Choose from {list(factories.keys())}"
        )

    return factories[noise_type](param)