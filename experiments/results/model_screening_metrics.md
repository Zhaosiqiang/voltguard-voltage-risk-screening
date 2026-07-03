| method                            | conformal_variant                |   precision |   recall |      f1 |   false_alarm_rate |   missed_violations |
|:----------------------------------|:---------------------------------|------------:|---------:|--------:|-------------------:|--------------------:|
| LinDistFlow physical backbone     | none                             |     1       |  0.9164  | 0.95637 |            0       |                  77 |
| Random forest                     | none                             |     0.9989  |  0.99023 | 0.99455 |            0.00019 |                   9 |
| Gradient boosting                 | none                             |     1       |  0.97286 | 0.98624 |            0       |                  25 |
| Boosting point + global conformal | global                           |     0.98604 |  0.99674 | 0.99136 |            0.0025  |                   3 |
| VoltGuard topology-aware residual | global                           |     0.99352 |  0.99891 | 0.99621 |            0.00115 |                   1 |
| VoltGuard topology-aware residual | pv_conditioned                   |     0.99675 |  0.99891 | 0.99783 |            0.00058 |                   1 |
| VoltGuard topology-aware residual | topology_conditioned             |     0.99138 |  0.99891 | 0.99513 |            0.00154 |                   1 |
| VoltGuard topology-aware residual | topology_pv_loading_conditioned  |     0.99675 |  0.99891 | 0.99783 |            0.00058 |                   1 |
| VoltGuard topology-aware residual | topology_pv_loading_no_shrinkage |     0.99783 |  0.99891 | 0.99837 |            0.00038 |                   1 |
| Neural graph residual ablation    | topology_conditioned             |     0.88365 |  0.99783 | 0.93728 |            0.02327 |                   2 |
