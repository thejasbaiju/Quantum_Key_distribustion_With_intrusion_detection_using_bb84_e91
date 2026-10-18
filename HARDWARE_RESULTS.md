# IBM Quantum Hardware Validation

Date: 2026-10-18  
Real backend: `ibm_fez` (156 qubits, open-plan instance)  
Comparison backends: ideal Qiskit Aer and calibrated `fake_fez`

## Common experiment configuration

- BB84: 512 transmitted qubits, 192 randomly disclosed check bits, alpha = 0.01.
- E91: 1,000 shots per CHSH setting, alpha = 0.01.
- Scenarios: clean channel and full intercept-resend.
- `INCONCLUSIVE` is mapped to an operational `ABORT`.

| Backend | BB84 clean QBER | BB84 full-attack QBER | E91 clean S | E91 full-attack S |
|---|---:|---:|---:|---:|
| Ideal Aer | 0.0000 | 0.2708 | 2.862 | 1.392 |
| Fake Fez | 0.0000 | 0.2188 | 2.746 | 1.366 |
| Real IBM Fez | 0.0104 | 0.2552 | 2.620 | 0.718 |

The clean real-hardware BB84 point estimate was low, but 192 check bits gave an
upper confidence bound of 0.120, slightly above the 0.11 security threshold.
It was therefore correctly marked `INCONCLUSIVE -> ABORT`, rather than being
accepted from the point estimate alone.

A follow-up clean BB84 run used 1,024 transmitted qubits and 384 check bits. It
measured QBER 0.0026 with upper bound 0.080 and was accepted as `SECURE` while
leaving 105 undisclosed sifted bits.

## Real hardware jobs

| Experiment | Job ID | Decision |
|---|---|---|
| BB84 clean, 512 qubits | `dbaco68c77vs7382jum0` | Inconclusive -> abort |
| BB84 Eve measurement, 512 qubits | `dbaco8gc77vs7382jup0` | Intermediate Eve job |
| BB84 full attack, 512 qubits | `dbacoac24mrc73856n1g` | Abort |
| E91 clean, 1,000 shots/setting | `dbacoc7i0auc7391qi10` | Secure |
| E91 full attack, 1,000 shots/setting | `dbacoe424mrc73856n5g` | Abort |
| BB84 clean confirmation, 1,024 qubits | `dbacongc77vs7382jv70` | Secure |

## Interpretation

The real device preserved sufficient quantum behavior to accept a clean E91
session and the larger clean BB84 session. Both protocols rejected full
interception. The full-attack E91 value on real Fez was substantially below the
ideal and calibrated-simulator values; this strengthens the abort decision but
should be described as combined attack and hardware disturbance, not as a new
theoretical prediction. These runs demonstrate feasibility, not a systematic
hardware characterization; repeated jobs across calibration periods would be
needed for that claim.
