import pytest

from seeding import seed_all


@pytest.fixture(autouse=True)
def fixed_seed():
    """Make every test reproducible: same bases, bits and Aer outcomes each run."""
    seed_all(1234)
