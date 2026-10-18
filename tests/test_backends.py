import math
import random

import pytest

from backends.protocols import measure_batched, run_bb84_batched, run_e91_batched, ideal_e91_chsh
from backends.runners import get_runner
from noise.noise_models import bit_flip_noise

from tests.helpers import assert_qber_near


@pytest.fixture(scope="module")
def aer():
    return get_runner("aer")


@pytest.fixture(scope="module")
def torino():
    return get_runner("fake_torino")


def test_measure_batched_returns_each_rounds_outcome(aer):
    """Grouping into 8 circuits must hand every round back its own outcome."""
    bits = [random.randint(0, 1) for _ in range(200)]
    bases = [random.choice(["Z", "X"]) for _ in range(200)]
    assert measure_batched(list(zip(bits, bases)), bases, aer) == bits


def test_bb84_batched_no_eve(aer):
    assert run_bb84_batched(1000, aer)["qber"] == 0.0


def test_bb84_batched_full_intercept(aer):
    assert_qber_near(run_bb84_batched(4000, aer, 1.0), 0.25)


def test_bb84_batched_applies_aer_noise():
    """Bit-flip p on the channel gives QBER = p/2, as in the unbatched protocol."""
    runner = get_runner("aer", noise_model=bit_flip_noise(0.1))
    assert_qber_near(run_bb84_batched(4000, runner), 0.05)


def test_e91_batched_matches_theory(aer):
    for p in (0.0, 0.5, 1.0):
        S = run_e91_batched(8000, aer, p)["chsh"]
        assert abs(S - ideal_e91_chsh(p)) < 0.08, f"eve={p}: S={S}, expected {ideal_e91_chsh(p)}"


def test_device_backend_rejects_custom_noise():
    with pytest.raises(ValueError):
        get_runner("fake_torino", noise_model=bit_flip_noise(0.1))


def test_unknown_backend():
    with pytest.raises(ValueError):
        get_runner("not_a_backend")


def test_fake_torino_detects_eve(torino):
    """
    On simulated IBM Torino noise the protocols still separate a clean channel
    from a full intercept-resend attack.
    """
    clean_bb84 = run_bb84_batched(1000, torino)["qber"]
    eve_bb84 = run_bb84_batched(1000, torino, 1.0)["qber"]
    assert clean_bb84 < 0.05 and eve_bb84 > 0.18, (clean_bb84, eve_bb84)

    clean_S = run_e91_batched(2000, torino)["chsh"]
    eve_S = run_e91_batched(2000, torino, 1.0)["chsh"]
    assert clean_S > 2.4, clean_S
    assert eve_S < 2.0, eve_S
