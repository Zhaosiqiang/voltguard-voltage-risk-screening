# Implementation Roadmap

## Completed Route

1. Generate IEEE 33-bus, IEEE 69-bus, and supplementary IEEE 118-bus AC
   scenarios with fixed seed.
2. Evaluate configured multi-seed and multi-split models through
   `experiments/evaluate_models.py`.
3. Save raw predictions, conformal scores, per-family metrics, scenario-level
   metrics, conformal ablations, runtime, and operating-value outputs.
4. Run AC corrective grid-search benchmark through
   `experiments/evaluate_control_benchmark.py`.
5. Assemble ECM:X-route manuscript and compile PDF.

## Current Gates

- `experiments/validate_project.py` must pass.
- No article figure files should exist; only figure descriptions are provided.
- Author metadata, funding, repository URL, conflicts, and final journal fields
  remain manual.

## Stretch Work

- Add IEEE 123-bus/OpenDSS or SMART-DS feeder.
- Replace discrete grid search with OPF/MPC downstream benchmark.
- Add stronger theory and experiments for topology and temporal shift.
