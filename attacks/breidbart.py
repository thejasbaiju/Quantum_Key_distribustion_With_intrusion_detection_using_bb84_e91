"""Breidbart-basis intercept-resend attack for BB84."""

import math
import random
from collections import defaultdict

from qiskit import QuantumCircuit

from bb84.bb84 import calculate_qber, generate_alice_data, sift_key


BREIDBART_ANGLE = math.pi / 8
BASIS_ANGLES = {"Z": 0.0, "X": math.pi / 4}


def _angle_measurement_circuit(bit, preparation_angle, measurement_angle, channel):
    qc = QuantumCircuit(1, 1)
    if bit:
        qc.x(0)
    if preparation_angle:
        qc.ry(2 * preparation_angle, 0)
    if channel:
        qc.id(0)
    if measurement_angle:
        qc.ry(-2 * measurement_angle, 0)
    qc.measure(0, 0)
    return qc


def _measure_batched_angles(preparations, measurement_angles, runner, channel=True):
    groups = defaultdict(list)
    for index, ((bit, angle), measurement_angle) in enumerate(zip(preparations, measurement_angles)):
        groups[(bit, angle, measurement_angle)].append(index)

    if not groups:
        return []

    keys = list(groups)
    circuits = [
        _angle_measurement_circuit(bit, prep_angle, meas_angle, channel)
        for bit, prep_angle, meas_angle in keys
    ]
    shots = [len(groups[key]) for key in keys]
    outcomes = [None] * len(preparations)
    for key, bitstrings in zip(keys, runner.sample(circuits, shots)):
        for index, bitstring in zip(groups[key], bitstrings):
            outcomes[index] = int(bitstring)
    return outcomes


def run_breidbart_bb84(n, runner, eve_prob=1.0):
    """Run BB84 with Eve measuring intercepted qubits at pi/8.

    A simple Breidbart measure-and-resend attack gives Eve a bit-error rate of
    sin(pi/8)^2 ~= 14.64%, while a full attack still causes Bob approximately
    25% QBER.  The two quantities must not be confused.
    """

    if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
        raise ValueError("n must be a positive integer")
    if not 0 <= eve_prob <= 1:
        raise ValueError("eve_prob must be between 0 and 1")

    alice_bits, alice_bases = generate_alice_data(n)
    bob_bases = [random.choice(["Z", "X"]) for _ in range(n)]
    preparations = [(bit, BASIS_ANGLES[basis]) for bit, basis in zip(alice_bits, alice_bases)]

    intercepted = [index for index in range(n) if random.random() < eve_prob]
    eve_bits = _measure_batched_angles(
        [preparations[index] for index in intercepted],
        [BREIDBART_ANGLE] * len(intercepted),
        runner,
        channel=False,
    )
    for index, eve_bit in zip(intercepted, eve_bits):
        preparations[index] = (eve_bit, BREIDBART_ANGLE)

    bob_bits = _measure_batched_angles(
        preparations,
        [BASIS_ANGLES[basis] for basis in bob_bases],
        runner,
        channel=True,
    )
    alice_key, bob_key = sift_key(alice_bits, alice_bases, bob_bases, bob_bits)
    sifted_bases = [
        alice_basis
        for alice_basis, bob_basis in zip(alice_bases, bob_bases)
        if alice_basis == bob_basis
    ]
    eve_errors = sum(alice_bits[index] != eve_bit for index, eve_bit in zip(intercepted, eve_bits))

    return {
        "alice_key": alice_key,
        "bob_key": bob_key,
        "sifted_bases": sifted_bases,
        "qber": calculate_qber(alice_key, bob_key),
        "key_length": len(alice_key),
        "intercepted": len(intercepted),
        "eve_bit_error_rate": eve_errors / len(intercepted) if intercepted else None,
        "eve_guess_accuracy": (
            1 - eve_errors / len(intercepted) if intercepted else None
        ),
    }
