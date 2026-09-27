import pandas as pd
import statistics
from pathlib import Path
from bb84.bb84 import run_bb84
from e91.e91 import run_e91, run_measurement, calculate_correlation, calculate_chsh, a, a_prime, b, b_prime
from noise.noise_models import (
    bit_flip_noise,
    phase_flip_noise,
    depolarizing_noise,
    amplitude_damping_noise,
    readout_error_noise,
)


def run_bb84_noise_sweep(noise_type, noise_values, n=100, runs=20):
    """
    Run BB84 for multiple noise strengths of a given type.
    """
    results = []
    factory = {
        "bit_flip": bit_flip_noise,
        "phase_flip": phase_flip_noise,
        "depolarizing": depolarizing_noise,
        "amplitude_damping": amplitude_damping_noise,
        "readout_error": readout_error_noise,
    }[noise_type]

    for p in noise_values:
        print(f"\nBB84 {noise_type}: p = {p:.4f}")
        noise_model = factory(p)

        qber_values = []
        key_lengths = []

        for run in range(runs):
            result = run_bb84(n, noise_model)
            qber_values.append(result["qber"])
            key_lengths.append(len(result["alice_key"]))

        avg_qber = statistics.mean(qber_values)
        avg_key = statistics.mean(key_lengths)

        results.append({
            "noise_strength": p,
            "qber": avg_qber,
            "key_length": avg_key,
            "noise_type": noise_type,
        })

        print(f"  QBER = {avg_qber:.4%}, Key len = {avg_key:.1f}")

    return results


def run_e91_noise_sweep(noise_type, noise_values, shots=1000, repeats=5):
    """
    Run E91 for multiple noise strengths of a given type.
    """
    results = []
    factory = {
        "bit_flip": bit_flip_noise,
        "phase_flip": phase_flip_noise,
        "depolarizing": depolarizing_noise,
        "amplitude_damping": amplitude_damping_noise,
        "readout_error": readout_error_noise,
    }[noise_type]

    for p in noise_values:
        print(f"\nE91 {noise_type}: p = {p:.4f}")
        noise_model = factory(p)

        chsh_values = []

        for run in range(repeats):
            E_ab = calculate_correlation(run_measurement(a, b, noise_model, shots=shots))
            E_ab_prime = calculate_correlation(run_measurement(a, b_prime, noise_model, shots=shots))
            E_a_prime_b = calculate_correlation(run_measurement(a_prime, b, noise_model, shots=shots))
            E_a_prime_b_prime = calculate_correlation(run_measurement(a_prime, b_prime, noise_model, shots=shots))
            chsh_values.append(calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime))

        avg_chsh = statistics.mean(chsh_values)
        std_chsh = statistics.pstdev(chsh_values)
        bell_violation = abs(avg_chsh) > 2

        results.append({
            "noise_strength": p,
            "chsh": avg_chsh,
            "chsh_std": std_chsh,
            "bell_violation": bell_violation,
            "noise_type": noise_type,
        })

        print(f"  CHSH = {avg_chsh:.4f}, Violation = {bell_violation}")

    return results


def run_all_noise_experiments():
    """Run all noise experiments for all noise types."""
    noise_values = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # BB84 noise experiments
    for noise_type in ["bit_flip", "phase_flip", "depolarizing", "amplitude_damping", "readout_error"]:
        print(f"\n{'='*60}")
        print(f"BB84 {noise_type.upper()} NOISE EXPERIMENT")
        print(f"{'='*60}")
        results = run_bb84_noise_sweep(noise_type, noise_values)
        df = pd.DataFrame(results)
        csv_path = results_dir / f"bb84_{noise_type}.csv"
        df.to_csv(csv_path, index=False)
        print(f"Saved to {csv_path}")

    # E91 noise experiments
    for noise_type in ["bit_flip", "phase_flip", "depolarizing", "amplitude_damping", "readout_error"]:
        print(f"\n{'='*60}")
        print(f"E91 {noise_type.upper()} NOISE EXPERIMENT")
        print(f"{'='*60}")
        results = run_e91_noise_sweep(noise_type, noise_values)
        df = pd.DataFrame(results)
        csv_path = results_dir / f"e91_{noise_type}.csv"
        df.to_csv(csv_path, index=False)
        print(f"Saved to {csv_path}")


if __name__ == "__main__":
    run_all_noise_experiments()