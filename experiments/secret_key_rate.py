"""Generate the asymptotic BB84 secret-key-fraction curve."""

import csv
from pathlib import Path

from detection.key_rate import secret_key_fraction


def generate_rows(step=0.001, maximum=0.20):
    count = round(maximum / step)
    return [
        {"qber": i * step, "secret_key_fraction": secret_key_fraction(i * step)}
        for i in range(count + 1)
    ]


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

    qber = [row["qber"] * 100 for row in rows]
    fraction = [row["secret_key_fraction"] for row in rows]
    plt.figure(figsize=(8, 5))
    plt.plot(qber, fraction, linewidth=2, label=r"$r=\max(0,1-2h_2(Q))$")
    plt.axvline(11.0, color="red", linestyle="--", label="Approx. 11% threshold")
    plt.xlabel("QBER (%)")
    plt.ylabel("Asymptotic secret-key fraction")
    plt.title("BB84 Secret-Key Fraction vs QBER")
    plt.ylim(-0.02, 1.03)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(plot_path, dpi=180)
    plt.close()


def main():
    rows = generate_rows()
    save_results(rows, "results/secret_key_rate.csv", "plots/secret_key_rate.png")
    print("Saved results/secret_key_rate.csv")
    print("Saved plots/secret_key_rate.png")


if __name__ == "__main__":
    main()
