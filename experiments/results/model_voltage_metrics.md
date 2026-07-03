| method                            | conformal_variant                |     mae |    rmse |   max_abs_error |   coverage |   avg_width |
|:----------------------------------|:---------------------------------|--------:|--------:|----------------:|-----------:|------------:|
| LinDistFlow physical backbone     | none                             | 0.00092 | 0.0014  |         0.00661 |  nan       |   nan       |
| Random forest                     | none                             | 0.00014 | 0.00023 |         0.00224 |  nan       |   nan       |
| Gradient boosting                 | none                             | 0.00029 | 0.00041 |         0.00588 |  nan       |   nan       |
| Boosting point + global conformal | global                           | 0.00029 | 0.00041 |         0.00588 |    0.9085  |     0.0011  |
| VoltGuard topology-aware residual | global                           | 7e-05   | 0.00011 |         0.00083 |    0.94984 |     0.00053 |
| VoltGuard topology-aware residual | pv_conditioned                   | 7e-05   | 0.00011 |         0.00083 |    0.9451  |     0.00049 |
| VoltGuard topology-aware residual | topology_conditioned             | 7e-05   | 0.00011 |         0.00083 |    0.95523 |     0.00053 |
| VoltGuard topology-aware residual | topology_pv_loading_conditioned  | 7e-05   | 0.00011 |         0.00083 |    0.9366  |     0.00043 |
| VoltGuard topology-aware residual | topology_pv_loading_no_shrinkage | 7e-05   | 0.00011 |         0.00083 |    0.91258 |     0.00042 |
| Neural graph residual ablation    | topology_conditioned             | 0.0013  | 0.00171 |         0.00966 |    0.9134  |     0.0054  |
