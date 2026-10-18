"""Compare simulated and theoretical BB84 interception detection probability."""

import argparse
import csv
from pathlib import Path

from detection.probability import simulate_detection_probability, theoretical_detection_probability


DEFAULT_CHECK_BITS = [1, 2, 3, 4, 5, 8, 10, 12, 16, 20]


def run_experiment(check_bits=DEFAULT_CHECK_BITS, trials=10000, seed=1234):
    rows = []
    for k in check_bits:
        simulated = simulate_detection_probability(k, trials=trials, seed=seed + k)
        theoretical = theoretical_detection_probability(k)
        rows.append({
            "check_bits": k,
            "trials": trials,
            "simulated_detection_probability": simulated,
            "theoretical_detection_probability": theoretical,
            "absolute_error": abs(simulated - theoretical),
        })
    return rows


def save_results(rows, results_path, plot_path):
    results_path = Path(results_path)
    plot_path = Path(plot_path)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    plot_path.parent.mkdir(parents=True, exist_ok=True)

    with results_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = [row["check_bits"] for row in rows]
    simulated = [row["simulated_detection_probability"] for row in rows]
    theoretical = [row["theoretical_detection_probability"] for row in rows]
    plt.figure(figsize=(8, 5))
    plt.plot(x, theoretical, label=r"Theory: $1-(3/4)^k$", linewidth=2)
    plt.scatter(x, simulated, label="Monte Carlo simulation", zorder=3)
    plt.xlabel("Disclosed check bits (k)")
    plt.ylabel("Probability of detecting Eve")
    plt.title("BB84 Full Intercept-Resend Detection Probability")
    plt.ylim(0, 1.03)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, dpi=180)
    plt.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args(argv)
    rows = run_experiment(trials=args.trials, seed=args.seed)
    save_results(
        rows,
        "results/detection_probability.csv",
        "plots/detection_probability.png",
    )
    print("Saved results/detection_probability.csv")
    print("Saved plots/detection_probability.png")


if __name__ == "__main__":
    main()
