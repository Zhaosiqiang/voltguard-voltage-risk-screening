| method                                          |    rmse |   coverage |   avg_width |   precision |   recall |   false_alarm_rate |   missed_violations |
|:------------------------------------------------|--------:|-----------:|------------:|------------:|---------:|-------------------:|--------------------:|
| Flat 1.0 p.u. + global quantile                 | 0.0329  |    0.90016 |     0.11745 |     0.15049 |  1       |            1       |                   0 |
| Historical bus envelope                         | 0.01258 |    0.95768 |     0.03499 |     0.35698 |  1       |            0.3191  |                   0 |
| Linear sensitivity regression + global quantile | 0.02052 |    0.90245 |     0.06683 |     0.24116 |  0.9924  |            0.55318 |                   7 |
| LinDistFlow + global quantile                   | 0.0014  |    0.91356 |     0.00474 |     0.97977 |  0.99891 |            0.00365 |                   1 |
