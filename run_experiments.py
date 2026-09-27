import sys
sys.path.insert(0, '.')
from experiments.noise_experiments import run_all_noise_experiments

print("Starting full noise experiment suite...")
run_all_noise_experiments()
print("\nDone!")