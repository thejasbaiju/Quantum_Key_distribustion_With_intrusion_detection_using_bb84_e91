"""Demonstrate basis-wise BB84 diagnostics for noise and Eve."""

import argparse
import csv
from pathlib import Path

from backends.protocols import run_bb84_batched
from backends.runners import get_runner
from detection.basis_diagnostic import diagnose_basis_errors
from noise.noise_models import bit_flip_noise, phase_flip_noise, readout_error_noise
from seeding import seed_all


def _run_case(name, n, eve_prob=0.0, noise_model=None):
    result = run_bb84_batched(n, get_runner("aer", noise_model=noise_model), eve_prob)
    diagnostic = diagnose_basis_errors(
        result["alice_key"], result["bob_key"], result["sifted_bases"]
    )
    return {
        "scenario": name,
        "z_qber": diagnostic["z_basis"]["qber"],
        "x_qber": diagnostic["x_basis"]["qber"],
        "classification": diagnostic["classification"],
        "sifted_bits": result["key_length"],
    }


def run_experiment(n=10000, seed=1234):
    seed_all(seed)
    return [
        _run_case("clean", n),
        _run_case("bit_flip_p0.20", n, noise_model=bit_flip_noise(0.20)),
        _run_case("phase_flip_p0.20", n, noise_model=phase_flip_noise(0.20)),
        _run_case("readout_p0.20", n, noise_model=readout_error_noise(0.20)),
        _run_case("eve_full_intercept", n, eve_prob=1.0),
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
    import numpy as np

    positions = np.arange(len(rows))
    width = 0.36
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(positions - width / 2, [row["z_qber"] for row in rows], width, label="Z-basis QBER")
    ax.bar(positions + width / 2, [row["x_qber"] for row in rows], width, label="X-basis QBER")
    ax.set_xticks(positions, [row["scenario"].replace("_", "\n") for row in rows])
    ax.set_ylabel("Basis-specific QBER")
    ax.set_title("BB84 Basis Error Signatures: Diagnostic, Not a Security Proof")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args(argv)
    rows = run_experiment(n=args.n, seed=args.seed)
    save_results(rows, "results/basis_diagnostic.csv", "plots/basis_diagnostic.png")
    print("Saved results/basis_diagnostic.csv")
    print("Saved plots/basis_diagnostic.png")


if __name__ == "__main__":
    main()
