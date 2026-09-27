import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results/bb84_bit_flip.csv")
n = 100
df["key_efficiency"] = (df["key_length"] / n) * 100

plt.figure(figsize=(8, 5))
plt.plot(df["noise_strength"], df["key_efficiency"], marker="o")
plt.xlabel("Bit-Flip Noise Strength (p)")
plt.ylabel("Key-Generation Efficiency (%)")
plt.title("BB84: Bit-Flip Noise Strength vs Key-Generation Efficiency")
plt.grid(True)
plt.tight_layout()
plt.savefig("plots/key_efficiency.png", dpi=150)
print("Saved plots/key_efficiency.png")