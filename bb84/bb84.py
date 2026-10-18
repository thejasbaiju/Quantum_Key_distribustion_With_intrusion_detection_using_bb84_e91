import random

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from noise.noise_models import bit_flip_noise
from seeding import sim_seed


def generate_alice_data(n):
    """Generate Alice's random bits and bases."""

    bits = [random.randint(0, 1) for _ in range(n)]
    bases = [random.choice(["Z", "X"]) for _ in range(n)]

    return bits, bases


def prepare_qubit(bit, basis):
    """Prepare one BB84 qubit."""

    qc = QuantumCircuit(1, 1)

    # Encode the bit
    if bit == 1:
        qc.x(0)

    # Choose the X basis
    if basis == "X":
        qc.h(0)

    # End of Alice's preparation
    qc.barrier()

    return qc


def prepare_alice_qubits(bits, bases):
    """Prepare all qubits."""

    circuits = []

    for bit, basis in zip(bits, bases):
        circuits.append(
            prepare_qubit(bit, basis)
        )

    return circuits


def measure_qubit(qc, basis, simulator):
    """Bob measures one qubit."""

    bob_qc = qc.copy()

    # Quantum channel
    bob_qc.id(0)

    # Bob chooses measurement basis
    if basis == "X":
        bob_qc.h(0)

    # Measurement
    bob_qc.measure(0, 0)

    result = simulator.run(
        bob_qc,
        shots=1,
        seed_simulator=sim_seed()
    ).result()

    counts = result.get_counts()

    return int(list(counts.keys())[0])


def measure_all_qubits(circuits, bob_bases, noise_model=None):
    """Bob measures all qubits."""

    simulator = AerSimulator(
        noise_model=noise_model
    )

    bob_bits = []

    for qc, basis in zip(circuits, bob_bases):

        bit = measure_qubit(
            qc,
            basis,
            simulator
        )

        bob_bits.append(bit)

    return bob_bits


def sift_key(
    alice_bits,
    alice_bases,
    bob_bases,
    bob_bits
):
    """Keep bits where Alice and Bob used the same basis."""

    alice_key = []
    bob_key = []

    for alice_bit, alice_basis, bob_basis, bob_bit in zip(
        alice_bits,
        alice_bases,
        bob_bases,
        bob_bits
    ):

        if alice_basis == bob_basis:
            alice_key.append(alice_bit)
            bob_key.append(bob_bit)

    return alice_key, bob_key


def calculate_qber(alice_key, bob_key):
    """Calculate QBER."""

    if not alice_key:
        return 0.0

    errors = sum(
        a != b
        for a, b in zip(alice_key, bob_key)
    )

    return errors / len(alice_key)


def run_bb84(n, noise_model=None):
    """Run one complete BB84 experiment."""

    # Alice
    alice_bits, alice_bases = generate_alice_data(n)

    # Alice prepares qubits
    alice_qubits = prepare_alice_qubits(
        alice_bits,
        alice_bases
    )

    # Bob chooses bases
    bob_bases = [
        random.choice(["Z", "X"])
        for _ in range(n)
    ]

    # Bob measures
    bob_bits = measure_all_qubits(
        alice_qubits,
        bob_bases,
        noise_model
    )

    # Sifting
    alice_key, bob_key = sift_key(
        alice_bits,
        alice_bases,
        bob_bases,
        bob_bits
    )

    # QBER
    qber = calculate_qber(
        alice_key,
        bob_key
    )

    return {
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "bob_bases": bob_bases,
        "bob_bits": bob_bits,
        "alice_key": alice_key,
        "bob_key": bob_key,
        "qber": qber
    }


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    N = 1000

    # Ideal experiment
    ideal_result = run_bb84(N)

    print("===== IDEAL BB84 =====")
    print(
        "Sifted key length:",
        len(ideal_result["alice_key"])
    )
    print(
        "QBER:",
        f"{ideal_result['qber']:.2%}"
    )

    # Bit-flip experiment
    noise_model = bit_flip_noise(0.1)

    noisy_result = run_bb84(
        N,
        noise_model
    )

    print("\n===== BIT-FLIP BB84 =====")
    print(
        "reSifted key length:",
        len(noisy_result["alice_key"])
    )
    print(
        "QBER:",
        f"{noisy_result['qber']:.2%}"
    )
