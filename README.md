# Quantum Key Distribution with Intrusion Detection using BB84 & E91

> **Attribution:** The simulation code in this repository is based on
> [alia5252/QKD-BB84-E91-SIMULATION](https://github.com/alia5252/QKD-BB84-E91-SIMULATION)
> (commit `f415494`). See [NOTICE](NOTICE). Independent verification of its results is in
> [verification/VERIFICATION.md](verification/VERIFICATION.md).


## Project Overview

A simulation study of Quantum Key Distribution (QKD) protocols using Qiskit. The project implements the two foundational QKD protocols — BB84 and E91 — subjects them to realistic channel noise and eavesdropping attacks, and quantifies their security through established metrics (QBER and the CHSH parameter).

## Research Question

How do different quantum channel noise models and eavesdropping strategies affect the security and performance of prepare-and-measure (BB84) versus entanglement-based (E91) QKD protocols?

## BB84 & E91 Explanation

### BB84 (Prepare & Measure)

- Alice prepares qubits in randomly chosen bases (Z: |0⟩/|1⟩, X: |+⟩/|−⟩) encoding random bits.
- Bob measures each qubit in a randomly chosen basis.
- After transmission, Alice and Bob publicly compare bases (sifting) and keep only matching-basis bits.
- Security is verified by testing a subset of the sifted key: the Quantum Bit Error Rate (QBER) reveals eavesdropping.

### E91 (Entanglement Based)

- A source distributes entangled Bell pairs |Φ⁺⟩ = (|00⟩ + |11⟩)/√2 to Alice and Bob.
- Each party measures in one of several angles (Alice: a=0, a′=π/4; Bob: b=π/8, b′=3π/8).
- Correlations E(a,b) are computed from joint measurement statistics.
- Security is verified via the CHSH inequality: S = E(a,b) − E(a,b′) + E(a′,b) + E(a′,b′). Quantum mechanics allows S up to 2√2 ≈ 2.83; classical local realism is bounded by |S| ≤ 2. Any measured |S| ≤ 2 indicates either excessive noise or eavesdropping.

## Noise Models

| Noise Model | Mechanism | BB84 Effect |
|---|---|---|
| **Bit-flip** | Pauli-X with probability p | QBER = p/2 (Z-basis only) |
| **Phase-flip** | Pauli-Z with probability p | QBER = p/2 (X-basis only) |
| **Depolarizing** | Mixed X/Y/Z with probability p | QBER ≈ p/2 |
| **Amplitude damping** | |1⟩ decays to |0⟩ with probability γ | QBER ≈ γ/4 + (1−√(1−γ))/4 ≈ 3γ/8 (γ/2 in Z basis only) |
| **Readout error** | Measurement bit-flip with probability p | QBER = p |
| **Combined bit+phase** | Simultaneous X and Z errors | QBER ≈ p |

All noise is applied via Qiskit Aer noise models attached to the identity (channel) operation in the quantum circuit.

## Metrics

- **QBER (Quantum Bit Error Rate)** — fraction of mismatched bits in the sifted key. Security threshold: QBER < 11%.
- **CHSH parameter S** — Bell inequality value. Security threshold: S > 2 (Bell violation must persist).
- **Key-generation efficiency** — sifted key length as a fraction of transmitted qubits (≈50% from basis sifting).
- **Eve attack probability** — intercept-resend probability sweep, measured against both QBER and CHSH.

## Repository Structure

```
QKD_project/
├── bb84/           # BB84 protocol implementation
├── e91/            # E91 protocol implementation
├── noise/          # Noise channel models (Aer)
├── experiments/    # Noise sweeps, Eve attacks, completeness runs
├── plots/          # Graph-generation scripts and output PNGs
├── results/        # CSV result data
├── tests/          # pytest test suite
├── CONTRIBUTION_REPORT.md
├── README.md
├── requirements.txt
├── .gitignore
└── run_experiments.py
```

## Installation

```bash
pip install -r requirements.txt
```

Requires Python 3.10+.

## Running Instructions

Run the full noise experiment suite:

```bash
python run_experiments.py
```

Or run individual experiment modules:

```bash
python -m experiments.completeness
python -m experiments.eve_attack
python -m experiments.noise_experiments
```

Generate all final graphs:

```bash
python -m plots.plot_combined
```

## Testing

```bash
python -m pytest tests/ -v
```

The suite contains 25 tests covering noise-model correctness against theory, BB84 QBER bounds, E91 CHSH bounds, sifting, and input validation.

## Scope

**In scope:**
- BB84 and E91 protocol simulation on Qiskit Aer
- Five noise models plus combined bit+phase noise
- Intercept-resend eavesdropping on both protocols
- QBER and CHSH security analysis with threshold identification
- BB84 vs E91 comparison (security, robustness, efficiency)

**Out of scope (future extensions):**
- Post-selection / error-correction / privacy-amplification stages
- Photon-number-splitting and Trojan-horse attacks
- Finite-key analysis
- Hardware/real-device noise characterization
- Decoy-state BB84 variants

## Author

Thejas Baiju
Pranav M Nair
Soorya Narayanan