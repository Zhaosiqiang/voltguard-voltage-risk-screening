| method                            | variant                         |   scenarios |   drop_rmse_mean |   drop_rmse_std |   drop_mae_mean |   drop_max_abs_p95 |   violating_only_drop_rmse |
|:----------------------------------|:--------------------------------|------------:|-----------------:|----------------:|----------------:|-------------------:|---------------------------:|
| AC power-flow label               | reference                       |         120 |         0.000238 |        0.000124 |        0.000101 |           0.002516 |                   0.000272 |
| Boosting point + global conformal | global                          |         120 |         0.000563 |        0.000331 |        0.000379 |           0.004631 |                   0.000621 |
| Neural graph residual ablation    | topology_conditioned            |         120 |         0.003139 |        0.001289 |        0.002437 |           0.014201 |                   0.002904 |
| VoltGuard topology-aware residual | topology_pv_loading_conditioned |         120 |         0.00025  |        0.00013  |        0.000122 |           0.002395 |                   0.000279 |
