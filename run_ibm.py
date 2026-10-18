"""
Run BB84 and E91 (with optional intercept-resend) on Aer, a simulated IBM
device, or real IBM Quantum hardware.

Examples:
    python run_ibm.py --backend aer
    python run_ibm.py --backend fake_torino --eve 0 0.5 1
    python run_ibm.py --backend ibm_torino --eve 0 1 --n 1000 --shots 2000 --hardware

Real hardware needs an IBM Quantum account: either save it once with
    QiskitRuntimeService.save_account(token="...", channel="ibm_quantum_platform")
or set the QISKIT_IBM_TOKEN environment variable. Never commit your token.
"""
import argparse
import sys

from backends.protocols import run_bb84_batched, run_e91_batched, ideal_bb84_qber, ideal_e91_chsh
from backends.runners import get_runner
from seeding import seed_all


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backend", default="fake_torino", help="aer, fake_<device> (e.g. fake_torino) or ibm_<device> (default: fake_torino)")
    parser.add_argument("--protocol", choices=["bb84", "e91", "all"], default="all")
    parser.add_argument("--eve", type=float, nargs="+", default=[0.0, 1.0], help="intercept probabilities to run (default: 0 1)")
    parser.add_argument("--n", type=int, default=2000, help="BB84 qubits sent per run (default: 2000)")
    parser.add_argument("--shots", type=int, default=4000, help="E91 shots per CHSH setting (default: 4000)")
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--hardware", action="store_true", help="required for ibm_* backends: confirms you want to spend QPU time")
    args = parser.parse_args(argv)

    if args.backend.startswith("ibm_") and not args.hardware:
        sys.exit(f"{args.backend} is real hardware and uses your IBM Quantum time. Re-run with --hardware to confirm.")

    seed_all(args.seed)
    runner = get_runner(args.backend)
    print(f"Backend: {runner.name}  ({'real hardware' if runner.is_hardware else 'simulator'})")
    print("'Ideal' columns are noise-free theory; the gap to 'measured' is device or channel noise.\n")

    if args.protocol in ("bb84", "all"):
        print(f"BB84, {args.n} qubits per run")
        print(f"{'eve prob':>9} {'QBER':>8} {'ideal':>7} {'sifted':>7}  verdict (QBER < 11%)")
        for p in args.eve:
            r = run_bb84_batched(args.n, runner, p)
            verdict = "secure" if r["qber"] < 0.11 else "ABORT: eavesdropper/noise"
            print(f"{p:>9.2f} {r['qber']:>8.4f} {ideal_bb84_qber(p):>7.4f} {r['key_length']:>7}  {verdict}")
        print()

    if args.protocol in ("e91", "all"):
        print(f"E91 CHSH, {args.shots} shots per setting")
        print(f"{'eve prob':>9} {'S':>8} {'ideal':>7}  verdict (S > 2)")
        for p in args.eve:
            r = run_e91_batched(args.shots, runner, p)
            verdict = "secure" if r["bell_violation"] else "ABORT: no Bell violation"
            print(f"{p:>9.2f} {r['chsh']:>8.3f} {ideal_e91_chsh(p):>7.3f}  {verdict}")


if __name__ == "__main__":
    main()
