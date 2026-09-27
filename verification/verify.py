import math, random, statistics, numpy as np
random.seed(1); np.random.seed(1)
from experiments.eve_attack import eve_intercept_resend_bb84, eve_intercept_resend_e91
from e91.e91 import run_e91
from bb84.bb84 import run_bb84
from noise.noise_models import phase_flip_noise, depolarizing_noise, amplitude_damping_noise

print("=== CHECK 1: BB84 full intercept-resend (repo code) ===")
q=[eve_intercept_resend_bb84(1000,1.0) for _ in range(4)]
tot=sum(len(r["alice_key"]) for r in q); err=sum(sum(a!=b for a,b in zip(r["alice_key"],r["bob_key"])) for r in q)
p=err/tot; print(f"QBER = {p:.4f}  (sifted bits={tot}, ±{1.96*math.sqrt(p*(1-p)/tot):.4f} 95% CI)  expected 0.25")
for pe in (0.0,0.5):
    rs=[eve_intercept_resend_bb84(1000,pe) for _ in range(2)]
    print(f"  eve_prob={pe}: QBER={statistics.mean(r['qber'] for r in rs):.4f}  expected {pe/4:.3f}")

print("=== CHECK 1b: independent NumPy BB84 intercept-resend ===")
N=200000
ab=np.random.randint(2,size=N); aB=np.random.randint(2,size=N); eB=np.random.randint(2,size=N); bB=np.random.randint(2,size=N)
e=np.where(eB==aB,ab,np.random.randint(2,size=N))
b=np.where(bB==eB,e,np.random.randint(2,size=N))
m=aB==bB; print(f"QBER = {(ab[m]!=b[m]).mean():.4f}")

print("=== CHECK 2: E91 clean channel S (repo code) ===")
Ss=[run_e91(shots=20000)["chsh"] for _ in range(5)]
print(f"S = {statistics.mean(Ss):.4f} ± {statistics.pstdev(Ss):.4f}  expected {2*math.sqrt(2):.4f}")
print("=== CHECK 2b: E91 with full Eve intercept (repo code) ===")
r=eve_intercept_resend_e91(1.0,shots=4000); print(f"S = {r['chsh']:.4f}  expected <=2 (violation={r['bell_violation']})")

print("=== CHECK 2c: independent analytic S from density matrix ===")
phi=np.array([1,0,0,1])/np.sqrt(2)
def Ry(t): return np.array([[math.cos(t/2),-math.sin(t/2)],[math.sin(t/2),math.cos(t/2)]])
Z=np.diag([1,-1])
def E(x,y):
    U=np.kron(Ry(-2*x),Ry(-2*y)); s=U@phi   # note qiskit little-endian is irrelevant for ZZ
    return s@np.kron(Z,Z)@s
a,ap,b_,bp=0,math.pi/4,math.pi/8,3*math.pi/8
print(f"S = {E(a,b_)-E(a,bp)+E(ap,b_)+E(ap,bp):.4f}")

print("=== CHECK 3: phase-flip test failure — is it just a flaky threshold? ===")
qs=[run_bb84(500,phase_flip_noise(0.1))["qber"] for _ in range(20)]
print(f"20 runs n=500: mean={statistics.mean(qs):.4f}, min={min(qs):.4f}, fails(<0.03)={sum(x<0.03 for x in qs)}/20  expected mean 0.05")

print("=== CHECK 4: README claims vs reality ===")
for name,nm,claim in [("depolarizing p=0.3",depolarizing_noise(0.3),"README says p/3=0.100"),("amp damping g=0.2",amplitude_damping_noise(0.2),"README says g/2=0.100")]:
    qs=[run_bb84(2000,nm)["qber"] for _ in range(2)]
    print(f"{name}: QBER={statistics.mean(qs):.4f}  ({claim})")
