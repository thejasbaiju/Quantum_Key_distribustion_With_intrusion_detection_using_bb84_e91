import random
import math
import statistics
import pandas as pd
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from bb84.bb84 import generate_alice_data, prepare_qubit, sift_key, calculate_qber
from e91.e91 import create_entangled_pair, measure_in_basis, calculate_correlation, calculate_chsh, a, a_prime, b, b_prime
from noise.noise_models import bit_flip_noise, phase_flip_noise, depolarizing_noise, amplitude_damping_noise, readout_error_noise


def eve_intercept_resend_bb84(n, eve_intercept_prob, noise_model=None, simulator=None):
    """
    Eve performs intercept-resend attack on BB84.
    eve_intercept_prob: probability that Eve intercepts each qubit.
    Eve measures in a random basis and resends.
    """
    if simulator is None:
        simulator = AerSimulator(noise_model=noise_model)

    alice_bits, alice_bases = generate_alice_data(n)
    alice_qubits = [prepare_qubit(bit, basis) for bit, basis in zip(alice_bits, alice_bases)]
    bob_bases = [random.choice(["Z", "X"]) for _ in range(n)]
    bob_bits = []

    for i, (qc, alice_basis) in enumerate(zip(alice_qubits, alice_bases)):
        if random.random() < eve_intercept_prob:
            eve_basis = random.choice(["Z", "X"])
            eve_qc = qc.copy()
            if eve_basis == "X":
                eve_qc.h(0)
            eve_qc.measure(0, 0)
            result = simulator.run(eve_qc, shots=1).result()
            counts = result.get_counts()
            eve_bit = int(list(counts.keys())[0])
            eve_qc = QuantumCircuit(1, 1)
            if eve_bit == 1:
                eve_qc.x(0)
            if eve_basis == "X":
                eve_qc.h(0)
            qc = eve_qc

        bob_qc = qc.copy()
        if bob_bases[i] == "X":
            bob_qc.h(0)
        bob_qc.measure(0, 0)
        result = simulator.run(bob_qc, shots=1).result()
        counts = result.get_counts()
        bob_bit = int(list(counts.keys())[0])
        bob_bits.append(bob_bit)

    alice_key, bob_key = sift_key(alice_bits, alice_bases, bob_bases, bob_bits)
    qber = calculate_qber(alice_key, bob_key)

    return {
        "alice_key": alice_key,
        "bob_key": bob_key,
        "qber": qber,
        "key_length": len(alice_key),
    }


def _e91_eve_intercept_circuit(alice_angle, bob_angle, eve_angle):
    """
    Build a dynamic circuit where Eve intercepts Bob's qubit:
    Bell pair -> Eve measures q1 in eve_angle basis -> reset/resend
    eigenstate -> Alice/Bob measure. Uses if_test (Qiskit >= 1.0).
    Classical registers: a (Alice), b (Bob), e (Eve).
    """
    from qiskit import QuantumRegister, ClassicalRegister
    q = QuantumRegister(2, "q")
    cA = ClassicalRegister(1, "a")
    cB = ClassicalRegister(1, "b")
    cE = ClassicalRegister(1, "e")
    qc = QuantumCircuit(q, cA, cB, cE)
    qc.h(0)
    qc.cx(0, 1)
    qc.id(0)
    qc.id(1)
    # Eve measures Bob's qubit
    qc.ry(-2 * eve_angle, 1)
    qc.measure(1, cE)
    # Resend eigenstate Eve observed
    qc.reset(1)
    with qc.if_test((cE, 1)):
        qc.x(1)
    qc.ry(2 * eve_angle, 1)
    # Alice & Bob measure
    qc.ry(-2 * alice_angle, 0)
    qc.ry(-2 * bob_angle, 1)
    qc.measure(0, cA)
    qc.measure(1, cB)
    return qc


def _e91_counts_to_ab(dynamic_counts):
    """Convert {'e b a': n} counts to {'00','01','10','11'} on (a,b)."""
    ab = {"00": 0, "01": 0, "10": 0, "11": 0}
    for key, n in dynamic_counts.items():
        parts = key.replace("_", " ").split(" ")
        parts = [p for p in parts if p != ""]
        if len(parts) == 3:
            # registers ordered e b a in output string
            e_bit, b_bit, a_bit = parts[0][-1], parts[1][-1], parts[2][-1]
        elif len(parts) == 1 and len(parts[0]) == 3:
            e_bit, b_bit, a_bit = parts[0][0], parts[0][1], parts[0][2]
        else:
            continue
        ab[f"{a_bit}{b_bit}"] += n
    return ab


def _add_counts(d1, d2):
    out = dict(d1)
    for k, v in d2.items():
        out[k] = out.get(k, 0) + v
    return out


