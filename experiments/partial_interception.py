"""Compare BB84 and E91 under partial intercept-resend attacks."""

import argparse
import csv
import math
import statistics
from pathlib import Path

from backends.protocols import ideal_bb84_qber, ideal_e91_chsh, run_bb84_batched, run_e91_batched
from backends.runners import get_runner
from detection.statistical import SECURE, bb84_statistical_test, e91_statistical_test
from seeding import seed_all


DEFAULT_EVE_PROBS = [i / 10 for i in range(11)]


def ideal_bb84_interception_limit(qber_threshold=0.11):
    """Interception fraction where ideal BB84 reaches the QBER threshold."""
    return min(1.0, 4 * qber_threshold)


def ideal_e91_interception_limit():
    """Interception fraction where the repository's ideal E91 model reaches S=2."""
    return 2 - math.sqrt(2)


def run_experiment(
    eve_probs=DEFAULT_EVE_PROBS,
    n=4000,
    shots=4000,
    check_bits=512,
    alpha=0.01,
    repeats=10,
    seed=1234,
):
    seed_all(seed)
    runner = get_runner("aer")
    rows = []
    for eve_prob in eve_probs:
        bb84_qbers, bb84_secure = [], []
        e91_values, e91_secure = [], []
        for _ in range(repeats):
            bb84 = run_bb84_batched(n, runner, eve_prob)
            k = min(check_bits, max(1, bb84["key_length"] - 1))
            bb84_test = bb84_statistical_test(
                bb84["alice_key"], bb84["bob_key"], k, alpha=alpha
            )
            bb84_qbers.append(bb84_test["qber"])
            bb84_secure.append(bb84_test["operational_decision"] == SECURE)

            e91 = run_e91_batched(shots, runner, eve_prob)
            e91_test = e91_statistical_test(
                [e91["E_ab"], e91["E_ab_prime"], e91["E_a_prime_b"], e91["E_a_prime_b_prime"]],
                shots,
                alpha=alpha,
            )
            e91_values.append(e91["chsh"])
            e91_secure.append(e91_test["operational_decision"] == SECURE)

        rows.append({
            "eve_probability": eve_prob,
            "bb84_sample_qber": statistics.mean(bb84_qbers),
            "bb84_qber_std": statistics.pstdev(bb84_qbers),
            "bb84_theoretical_qber": ideal_bb84_qber(eve_prob),
            "bb84_secure_rate": statistics.mean(bb84_secure),
            "e91_chsh": statistics.mean(e91_values),
            "e91_chsh_std": statistics.pstdev(e91_values),
            "e91_theoretical_chsh": ideal_e91_chsh(eve_prob),
            "e91_secure_rate": statistics.mean(e91_secure),
            "repeats": repeats,
            "alpha": alpha,
            "bb84_check_bits": check_bits,
            "e91_shots_per_setting": shots,
        })
    return rows


def save_results(rows, results_path, plot_path, decision_plot_path):
    results_path = Path(results_path)
    plot_path = Path(plot_path)
    decision_plot_path = Path(decision_plot_path)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    decision_plot_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    x = [row["eve_probability"] for row in rows]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].errorbar(x, [row["bb84_sample_qber"] for row in rows],
                     yerr=[row["bb84_qber_std"] for row in rows], marker="o", capsize=3,
                     label="Simulation")
    axes[0].plot(x, [row["bb84_theoretical_qber"] for row in rows], label="Theory: p(Eve)/4")
    axes[0].axhline(0.11, color="red", linestyle="--", label="11% QBER limit")
    axes[0].axvline(ideal_bb84_interception_limit(), color="gray", linestyle=":",
                    label="Ideal crossing: 44%")
    axes[0].set(xlabel="Eve interception probability", ylabel="Sampled QBER",
                title="BB84 under Partial Interception")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()

    axes[1].errorbar(x, [row["e91_chsh"] for row in rows],
                     yerr=[row["e91_chsh_std"] for row in rows], marker="o", capsize=3,
                     label="Simulation")
    axes[1].plot(x, [row["e91_theoretical_chsh"] for row in rows], label="Theory")
    axes[1].axhline(2, color="red", linestyle="--", label="Classical limit")
    axes[1].axvline(ideal_e91_interception_limit(), color="gray", linestyle=":",
                    label="Ideal crossing: 58.6%")
    axes[1].set(xlabel="Eve interception probability", ylabel="CHSH S",
                title="E91 under Partial Interception")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()

    fig.suptitle("BB84 vs E91: Partial Intercept-Resend")
    fig.tight_layout()
    fig.savefig(plot_path, dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, [row["bb84_secure_rate"] for row in rows], marker="o", label="BB84 secure-accept rate")
    ax.plot(x, [row["e91_secure_rate"] for row in rows], marker="s", label="E91 secure-accept rate")
    ax.axvline(ideal_bb84_interception_limit(), color="tab:blue", linestyle=":", label="BB84 raw limit: 44%")
    ax.axvline(ideal_e91_interception_limit(), color="tab:orange", linestyle=":", label="E91 raw limit: 58.6%")
    ax.set_xlabel("Eve interception probability")
    ax.set_ylabel("Fraction of runs accepted as secure")
    ax.set_title("Confidence-Aware Acceptance under Partial Interception")
    ax.set_ylim(-0.03, 1.03)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(decision_plot_path, dpi=180)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=4000)
    parser.add_argument("--shots", type=int, default=4000)
    parser.add_argument("--check-bits", type=int, default=512)
    parser.add_argument("--alpha", type=float, default=0.01)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args(argv)
    rows = run_experiment(
        n=args.n,
        shots=args.shots,
        check_bits=args.check_bits,
        alpha=args.alpha,
        repeats=args.repeats,
        seed=args.seed,
    )
    save_results(
        rows,
        "results/partial_interception.csv",
        "plots/partial_interception.png",
        "plots/partial_interception_decisions.png",
    )
    print("Saved results/partial_interception.csv")
    print("Saved plots/partial_interception.png")
    print("Saved plots/partial_interception_decisions.png")


if __name__ == "__main__":
    main()
