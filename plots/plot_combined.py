import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

results_dir = Path("results")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12

noise_types = ["bit_flip", "phase_flip", "depolarizing", "amplitude_damping", "readout_error"]
noise_labels = {
    "bit_flip": "Bit-Flip",
    "phase_flip": "Phase-Flip",
    "depolarizing": "Depolarizing",
    "amplitude_damping": "Amplitude Damping",
    "readout_error": "Readout Error",
}
noise_colors = {
    "bit_flip": "green",
    "phase_flip": "blue",
    "depolarizing": "red",
    "amplitude_damping": "orange",
    "readout_error": "purple",
}


def plot_qber_all_noise():
    plt.figure(figsize=(10, 6))
    for noise_type in noise_types:
        csv_path = results_dir / f"bb84_{noise_type}.csv"
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path)
        plt.plot(df["noise_strength"], df["qber"] * 100, marker="o",
                 label=noise_labels[noise_type], color=noise_colors[noise_type])
    plt.xlabel("Noise Strength (p)")
    plt.ylabel("QBER (%)")
    plt.title("BB84: QBER vs Noise Strength for All Noise Types")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("plots/qber_all_noise.png", dpi=150)
    print("Saved plots/qber_all_noise.png")


def plot_chsh_all_noise():
    plt.figure(figsize=(10, 6))
    for noise_type in noise_types:
        csv_path = results_dir / f"e91_{noise_type}.csv"
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path)
        plt.plot(df["noise_strength"], df["chsh"], marker="o",
                 label=noise_labels[noise_type], color=noise_colors[noise_type])
    plt.axhline(y=2.0, linestyle="--", color="gray", label="Classical limit (S=2)")
    plt.axhline(y=2*np.sqrt(2), linestyle="--", color="black", label="Quantum max (2√2)")
    plt.xlabel("Noise Strength (p)")
    plt.ylabel("CHSH Parameter (S)")
    plt.title("E91: CHSH vs Noise Strength for All Noise Types")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("plots/chsh_all_noise.png", dpi=150)
    print("Saved plots/chsh_all_noise.png")


def plot_eve_attack():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    bb84_df = pd.read_csv(results_dir / "eve_bb84_attack.csv")
    ax1.plot(bb84_df["eve_prob"], bb84_df["qber"] * 100, marker="o", color="red")
    ax1.set_xlabel("Eve Intercept Probability")
    ax1.set_ylabel("QBER (%)")
    ax1.set_title("BB84: Eve Attack vs QBER")
    ax1.grid(True, alpha=0.3)

    e91_df = pd.read_csv(results_dir / "eve_e91_attack.csv")
    ax2.plot(e91_df["eve_prob"], e91_df["chsh"], marker="s", color="blue")
    ax2.axhline(y=2.0, linestyle="--", color="gray", label="Classical limit")
    ax2.axhline(y=2*np.sqrt(2), linestyle="--", color="black", label="Quantum max")
    ax2.set_xlabel("Eve Intercept Probability")
    ax2.set_ylabel("CHSH (S)")
    ax2.set_title("E91: Eve Attack vs CHSH")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("plots/eve_attack.png", dpi=150)
    print("Saved plots/eve_attack.png")


def plot_bb84_vs_e91():
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    df_bb84 = pd.read_csv(results_dir / "bb84_bit_flip.csv")
    df_e91 = pd.read_csv(results_dir / "e91_bit_flip.csv")

    axes[0].plot(df_bb84["noise_strength"], df_bb84["qber"] * 100, marker="o", label="BB84", color="green")
    axes[0].plot(df_e91["noise_strength"], df_e91["chsh"] / 2 * 100, marker="s", label="E91 (S/2)", color="blue")
    axes[0].set_xlabel("Bit-Flip Noise Strength (p)")
    axes[0].set_ylabel("Error Rate (%)")
    axes[0].set_title("BB84 vs E91: Bit-Flip Noise")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(df_bb84["noise_strength"], df_bb84["key_length"] / 100 * 100, marker="o", label="BB84", color="green")
    axes[1].set_xlabel("Bit-Flip Noise Strength (p)")
    axes[1].set_ylabel("Key-Generation Efficiency (%)")
    axes[1].set_title("BB84: Key-Generation Efficiency")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(df_e91["noise_strength"], df_e91["chsh"], marker="s", label="E91", color="blue")
    axes[2].axhline(y=2.0, linestyle="--", color="gray", label="Classical limit")
    axes[2].axhline(y=2*np.sqrt(2), linestyle="--", color="black", label="Quantum max")
    axes[2].set_xlabel("Bit-Flip Noise Strength (p)")
    axes[2].set_ylabel("CHSH (S)")
    axes[2].set_title("E91: CHSH vs Noise")
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("plots/bb84_vs_e91.png", dpi=150)
    print("Saved plots/bb84_vs_e91.png")


def plot_combined_results():
    plot_qber_all_noise()
    plot_chsh_all_noise()
    plot_eve_attack()
    plot_bb84_vs_e91()
    print("\nAll final plots generated!")


if __name__ == "__main__":
    plot_combined_results()