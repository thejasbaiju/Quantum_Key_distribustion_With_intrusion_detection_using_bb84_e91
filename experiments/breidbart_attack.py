"""Sweep the BB84 Breidbart-basis intercept-resend attack."""

import argparse
import csv
import math
import statistics
from pathlib import Path

from attacks.breidbart import run_breidbart_bb84
from backends.runners import get_runner
from detection.statistical import ABORT, bb84_statistical_test
from seeding import seed_all


DEFAULT_EVE_PROBS = [i / 10 for i in range(11)]


def run_experiment(eve_probs=DEFAULT_EVE_PROBS, n=4000, check_bits=512, alpha=0.01, repeats=10, seed=1234):
    seed_all(seed)
    runner = get_runner("aer")
    rows = []
    for eve_prob in eve_probs:
        runs = [run_breidbart_bb84(n, runner, eve_prob) for _ in range(repeats)]
        eve_rates = [run["eve_bit_error_rate"] for run in runs if run["eve_bit_error_rate"] is not None]
        detector_results = [
            bb84_statistical_test(
                run["alice_key"],
                run["bob_key"],
                min(check_bits, max(1, run["key_length"] - 1)),
                alpha=alpha,
            )
            for run in runs
        ]
        rows.append({
            "eve_probability": eve_prob,
            "bb84_qber": statistics.mean(run["qber"] for run in runs),
            "theoretical_bb84_qber": eve_prob / 4,
            "eve_bit_error_rate": statistics.mean(eve_rates) if eve_rates else "",
            "theoretical_eve_bit_error_rate": math.sin(math.pi / 8) ** 2 if eve_prob > 0 else "",
            "detector_abort_rate": statistics.mean(
                result["operational_decision"] == ABORT for result in detector_results
            ),
            "repeats": repeats,
            "qubits_per_repeat": n,
            "check_bits": check_bits,
            "alpha": alpha,
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

    x = [row["eve_probability"] for row in rows]
    qber = [row["bb84_qber"] for row in rows]
    theory = [row["theoretical_bb84_qber"] for row in rows]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(x, theory, label="Bob theory: p(Eve)/4", linewidth=2)
    ax.scatter(x, qber, label="Bob simulated QBER", zorder=3)
    ax.axhline(math.sin(math.pi / 8) ** 2, color="purple", linestyle="--",
               label="Eve bit error at pi/8: 14.64%")
    ax.set_xlabel("Eve interception probability")
    ax.set_ylabel("Error rate")
    ax.set_ylim(0, 0.30)
    ax.grid(True, alpha=0.3)

    detector_axis = ax.twinx()
    detector_axis.plot(x, [row["detector_abort_rate"] for row in rows], color="green",
                       marker="s", linestyle=":", label="Detector operational abort rate")
    detector_axis.set_ylabel("Detector abort rate")
    detector_axis.set_ylim(-0.03, 1.03)
    handles, labels = ax.get_legend_handles_labels()
    extra_handles, extra_labels = detector_axis.get_legend_handles_labels()
    ax.legend(handles + extra_handles, labels + extra_labels, loc="upper left")
    ax.set_title("BB84 Breidbart-Basis Intercept-Resend Attack")
    fig.tight_layout()
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=4000)
    parser.add_argument("--check-bits", type=int, default=512)
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args(argv)
    rows = run_experiment(
        n=args.n,
        check_bits=args.check_bits,
        alpha=args.alpha,
        repeats=args.repeats,
        seed=args.seed,
    )
    save_results(rows, "results/breidbart_attack.csv", "plots/breidbart_attack.png")
    print("Saved results/breidbart_attack.csv")
    print("Saved plots/breidbart_attack.png")


if __name__ == "__main__":
    main()
