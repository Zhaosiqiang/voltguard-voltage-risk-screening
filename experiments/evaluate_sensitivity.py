"""Compatibility entry point.

Conformal risk-level sensitivity is now produced by evaluate_models.py so that
all split, seed, grouping, and raw-output tables share one configuration.
"""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    path = Path("VoltGuard-CPGNN/experiments/results/conformal_sensitivity_metrics.md")
    if not path.exists():
        raise SystemExit("Run evaluate_models.py before evaluate_sensitivity.py")
    print(path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
