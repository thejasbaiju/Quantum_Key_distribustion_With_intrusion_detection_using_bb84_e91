import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/e91_bit_flip.csv")

plt.figure(figsize=(8, 5))
plt.errorbar(
    df["noise_strength"],
    df["chsh"],
    marker="o",
    capsize=4,
    label="E91 CHSH"
)
plt.axhline(y=2.0, linestyle="--", label="Classical limit (S=2)")
plt.axhline(y=2*(2**0.5), linestyle="--", label="Theoretical maximum (2√2)")
plt.xlabel("Noise Strength (p)")
plt.ylabel("CHSH Parameter (S)")
plt.title("E91: Noise Strength vs CHSH Parameter")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("plots/chsh.png", dpi=150)
print("Saved plots/chsh.png")