import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/bb84_bit_flip.csv")

plt.figure(figsize=(8, 5))
plt.plot(df["noise_strength"], df["key_length"], marker="o")
plt.xlabel("Bit-Flip Noise Strength (p)")
plt.ylabel("Average Sifted Key Length (bits)")
plt.title("BB84: Bit-Flip Noise Strength vs Sifted Key Length")
plt.grid(True)
plt.tight_layout()
plt.savefig("plots/key_length.png", dpi=150)
print("Saved plots/key_length.png")