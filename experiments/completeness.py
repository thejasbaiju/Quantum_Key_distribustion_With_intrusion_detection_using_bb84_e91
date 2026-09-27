import sys
sys.path.insert(0, '..')
import pandas as pd
import statistics
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import math

from bb84.bb84 import run_bb84, sift_key, generate_alice_data, prepare_qubit, calculate_qber
from e91.e91 import create_entangled_pair, measure_in_basis, calculate_correlation, calculate_chsh, a, a_prime, b, b_prime, run_measurement
from noise.noise_models import bit_flip_noise, phase_flip_noise, depolarizing_noise, amplitude_damping_noise, readout_error_noise, combined_bit_phase_flip
from experiments.eve_attack import eve_intercept_resend_bb84, eve_intercept_resend_e91

results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

print("=" * 60)
print("1. COMBINED BIT+PHASE FLIP NOISE SWEEP")
print("=" * 60)

noise_values = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
results = []
for p in noise_values:
    print(f"\nCombined bit+phase p = {p:.2f}")
    noise_model = combined_bit_phase_flip(p, p)
    qber_vals = []
    key_lengths = []
    for run in range(10):
        result = run_bb84(100, noise_model)
        qber_vals.append(result["qber"])
        key_lengths.append(len(result["alice_key"]))
    results.append({
        "noise_strength": p,
        "qber": statistics.mean(qber_vals),
        "key_length": statistics.mean(key_lengths),
        "noise_type": "combined_bit_phase"
    })
    print(f"  QBER = {statistics.mean(qber_vals):.4f}")

df = pd.DataFrame(results)
df.to_csv(results_dir / "bb84_combined_bit_phase.csv", index=False)
print("Saved results/bb84_combined_bit_phase.csv")

print("\n" + "=" * 60)
print("2. CHSH SWEEP - ALL NOISE TYPES")
print("=" * 60)

chsh_noise_types = ["bit_flip", "phase_flip", "depolarizing", "amplitude_damping", "readout_error"]
chsh_results = []
for noise_type in chsh_noise_types:
    print(f"\n--- {noise_type} ---")
    factory = {
        "bit_flip": bit_flip_noise,
        "phase_flip": phase_flip_noise,
        "depolarizing": depolarizing_noise,
        "amplitude_damping": amplitude_damping_noise,
        "readout_error": readout_error_noise,
    }[noise_type]
    for p in noise_values:
        noise_model = factory(p)
        chsh_vals = []
        for _ in range(5):
            E_ab = calculate_correlation(run_measurement(a, b, noise_model, shots=500))
            E_ab_prime = calculate_correlation(run_measurement(a, b_prime, noise_model, shots=500))
            E_a_prime_b = calculate_correlation(run_measurement(a_prime, b, noise_model, shots=500))
            E_a_prime_b_prime = calculate_correlation(run_measurement(a_prime, b_prime, noise_model, shots=500))
            chsh_vals.append(calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime))
        chsh_results.append({
            "noise_strength": p,
            "chsh": statistics.mean(chsh_vals),
            "chsh_std": statistics.pstdev(chsh_vals),
            "noise_type": noise_type
        })

df_chsh = pd.DataFrame(chsh_results)
df_chsh.to_csv(results_dir / "chsh_all_noise_types.csv", index=False)
print("Saved results/chsh_all_noise_types.csv")

print("\n" + "=" * 60)
print("3. E91 COMBINED BIT+PHASE NOISE SWEEP")
print("=" * 60)

e91_combined = []
for p in noise_values:
    print(f"\nE91 combined bit+phase p = {p:.2f}")
    noise_model = combined_bit_phase_flip(p, p)
    chsh_vals = []
    for _ in range(5):
        E_ab = calculate_correlation(run_measurement(a, b, noise_model, shots=500))
        E_ab_prime = calculate_correlation(run_measurement(a, b_prime, noise_model, shots=500))
        E_a_prime_b = calculate_correlation(run_measurement(a_prime, b, noise_model, shots=500))
        E_a_prime_b_prime = calculate_correlation(run_measurement(a_prime, b_prime, noise_model, shots=500))
        chsh_vals.append(calculate_chsh(E_ab, E_ab_prime, E_a_prime_b, E_a_prime_b_prime))
    e91_combined.append({
        "noise_strength": p,
        "chsh": statistics.mean(chsh_vals),
        "chsh_std": statistics.pstdev(chsh_vals),
        "noise_type": "combined_bit_phase"
    })
    print(f"  CHSH = {statistics.mean(chsh_vals):.4f}")

df_ec = pd.DataFrame(e91_combined)
df_ec.to_csv(results_dir / "e91_combined_bit_phase.csv", index=False)
print("Saved results/e91_combined_bit_phase.csv")

print("\n" + "=" * 60)
print("4. KEY GENERATION EFFICIENCY vs QBER TRADEOFF")
print("=" * 60)

# Plot QBER vs key efficiency
tradeoff_data = []
for p in noise_values:
    for noise_type in ["bit_flip", "phase_flip", "depolarizing", "amplitude_damping", "readout_error"]:
        factory = {
            "bit_flip": bit_flip_noise,
            "phase_flip": phase_flip_noise,
            "depolarizing": depolarizing_noise,
            "amplitude_damping": amplitude_damping_noise,
            "readout_error": readout_error_noise,
        }[noise_type]
        noise_model = factory(p)
        qber_vals = []
        key_lengths = []
        for run in range(5):
            result = run_bb84(100, noise_model)
            qber_vals.append(result["qber"])
            key_lengths.append(len(result["alice_key"]))
        tradeoff_data.append({
            "noise_strength": p,
            "noise_type": noise_type,
            "qber": statistics.mean(qber_vals),
            "key_efficiency": statistics.mean(key_lengths) / 100.0,
        })

df_tradeoff = pd.DataFrame(tradeoff_data)
df_tradeoff.to_csv(results_dir / "key_efficiency_tradeoff.csv", index=False)
print("Saved results/key_efficiency_tradeoff.csv")

print("\n" + "=" * 60)
print("5. SECURITY THRESHOLDS")
print("=" * 60)

# BB84: 11% QBER threshold
thresholds = []
for noise_type in ["bit_flip", "phase_flip", "depolarizing", "amplitude_damping", "readout_error", "combined_bit_phase"]:
    csv_path = results_dir / f"bb84_{noise_type}.csv"
    if not csv_path.exists():
        continue
    df = pd.read_csv(csv_path)
    threshold = None
    for _, row in df.iterrows():
        if row["qber"] > 0.11:
            threshold = row["noise_strength"]
            break
    qber_02 = float(df[df.noise_strength == 0.2]["qber"].values[0]) if len(df[df.noise_strength == 0.2]) > 0 else None
    thresholds.append({
        "noise_type": noise_type,
        "qber_at_0.2": qber_02,
        "threshold_p": threshold,
    })
    print(f"BB84 {noise_type}: QBER@0.2={qber_02}, threshold_p={threshold}")

df_thresholds = pd.DataFrame(thresholds)
df_thresholds.to_csv(results_dir / "security_thresholds.csv", index=False)
print("Saved results/security_thresholds.csv")

print("\n" + "=" * 60)
print("ALL COMPLETENESS EXPERIMENTS COMPLETE")
print("=" * 60)
