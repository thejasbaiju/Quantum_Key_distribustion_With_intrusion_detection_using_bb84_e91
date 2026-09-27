# Independent verification of the upstream simulation

Checked on 2026-09-27 against upstream commit `f415494`, using Python 3.12.7, qiskit 2.5.0 and qiskit-aer 0.17.2.

Reproduce from the repo root:

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
PYTHONPATH=. python verification/verify.py
```

## Test suite: 24 of 25 pass

`test_phase_flip_qber_bb84` fails intermittently. The threshold is too tight for the sample size, and the code itself is correct.
With n=500 only about 244 bits survive sifting. Over 20 reruns the mean QBER was 0.049 (expected 0.05), and 1 run in 20 fell below the 0.03 cutoff.

## Core physics checks

| Check | Upstream code | Independent NumPy model | Theory |
|---|---|---|---|
| BB84, full intercept-resend: QBER | 0.249 ± 0.019 | 0.251 | 0.25 |
| BB84, 50% intercept: QBER | 0.131 | — | 0.125 |
| E91, clean channel: CHSH S | 2.830 ± 0.010 | 2.8284 | 2√2 ≈ 2.828 |
| E91, full Eve intercept: CHSH S | 1.42 | — | ≤ 2 (≈ √2) |

## Known issues in the upstream code

1. **README formulas are wrong, but the code is right.** Depolarizing QBER is **p/2**, not p/3 (measured 0.155 at p=0.3).
   Amplitude-damping QBER averaged over both bases is ≈ (γ/2 + (1−√(1−γ))/2)/2, not γ/2 (measured 0.074 at γ=0.2, predicted 0.076).
2. **Noise is ignored during the BB84 Eve attack.** `eve_intercept_resend_bb84` accepts `noise_model`, but Bob's circuit has
   no `id` gate, which is the gate noise is attached to, so the noise never applies.
3. **No tests for the Eve attacks.**
4. **Readout error is modelled as a Pauli-X on `measure`** instead of Qiskit's `ReadoutError`. For a symmetric error the results are the same.
