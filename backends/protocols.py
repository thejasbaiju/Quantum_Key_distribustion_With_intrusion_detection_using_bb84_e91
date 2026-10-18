import math
import random
from collections import Counter, defaultdict

from bb84.bb84 import generate_alice_data, prepare_qubit, sift_key, calculate_qber
from e91.e91 import create_entangled_pair, measure_in_basis, calculate_correlation, calculate_chsh, a, a_prime, b, b_prime
from experiments.eve_attack import _e91_eve_intercept_circuit, _e91_counts_to_ab


CHSH_SETTINGS = [(a, b), (a, b_prime), (a_prime, b), (a_prime, b_prime)]
EVE_ANGLES = [a, a_prime, b, b_prime]


def _measurement_circuit(bit, prep_basis, meas_basis, channel):
    """Prepare one BB84 state and measure it in meas_basis."""

    qc = prepare_qubit(bit, prep_basis)

    # Quantum channel: the repo's Aer noise models attach to 'id'
    # (device transpilers drop it; real devices supply their own noise)
    if channel:
        qc.id(0)

    if meas_basis == "X":
        qc.h(0)

    qc.measure(0, 0)

    return qc


def measure_batched(preps, meas_bases, runner, channel=True):
    """
    Measure many single-qubit rounds in one job.

    preps: list of (bit, basis) states to prepare; meas_bases: one basis per round.
    Only 8 distinct circuits exist (bit x prep basis x meas basis), so each runs
    once with shots = number of rounds using it, and the per-shot outcomes are
    handed back to those rounds. Shots are independent, so this is equivalent to
    running every round as its own circuit.
    """

    groups = defaultdict(list)
    for i, ((bit, basis), meas_basis) in enumerate(zip(preps, meas_bases)):
        groups[(bit, basis, meas_basis)].append(i)

    if not groups:
        return []

    keys = list(groups)
    circuits = [_measurement_circuit(*key, channel=channel) for key in keys]
    shots = [len(groups[key]) for key in keys]

    outcomes = [None] * len(preps)
    for key, bitstrings in zip(keys, runner.sample(circuits, shots)):
        for i, bitstring in zip(groups[key], bitstrings):
            outcomes[i] = int(bitstring)

    return outcomes


def run_bb84_batched(n, runner, eve_prob=0.0):
    """
    BB84 with optional intercept-resend, in at most two jobs (Eve, then Bob).

    Eve measures each intercepted qubit in a random basis straight after Alice
    and resends the state she observed, as in experiments.eve_attack.
    """

    alice_bits, alice_bases = generate_alice_data(n)
    bob_bases = [random.choice(["Z", "X"]) for _ in range(n)]
    preps = list(zip(alice_bits, alice_bases))

    intercepted = [i for i in range(n) if random.random() < eve_prob]
    if intercepted:
        eve_bases = [random.choice(["Z", "X"]) for _ in intercepted]
        eve_bits = measure_batched(
            [preps[i] for i in intercepted],
            eve_bases,
            runner,
            channel=False
        )
        for i, eve_bit, eve_basis in zip(intercepted, eve_bits, eve_bases):
            preps[i] = (eve_bit, eve_basis)

    bob_bits = measure_batched(preps, bob_bases, runner)

    alice_key, bob_key = sift_key(alice_bits, alice_bases, bob_bases, bob_bits)

    return {
        "alice_key": alice_key,
        "bob_key": bob_key,
        "qber": calculate_qber(alice_key, bob_key),
        "key_length": len(alice_key),
        "intercepted": len(intercepted),
    }


def _e91_circuit(alice_angle, bob_angle):
    qc = create_entangled_pair()
    measure_in_basis(qc, 0, alice_angle)
    measure_in_basis(qc, 1, bob_angle)
    qc.measure_all()
    return qc


def run_e91_batched(shots, runner, eve_prob=0.0):
    """
    CHSH test for E91 in one job.

    For each of the four settings, a fraction eve_prob of the shots run Eve's
    intercept-resend circuit, split evenly over her four angles (as in
    experiments.eve_attack.eve_intercept_resend_e91); the rest are clean.
    """

    n_eve = int(round(shots * eve_prob))
    n_clean = shots - n_eve

    circuits, shot_counts, owners = [], [], []
    for setting, (alice_angle, bob_angle) in enumerate(CHSH_SETTINGS):
        if n_clean > 0:
            circuits.append(_e91_circuit(alice_angle, bob_angle))
            shot_counts.append(n_clean)
            owners.append((setting, False))

        for i, eve_angle in enumerate(EVE_ANGLES):
            n = n_eve // 4 + (1 if i < n_eve % 4 else 0)
            if n > 0:
                circuits.append(_e91_eve_intercept_circuit(alice_angle, bob_angle, eve_angle))
                shot_counts.append(n)
                owners.append((setting, True))

    counts = [Counter() for _ in CHSH_SETTINGS]
    for (setting, is_eve), bitstrings in zip(owners, runner.sample(circuits, shot_counts)):
        raw = Counter(bitstrings)
        counts[setting].update(_e91_counts_to_ab(raw) if is_eve else raw)

    E = [calculate_correlation(c) for c in counts]
    S = calculate_chsh(*E)

    return {
        "E_ab": E[0],
        "E_ab_prime": E[1],
        "E_a_prime_b": E[2],
        "E_a_prime_b_prime": E[3],
        "chsh": S,
        "bell_violation": abs(S) > 2,
    }


def ideal_bb84_qber(eve_prob):
    """Noise-free intercept-resend QBER: Eve errs on half her guesses, Bob on half of those."""
    return eve_prob / 4


def ideal_e91_chsh(eve_prob):
    """Noise-free CHSH: clean shots give 2*sqrt(2), intercepted shots sqrt(2)."""
    return (1 - eve_prob) * 2 * math.sqrt(2) + eve_prob * math.sqrt(2)
