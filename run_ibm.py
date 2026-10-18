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
from detection.statistical import bb84_statistical_test, e91_statistical_test
from detection.basis_diagnostic import diagnose_basis_errors
from seeding import seed_all


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backend", default="fake_torino", help="aer, fake_<device> (e.g. fake_torino) or ibm_<device> (default: fake_torino)")
    parser.add_argument("--protocol", choices=["bb84", "e91", "all"], default="all")
    parser.add_argument("--eve", type=float, nargs="+", default=[0.0, 1.0], help="intercept probabilities to run (default: 0 1)")
    parser.add_argument("--n", type=int, default=2000, help="BB84 qubits sent per run (default: 2000)")
    parser.add_argument("--shots", type=int, default=4000, help="E91 shots per CHSH setting (default: 4000)")
    parser.add_argument("--check-bits", type=int, default=256, help="BB84 sifted bits disclosed for parameter estimation (default: 256)")
    parser.add_argument("--alpha", type=float, default=0.01, help="statistical error probability for confidence bounds (default: 0.01)")
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
        print(f"{'eve prob':>9} {'sample Q':>9} {'bounds':>17} {'remain':>7}  statistical verdict")
        for p in args.eve:
            r = run_bb84_batched(args.n, runner, p)
            k = min(args.check_bits, r["key_length"])
            if k == 0:
                print(f"{p:>9.2f} {'n/a':>9} {'no sifted key':>17} {0:>7}  ABORT")
                continue
            detector = bb84_statistical_test(r["alice_key"], r["bob_key"], k, alpha=args.alpha)
            bounds = f"[{detector['lower_bound']:.3f},{detector['upper_bound']:.3f}]"
            print(
                f"{p:>9.2f} {detector['qber']:>9.4f} {bounds:>17} "
                f"{detector['remaining_key_length']:>7}  "
                f"{detector['decision']} -> {detector['operational_decision']}"
            )
            print(f"{'':>11}noise-free expected QBER={ideal_bb84_qber(p):.4f}; {detector['reason']}")
            check_bases = [r["sifted_bases"][i] for i in detector["check_indices"]]
            diagnostic = diagnose_basis_errors(
                detector["alice_check"], detector["bob_check"], check_bases
            )
            z_qber = diagnostic["z_basis"]["qber"]
            x_qber = diagnostic["x_basis"]["qber"]
            z_text = "n/a" if z_qber is None else f"{z_qber:.3f}"
            x_text = "n/a" if x_qber is None else f"{x_qber:.3f}"
            print(
                f"{'':>11}basis diagnostic={diagnostic['classification']} "
                f"(Z={z_text}, X={x_text}); diagnostic only"
            )
        print()

    if args.protocol in ("e91", "all"):
        print(f"E91 CHSH, {args.shots} shots per setting")
        print(f"{'eve prob':>9} {'S':>8} {'lower':>8} {'ideal':>8}  statistical verdict")
        for p in args.eve:
            r = run_e91_batched(args.shots, runner, p)
            detector = e91_statistical_test(
                [r["E_ab"], r["E_ab_prime"], r["E_a_prime_b"], r["E_a_prime_b_prime"]],
                args.shots,
                alpha=args.alpha,
            )
            print(
                f"{p:>9.2f} {r['chsh']:>8.3f} {detector['lower_bound']:>8.3f} "
                f"{ideal_e91_chsh(p):>8.3f}  "
                f"{detector['decision']} -> {detector['operational_decision']}"
            )


if __name__ == "__main__":
    main()
