# EV-Conditioning Sample-Size Outlook

This supplementary table is an outlook derived from the executed
EV-conditioning ablation, not a new performance experiment. The current
topology+PV+loading+EV key has 55 families, a weakest-family calibration count
of 33, and seven empty test families. The primary topology+PV+loading key has
16 families and a weakest-family calibration count of 198.

| Calibration scale relative to current EV-conditioned split | Current min EV-family calibration samples | Approx. min EV-family calibration samples | Expected status |
|---:|---:|---:|---|
| 1x | 33 | 33 | Fragmented; no recall gain observed and intervals are wider |
| 2x | 33 | 66 | Still below primary-family support; diagnostic use only |
| 4x | 33 | 132 | Candidate regime for retesting EV-conditioned intervals |
| 6x | 33 | 198 | Comparable weakest-family support to topology+PV+loading |
| 8x | 33 | 264 | Plausible regime if width and false alarms begin to fall |

The table supports a conservative interpretation: EV scale is useful as a
point-estimator feature in the current experiments, but EV-conditioned
calibration should be retested only after the weakest EV-conditioned family has
substantially more calibration support.
