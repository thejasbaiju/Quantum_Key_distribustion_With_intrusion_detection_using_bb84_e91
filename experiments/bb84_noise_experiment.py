import pandas as pd
from pathlib import Path
import statistics
from bb84.bb84 import run_bb84
from noise.noise_models import bit_flip_noise

# Only needed if you actually use run_noise_sweep_average below
from e91.e91 import (
    calculate_correlation,
    calculate_chsh,
    run_measurement,
    a, a_prime, b, b_prime
)


def run_noise_sweep(noise_values, n, runs):
    """
    Run BB84 for multiple noise strengths.
    """
    results = []

    for p in noise_values:
        print(f"\nRunning noise level: {p:.2f}")

        qber_values = []
        key_lengths = []

        for run in range(runs):
            print(f"  Run {run + 1}/{runs}", end="\r")

            noise_model = bit_flip_noise(p)
            result = run_bb84(n, noise_model)

            qber_values.append(result["qber"])
            key_lengths.append(len(result["alice_key"]))

        average_qber = sum(qber_values) / len(qber_values)
        average_key_length = sum(key_lengths) / len(key_lengths)

        results.append({
            "noise_strength": p,
            "qber": average_qber,
            "key_length": average_key_length
        })

        print(
            f"  Completed: "
            f"QBER = {average_qber:.2%}, "
            f"Key length = {average_key_length:.1f}"
        )

    return results


def run_noise_sweep_average(noise_values, shots=1000, runs=20):
    """
    Run E91 multiple times for each noise strength
    and calculate the average CHSH value.
    """
    results = []

    for p in noise_values:
        print(f"\nRunning noise level: {p:.2f}")

        chsh_values = []

        for run in range(runs):
            noise_model = bit_flip_noise(p)

            E_ab = calculate_correlation(run_measurement(a, b, noise_model, shots=shots))
            E_ab_prime = calculate_correlation(run_measurement(a, b_prime, noise_model, shots=shots))
            E_a_prime_b = calculate_correlation(run_measurement(a_prime, b, noise_model, shots=shots))
            E_a_prime_b_prime = calculate_correlation(
                run_measurement(a_prime, b_prime, noise_model, shots)
            )

            S = calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime)
            chsh_values.append(S)

        std_chsh = statistics.stdev(chsh_values)
        average_chsh = sum(chsh_values) / len(chsh_values)

        results.append({
            "noise_strength": p,
            "chsh": average_chsh,
            "chsh_std": std_chsh
        })

        print(f"Average CHSH = {average_chsh:.4f}, Std = {std_chsh:.4f}")

    return results


if __name__ == "__main__":

    noise_values = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

    results = run_noise_sweep(noise_values, n=100, runs=20)

    df = pd.DataFrame(results)

    print("\n===== BB84 BIT-FLIP EXPERIMENT =====")
    print(df)

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    output_file = results_dir / "bb84_bit_flip.csv"
    df.to_csv(output_file, index=False)

    print(f"\nData saved to: {output_file}")