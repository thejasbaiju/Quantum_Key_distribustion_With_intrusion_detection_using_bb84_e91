import random


def seed_all(seed):
    """Seed Python's RNG so bases, bits and simulator seeds are reproducible."""

    random.seed(seed)


def sim_seed():
    """
    Draw a fresh Aer seed from Python's RNG for one simulator.run() call.

    A single fixed seed would make every 1-shot run return the same outcome,
    so each call gets its own seed; seed_all() makes the sequence reproducible.
    """

    return random.getrandbits(31)
