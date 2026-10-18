"""Experiment entry points, imported lazily to avoid unnecessary dependencies."""


def run_all_noise_experiments(*args, **kwargs):
    from .noise_experiments import run_all_noise_experiments as implementation
    return implementation(*args, **kwargs)


def run_bb84_noise_sweep(*args, **kwargs):
    from .noise_experiments import run_bb84_noise_sweep as implementation
    return implementation(*args, **kwargs)


def run_e91_noise_sweep(*args, **kwargs):
    from .noise_experiments import run_e91_noise_sweep as implementation
    return implementation(*args, **kwargs)


def run_eve_attack_sweep(*args, **kwargs):
    from .eve_attack import run_eve_attack_sweep as implementation
    return implementation(*args, **kwargs)