def eve_intercept_resend_e91(eve_intercept_prob, noise_model=None, shots=500):
    """
    Eve performs intercept-resend attack on E91 (FIXED model).
    Per shot: with prob (1-p) clean entangled measurement,
    with prob p Eve intercepts Bob's qubit in a random CHSH basis,
    measures it and resends the eigenstate (breaks entanglement).
    """
    simulator = AerSimulator() if noise_model is None else AerSimulator(noise_model=noise_model)
    eve_bases = [a, a_prime, b, b_prime]

    chsh_values = []

    for _ in range(5):
        E_vals = []
        for alice_angle, bob_angle in [(a, b), (a, b_prime), (a_prime, b), (a_prime, b_prime)]:
            n_eve = int(round(shots * eve_intercept_prob))
            n_clean = shots - n_eve
            total = {"00": 0, "01": 0, "10": 0, "11": 0}
            if n_clean > 0:
                total = _add_counts(total, run_measurement_clean(alice_angle, bob_angle, simulator, n_clean))
            if n_eve > 0:
                # split Eve shots evenly over her 4 random bases
                per = n_eve // 4
                rem = n_eve % 4
                for i, e_ang in enumerate(eve_bases):
                    n = per + (1 if i < rem else 0)
                    if n == 0:
                        continue
                    qc = _e91_eve_intercept_circuit(alice_angle, bob_angle, e_ang)
                    raw = simulator.run(qc, shots=n).result().get_counts()
                    total = _add_counts(total, _e91_counts_to_ab(raw))
            E_vals.append(calculate_correlation(total))
        chsh_values.append(calculate_chsh(*E_vals))

    avg_chsh = statistics.mean(chsh_values)
    std_chsh = statistics.pstdev(chsh_values)
    bell_violation = abs(avg_chsh) > 2

    return {
        "chsh": avg_chsh,
        "chsh_std": std_chsh,
        "bell_violation": bell_violation,
    }


def run_measurement_clean(alice_angle, bob_angle, simulator, shots):
    """Clean entangled E91 measurement using a given simulator."""
    from e91.e91 import create_entangled_pair, measure_in_basis
    qc = create_entangled_pair()
    measure_in_basis(qc, 0, alice_angle)
    measure_in_basis(qc, 1, bob_angle)
    qc.measure_all()
    return simulator.run(qc, shots=shots).result().get_counts()


def _e91_with_eve(eve_intercept_prob, alice_angle, bob_angle, noise_model, simulator, shots):
    """Legacy wrapper kept for compatibility; uses the fixed model."""
    res = eve_intercept_resend_e91_single_setting(
        eve_intercept_prob, alice_angle, bob_angle, noise_model, simulator, shots
    )
    return res


def eve_intercept_resend_e91_single_setting(eve_intercept_prob, alice_angle, bob_angle, noise_model, simulator, shots):
    """Counts for one (a,b) setting with Eve attack probability."""
    from e91.e91 import create_entangled_pair, measure_in_basis
    eve_bases = [a, a_prime, b, b_prime]
    n_eve = int(round(shots * eve_intercept_prob))
    n_clean = shots - n_eve
    total = {"00": 0, "01": 0, "10": 0, "11": 0}
    if n_clean > 0:
        qc = create_entangled_pair()
        measure_in_basis(qc, 0, alice_angle)
        measure_in_basis(qc, 1, bob_angle)
        qc.measure_all()
        total = _add_counts(total, simulator.run(qc, shots=n_clean).result().get_counts())
    if n_eve > 0:
        per = n_eve // 4
        rem = n_eve % 4
        for i, e_ang in enumerate(eve_bases):
            n = per + (1 if i < rem else 0)
            if n == 0:
                continue
            qc = _e91_eve_intercept_circuit(alice_angle, bob_angle, e_ang)
            raw = simulator.run(qc, shots=n).result().get_counts()
            total = _add_counts(total, _e91_counts_to_ab(raw))
    return total


def run_eve_attack_sweep():
    """
    Run BB84 and E91 with Eve's intercept-resend at various attack probabilities.
    """
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    eve_probs = [0.00, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]

    # BB84 Eve attack
    print("\n" + "="*60)
    print("BB84 EVE INTERCEPT-RESEND ATTACK")
    print("="*60)
    bb84_results = []
    for p_eve in eve_probs:
        qber_values = []
        key_lengths = []
        for run in range(10):
            result = eve_intercept_resend_bb84(100, p_eve)
            qber_values.append(result["qber"])
            key_lengths.append(result["key_length"])
        avg_qber = statistics.mean(qber_values)
        avg_key = statistics.mean(key_lengths)
        bb84_results.append({
            "eve_prob": p_eve,
            "qber": avg_qber,
            "key_length": avg_key,
        })
        print(f"Eve prob = {p_eve:.2f}: QBER = {avg_qber:.4%}, Key len = {avg_key:.1f}")

    df_bb84 = pd.DataFrame(bb84_results)
    df_bb84.to_csv(results_dir / "eve_bb84_attack.csv", index=False)
    print(f"Saved bb84 Eve results")

    # E91 Eve attack
    print("\n" + "="*60)
    print("E91 EVE INTERCEPT-RESEND ATTACK")
    print("="*60)
    e91_results = []
    for p_eve in eve_probs:
        result = eve_intercept_resend_e91(p_eve)
        e91_results.append({
            "eve_prob": p_eve,
            "chsh": result["chsh"],
            "chsh_std": result["chsh_std"],
            "bell_violation": result["bell_violation"],
        })
        print(f"Eve prob = {p_eve:.2f}: CHSH = {result['chsh']:.4f}, Violation = {result['bell_violation']}")

    df_e91 = pd.DataFrame(e91_results)
    df_e91.to_csv(results_dir / "eve_e91_attack.csv", index=False)
    print(f"Saved e91 Eve results")

    return df_bb84, df_e91


if __name__ == "__main__":
    run_eve_attack_sweep()