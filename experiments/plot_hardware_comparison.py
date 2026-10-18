"""Plot ideal Aer, calibrated fake Fez, and real IBM Fez results."""

from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    data = pd.read_csv("results/hardware_comparison.csv")
    # The final row is a larger clean-BB84 confirmation run; keep the common
    # 512-qubit / 1000-shot configuration in the direct three-backend plot.
    common = data[~((data.backend == "ibm_fez") & (data.protocol == "BB84") & (data.qubits_or_shots == 1024))]
    backends = ["aer", "fake_fez", "ibm_fez"]
    labels = ["Ideal Aer", "Fake Fez", "Real IBM Fez"]
    x = np.arange(len(backends))
    width = 0.34

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for offset, eve, name in [(-width / 2, 0, "Clean"), (width / 2, 1, "Full intercept")]:
        bb84 = [
            float(common[(common.backend == backend) & (common.protocol == "BB84") & (common.eve_probability == eve)].measured_value.iloc[0])
            for backend in backends
        ]
        e91 = [
            float(common[(common.backend == backend) & (common.protocol == "E91") & (common.eve_probability == eve)].measured_value.iloc[0])
            for backend in backends
        ]
        axes[0].bar(x + offset, bb84, width, label=name)
        axes[1].bar(x + offset, e91, width, label=name)

    axes[0].axhline(0.11, color="red", linestyle="--", label="11% QBER limit")
    axes[0].set_title("BB84 Hardware Comparison")
    axes[0].set_ylabel("Sampled QBER")
    axes[0].set_xticks(x, labels)
    axes[0].grid(True, axis="y", alpha=0.3)
    axes[0].legend()

    axes[1].axhline(2.0, color="red", linestyle="--", label="CHSH classical limit")
    axes[1].set_title("E91 Hardware Comparison")
    axes[1].set_ylabel("CHSH S")
    axes[1].set_xticks(x, labels)
    axes[1].grid(True, axis="y", alpha=0.3)
    axes[1].legend()

    fig.suptitle("QKD Intrusion Detection: Simulation vs Real IBM Quantum Hardware")
    fig.tight_layout()
    output = Path("plots/hardware_comparison.png")
    output.parent.mkdir(exist_ok=True)
    fig.savefig(output, dpi=180)
    plt.close(fig)
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
