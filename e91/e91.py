from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from noise.noise_models import bit_flip_noise
import math
import statistics
import pandas as pd
from pathlib import Path


a = 0
a_prime = math.pi / 4

b = math.pi / 8
b_prime = 3 * math.pi / 8

def create_entangled_pair():
    """Create the Bell state |Phi+>."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.id(0)
    qc.id(1)
    return qc


def measure_in_basis(qc, qubit, angle):
    """Rotate the qubit according to the measurement angle."""
    qc.ry(-2 * angle, qubit)


def run_measurement(alice_angle, bob_angle, noise_model=None, shots=100):
    """Run one E91 measurement setting."""
    qc = create_entangled_pair()
    measure_in_basis(qc, 0, alice_angle)
    measure_in_basis(qc, 1, bob_angle)
    qc.measure_all()

    simulator = AerSimulator() if noise_model is None else AerSimulator(noise_model=noise_model)
    result = simulator.run(qc, shots=shots).result()
    return result.get_counts()


def calculate_correlation(counts):
    """
    Calculate E(a,b).
    E = P(00) + P(11) - P(01) - P(10)
    """
    total = sum(counts.values())
    n00 = counts.get("00", 0)
    n01 = counts.get("01", 0)
    n10 = counts.get("10", 0)
    n11 = counts.get("11", 0)
    return ((n00 + n11) - (n01 + n10)) / total


def calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime):
    """S = E(a,b) - E(a,b') + E(a',b) + E(a',b')"""
    return E_ab - E_ab_prime + E_a_prime_b + E_a_prime_b_prime


def run_e91(shots=1000):
    """Run the complete ideal E91 CHSH experiment."""
    E_ab = calculate_correlation(run_measurement(a, b, shots=shots))
    E_ab_prime = calculate_correlation(run_measurement(a, b_prime, shots=shots))
    E_a_prime_b = calculate_correlation(run_measurement(a_prime, b, shots=shots))
    E_a_prime_b_prime = calculate_correlation(run_measurement(a_prime, b_prime, shots=shots))

    S = calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime)
    bell_violation = abs(S) > 2

    return {
        "E_ab": E_ab,
        "E_ab_prime": E_ab_prime,
        "E_a_prime_b": E_a_prime_b,
        "E_a_prime_b_prime": E_a_prime_b_prime,
        "chsh": S,
        "bell_violation": bell_violation
    }


def run_noise_sweep(noise_values, shots=1000, repeats=5):
    """Run E91 for multiple bit-flip noise strengths, averaging over `repeats` trials."""
    results = []

    for p in noise_values:
        print(f"Running noise level: {p:.2f}")
        noise_model = bit_flip_noise(p)

        chsh_trials = []
        for _ in range(repeats):
            E_ab = calculate_correlation(run_measurement(a, b, noise_model, shots=shots))
            E_ab_prime = calculate_correlation(run_measurement(a, b_prime, noise_model, shots=shots))
            E_a_prime_b = calculate_correlation(run_measurement(a_prime, b, noise_model, shots=shots))
            E_a_prime_b_prime = calculate_correlation(run_measurement(a_prime, b_prime, noise_model, shots=shots))
            chsh_trials.append(calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime))

        average_chsh = statistics.mean(chsh_trials)
        std_chsh = statistics.pstdev(chsh_trials)
        bell_violation = abs(average_chsh) > 2

        results.append({
            "noise_strength": p,
            "chsh": average_chsh,
            "chsh_std": std_chsh,
            "bell_violation": bell_violation
        })

    return results


if __name__ == "__main__":

    alice_angle = 0
    bob_angle = math.pi / 4

    counts = run_measurement(alice_angle, bob_angle)
    correlation = calculate_correlation(counts)

    print("===== E91 CORRELATION =====")
    print(f"Alice angle = {alice_angle}")
    print(f"Bob angle   = {bob_angle}")
    print("\nMeasurement results:")
    print(counts)
    print(f"Correlation = {correlation:.4f}")

    result = run_e91(shots=1000)

    print("\n===== E91 CHSH EXPERIMENT =====")
    print(f"E(a,b)     = {result['E_ab']:.4f}")
    print(f"E(a,b')    = {result['E_ab_prime']:.4f}")
    print(f"E(a',b)    = {result['E_a_prime_b']:.4f}")
    print(f"E(a',b')   = {result['E_a_prime_b_prime']:.4f}")
    print(f"\nCHSH S = {result['chsh']:.4f}")
    print(f"Theoretical maximum = {2 * math.sqrt(2):.4f}")
    print("Classical limit = 2.0000")
    if result["bell_violation"]:
        print("Bell inequality violated: E91 shows quantum correlation.")
    else:
        print("No Bell inequality violation detected.")

    noise_values = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    results = run_noise_sweep(noise_values, shots=1000)
    for result in results:

        if not result["bell_violation"]:
            print(
                f"\nBell violation disappears at "
                f"noise strength p = {result['noise_strength']:.2f}"
            )
            break
    df = pd.DataFrame(results)

    print("\n===== E91 BIT-FLIP NOISE EXPERIMENT =====")
    print(df)

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    output_file = results_dir / "e91_noise.csv"
    df.to_csv(output_file, index=False)
    print(f"\nData saved to: {output_file}")