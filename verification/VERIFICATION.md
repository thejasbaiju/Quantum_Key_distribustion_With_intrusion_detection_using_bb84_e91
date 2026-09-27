# Independent verification of the upstream simulation

Checked on 2026-09-27 against upstream commit `f415494`, using Python 3.12.7, qiskit 2.5.0 and qiskit-aer 0.17.2.

Reproduce from the repo root:

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
PYTHONPATH=. python verification/verify.py
```

## Test suite before fixes: 24 of 25 pass

`test_phase_flip_qber_bb84` fails intermittently. The threshold is too tight for the sample size, and the code itself is correct.
With n=500 only about 244 bits survive sifting. Over 20 reruns the mean QBER was 0.049 (expected 0.05), and 1 run in 20 fell below the 0.03 cutoff.

## Core physics checks

| Check | Upstream code | Independent NumPy model | Theory |
|---|---|---|---|
| BB84, full intercept-resend: QBER | 0.249 ± 0.019 | 0.251 | 0.25 |
| BB84, 50% intercept: QBER | 0.131 | — | 0.125 |
| E91, clean channel: CHSH S | 2.830 ± 0.010 | 2.8284 | 2√2 ≈ 2.828 |
| E91, full Eve intercept: CHSH S | 1.42 | — | ≤ 2 (≈ √2) |

## Issues found in the upstream code, and their status

1. **Wrong QBER formulas in the README and CONTRIBUTION_REPORT.** Fixed. The code was right; the docs were wrong.
   - Bit-flip: **p/2**, not p. X errors leave |+⟩/|−⟩ unchanged, so only Z-basis bits are affected.
   - Depolarizing: **p/2**, not p/3 (measured 0.155 at p=0.3).
   - Amplitude damping: **γ/4 + (1−√(1−γ))/4 ≈ 3γ/8**, not γ/2 (measured 0.074 at γ=0.2, predicted 0.076).
2. **Noise was ignored during the BB84 Eve attack.** Fixed. Bob's circuit had no `id` gate, which is the gate
   noise attaches to. `test_bb84_eve_attack_applies_channel_noise` fails without the fix. The committed
   `results/eve_bb84_attack.csv` is unaffected because the sweep runs without noise.
3. **Flaky tests.** Fixed. The BB84 noise tests used hand-picked ranges, one of them centred on the wrong
   formula. They now assert within 3σ of the theoretical QBER, computed from the actual sifted key length.
   All randomness is seeded through `seeding.py` (`tests/conftest.py` pins seed 1234), so the suite gives
   the same result on every run. Across 30 other seeds, 1 run had a single 3.05σ miss, as expected
   statistically.
4. **No tests for the Eve attacks.** Fixed in `tests/test_eve_attack.py`:
   - BB84 full intercept: QBER ≈ 1/4
   - BB84 half intercept: QBER ≈ 1/8
   - clean E91: S ≈ 2√2
   - E91 full intercept: S ≈ √2, derived analytically as the average of cos2(x−e)·cos2(y−e) over Eve's four angles
5. **Readout error is modelled as a Pauli-X on `measure`** instead of Qiskit's `ReadoutError`. Not changed:
   for a symmetric error the results are the same.

Test suite after fixes: 32/32 pass in about 3 s.
