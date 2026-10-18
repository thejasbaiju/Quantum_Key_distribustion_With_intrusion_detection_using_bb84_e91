import os

from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator

from seeding import sim_seed


class AerRunner:
    """Local Aer simulator, optionally with one of the repo's noise models."""

    def __init__(self, noise_model=None):
        self.name = "aer"
        self.is_hardware = False
        self.simulator = AerSimulator(noise_model=noise_model)

    def sample(self, circuits, shots):
        """Run each circuit with its own shot count; return per-shot bitstrings per circuit."""

        memories = []
        for qc, n in zip(circuits, shots):
            result = self.simulator.run(
                qc,
                shots=n,
                memory=True,
                seed_simulator=sim_seed()
            ).result()
            memories.append(result.get_memory())

        return memories


class SamplerRunner:
    """
    IBM device through Qiskit Runtime's SamplerV2.

    With a fake backend (qiskit_ibm_runtime.fake_provider) this runs locally on
    Aer using that device's calibrated noise; with a real backend it submits one
    job to IBM Quantum. Both take exactly the same code path.
    """

    def __init__(self, backend, is_hardware):
        self.backend = backend
        self.name = backend.name
        self.is_hardware = is_hardware
        # Level 3 picks qubits using calibration data. Level 1 places these small
        # circuits on qubit 0, which on some devices has very poor readout
        # (e.g. ~17% on fake_torino vs a 2% median).
        self.pass_manager = generate_preset_pass_manager(
            backend=backend,
            optimization_level=3
        )

    def sample(self, circuits, shots):
        """
        Transpile to the device's native gates and run all circuits as one job.

        Runtime no longer accepts different shot counts per circuit in one job,
        so every circuit runs with the largest count and each result is trimmed
        to the shots it asked for.
        """

        # SamplerV2 is deprecated from qiskit-ibm-runtime 0.50.0 but still works
        # with the pinned version; migrate to its client-side Sampler when upgrading.
        from qiskit_ibm_runtime import SamplerV2

        sampler = SamplerV2(mode=self.backend)
        if not self.is_hardware:
            sampler.options.simulator.seed_simulator = sim_seed()

        isa_circuits = self.pass_manager.run(list(circuits))
        job = sampler.run(isa_circuits, shots=max(shots))

        if self.is_hardware:
            print(f"Submitted job {job.job_id()} to {self.name}; waiting for results...")

        return [
            pub_result.join_data().get_bitstrings()[:n]
            for pub_result, n in zip(job.result(), shots)
        ]


def get_runner(name, noise_model=None):
    """
    Build a runner by name.

    'aer'          local Aer simulator (noise_model optional)
    'fake_<name>'  local simulation of an IBM device, e.g. 'fake_torino'
    'ibm_<name>'   real IBM Quantum hardware, e.g. 'ibm_torino'. Needs a saved
                   account (QiskitRuntimeService.save_account) or the
                   QISKIT_IBM_TOKEN environment variable.
    """

    if name == "aer":
        return AerRunner(noise_model)

    if noise_model is not None:
        raise ValueError(
            "Custom noise models only apply to 'aer'; IBM devices use their own noise."
        )

    if name.startswith("fake_"):
        from qiskit_ibm_runtime import fake_provider

        class_name = "Fake" + name[len("fake_"):].capitalize()
        backend_class = getattr(fake_provider, class_name, None)
        if backend_class is None:
            raise ValueError(f"Unknown fake device '{name}' (no {class_name} in qiskit_ibm_runtime.fake_provider).")

        return SamplerRunner(backend_class(), is_hardware=False)

    if name.startswith("ibm_"):
        from qiskit_ibm_runtime import QiskitRuntimeService

        token = os.environ.get("QISKIT_IBM_TOKEN")
        if token:
            service = QiskitRuntimeService(channel="ibm_quantum_platform", token=token)
        else:
            service = QiskitRuntimeService()

        return SamplerRunner(service.backend(name), is_hardware=True)

    raise ValueError(f"Unknown backend '{name}'. Use 'aer', 'fake_<device>' or 'ibm_<device>'.")
