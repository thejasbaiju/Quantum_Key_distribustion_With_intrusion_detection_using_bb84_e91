# Quantum Key Distribution with Intrusion Detection using BB84 & E91




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
├── backends/       # Aer / simulated IBM / real IBM runners, batched protocols
├── plots/          # Graph-generation scripts and output PNGs
├── results/        # CSV result data
├── tests/          # pytest test suite
├── verification/   # Independent verification script and report
├── CONTRIBUTION_REPORT.md
├── README.md
├── requirements.txt
├── .gitignore
├── seeding.py      # Reproducible seeds for Python and Aer
├── run_experiments.py
└── run_ibm.py      # Run BB84/E91 on Aer or IBM backends
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

## Running on IBM Quantum

`run_ibm.py` runs BB84 and E91 (with optional intercept-resend) on three kinds of backend through one interface (`backends/`):

| `--backend` | What it is | Account needed |
|---|---|---|
| `aer` | Local Aer simulator (ideal) | No |
| `fake_<device>`, e.g. `fake_torino` | Local simulation using an IBM device's calibrated noise (28 devices in `qiskit_ibm_runtime.fake_provider`) | No |
| `ibm_<device>`, e.g. `ibm_torino` | Real IBM Quantum hardware | Yes |

```bash
python run_ibm.py --backend fake_torino --eve 0 0.5 1
```

Example output on `fake_torino` (seed 1234):

| Eve intercept prob | BB84 QBER | ideal | E91 S | ideal |
|---|---|---|---|---|
| 0.0 | 0.014 | 0.000 | 2.702 | 2.828 |
| 0.5 | 0.125 | 0.125 | 2.043 | 2.121 |
| 1.0 | 0.240 | 0.250 | 1.373 | 1.414 |

Both protocols still detect a full intercept-resend attack under realistic device noise. Note that at 50% interception BB84 aborts (QBER > 11%) while E91 still shows a Bell violation (S ≈ 2.04).

**Real hardware.** Create an account at [quantum.cloud.ibm.com](https://quantum.cloud.ibm.com), then either save it once:

```python
from qiskit_ibm_runtime import QiskitRuntimeService
QiskitRuntimeService.save_account(token="<your API key>", channel="ibm_quantum_platform")
```

or set the `QISKIT_IBM_TOKEN` environment variable. Never commit the token. Real devices use your QPU allowance, so the script requires `--hardware`:

```bash
python run_ibm.py --backend ibm_torino --eve 0 1 --n 1000 --shots 2000 --hardware
```

**How it differs from the Aer experiments:**
- **BB84 is batched.** Only 8 distinct circuits exist (bit × Alice basis × Bob basis), so each runs once with shots equal to the rounds that use it, and outcomes are mapped back to the rounds. A run is one or two jobs instead of one job per qubit.
- **Custom noise models apply only to `aer`.** They attach to `id` gates, which device transpilers remove; IBM devices supply their own noise.
- **Circuits are transpiled at optimization level 3**, which picks qubits using calibration data. At level 1 these small circuits land on qubit 0, which on `fake_torino` has about 17% readout error (the median is 2%).
- E91 Eve attacks use mid-circuit measurement, reset and `if_test`, which IBM's Heron devices support.

## Testing

```bash
python -m pytest tests/ -v
```

The suite contains 40 tests covering noise-model correctness against theory, BB84 QBER bounds, E91 CHSH bounds, intercept-resend attacks, batched IBM backends (including a simulated IBM Torino), sifting, and input validation.

## Scope

**In scope:**
- BB84 and E91 protocol simulation on Qiskit Aer, simulated IBM devices, and IBM Quantum hardware
- Five noise models plus combined bit+phase noise
- Intercept-resend eavesdropping on both protocols
- QBER and CHSH security analysis with threshold identification
- BB84 vs E91 comparison (security, robustness, efficiency)

**Out of scope (future extensions):**
- Post-selection / error-correction / privacy-amplification stages
- Photon-number-splitting and Trojan-horse attacks
- Finite-key analysis
- Systematic real-device noise characterization (single runs on IBM devices are supported via `run_ibm.py`)
- Decoy-state BB84 variants

## Author

Thejas Baiju
Pranav M Nair
Soorya Narayanan
