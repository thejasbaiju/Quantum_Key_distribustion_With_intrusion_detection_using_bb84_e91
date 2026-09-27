import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/bb84_bit_flip.csv")
df["qber_percent"] = df["qber"] * 100

plt.figure(figsize=(8, 5))
plt.plot(df["noise_strength"], df["qber_percent"], marker="o")
plt.xlabel("Bit-Flip Noise Strength (p)")
plt.ylabel("QBER (%)")
plt.title("BB84: Bit-Flip Noise Strength vs QBER")
plt.grid(True)
plt.tight_layout()
plt.savefig("plots/qber.png", dpi=150)
print("Saved plots/qber.png")