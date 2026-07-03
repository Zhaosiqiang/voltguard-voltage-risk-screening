| workflow                                        |   scenarios |    seconds |   ms_per_scenario |   speedup_vs_full_ac |
|:------------------------------------------------|------------:|-----------:|------------------:|---------------------:|
| VoltGuard online screening only                 |         120 |   0.030456 |          0.253799 |           6796.17    |
| Full AC grid search on every scenario           |         120 | 206.983    |       1724.86     |              1       |
| VoltGuard-flagged scenarios then AC grid search |          93 | 160.442    |       1725.19     |              1.29008 |
| VoltGuard top-20% budget then AC grid search    |          24 |  41.427    |       1726.13     |              4.99632 |
