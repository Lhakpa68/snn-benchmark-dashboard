# Analysis: every number Chapter 4 is written from

Generated from `benchmarks.db`. Single machine, CPU only.

## Measurement machine

| Property | Value |
|---|---|
| hostname | LT68 |
| os | Linux 6.18.33.2-microsoft-standard-WSL2 |
| arch | x86_64 |
| cpu | Intel(R) Core(TM) i9-14900HX |
| logical_cores | 32 |
| ram_gb | 11.5 |
| python | 3.11.15 |
| wsl | True |
| accelerator | CPU only |

## Package versions, captured at run time

| Package | Version |
|---|---|
| numpy | 2.4.6 |
| scipy | 1.17.1 |
| brian2 | 2.9.0 |
| nest | 3.10.0 |
| nengo | 4.1.0 |
| snntorch | 1.0.0 |
| torch | 2.13.0+cu130 |
| spikingjelly | present |
| cython | 3.2.9 |
| psutil | 7.2.2 |

## Experiment 1: inference at N = 100

Setup and simulation are timed separately, so a simulator that is slow to build is distinguishable from one that is slow to run.

| Backend | Simulate median (s) | SD | CV (%) | Setup median (s) | Peak RSS (MB) | CPU (%) | Spikes | Energy (J) |
|---|---|---|---|---|---|---|---|---|
| reference/vectorised | 0.00130 | 0.00015 | 11.7 | 0.00148 | 695.7 | 103.3 | 136 | 0.0750 |
| nest/threads2 | 0.00213 | 0.00043 | 20.1 | 0.01071 | 91.9 | 208.4 | 96 | 0.2280 |
| nest/threads4 | 0.00220 | 0.00038 | 17.3 | 0.01053 | 93.6 | 521.3 | 72 | 0.5717 |
| nest/threads1 | 0.00245 | 0.00031 | 12.7 | 0.01029 | 91.0 | 100.7 | 91 | 0.1356 |
| nengo/reference | 0.00476 | 0.00037 | 7.8 | 0.01173 | 641.6 | 100.4 | 134 | 0.2626 |
| spikingjelly/cpu | 0.00991 | 0.00122 | 12.3 | 0.00280 | 694.0 | 100.6 | 134 | 0.5467 |
| snntorch/cpu | 0.01307 | 0.00093 | 7.1 | 0.00274 | 690.3 | 100.2 | 134 | 0.7205 |
| reference/scalar | 0.01597 | 0.00077 | 4.8 | 0.00129 | 696.4 | 100.3 | 136 | 0.8804 |
| brian2/numpy | 0.13318 | 0.00704 | 5.3 | 0.01108 | 631.3 | 100.0 | 108 | 7.3271 |
| brian2/cython | 0.13933 | 0.01090 | 7.8 | 0.01204 | 638.8 | 100.0 | 108 | 7.6642 |
| brian2/cpp_standalone | 1.70039 | 0.15243 | 9.0 | 0.01367 | 642.8 | 780.5 | 91 | 737.1170 |

Spread across backends excluding the compile-dominated target: **106.88x** (0.13933 s / 0.00130 s).
Peak memory spread: **7.66x** (696.4 MB / 91.0 MB).

### Distributional checks on the raw runs

Chapter 3 specifies these before any parametric test. They are computable here because every individual run is stored.

| Backend | n | Shapiro-Wilk W | p | normal at 0.05 |
|---|---|---|---|---|
| brian2/cpp_standalone | 5 | 0.8992 | 0.4055 | yes |
| brian2/cython | 5 | 0.7905 | 0.0677 | yes |
| brian2/numpy | 5 | 0.6884 | 0.0072 | no |
| nengo/reference | 5 | 0.9267 | 0.5742 | yes |
| nest/threads1 | 5 | 0.8310 | 0.1415 | yes |
| nest/threads2 | 5 | 0.6877 | 0.0071 | no |
| nest/threads4 | 5 | 0.9865 | 0.9659 | yes |
| reference/scalar | 5 | 0.8510 | 0.1976 | yes |
| reference/vectorised | 5 | 0.9689 | 0.8681 | yes |
| snntorch/cpu | 5 | 0.8748 | 0.2865 | yes |
| spikingjelly/cpu | 5 | 0.8317 | 0.1433 | yes |

Levene's test for homogeneity of variance across 11 backends: W = 9.38, p = 4.285e-08. Variances differ, so Welch's ANOVA is used.

Welch's one-way ANOVA across all backends: F(10, 17.10) = 451.58, p = 1.143e-18, eta-squared = 0.9930.

#### Pairwise Welch comparisons, Holm-corrected

| Pair | t | p (raw) | p (Holm) | Cohen's d | separated |
|---|---|---|---|---|---|
| nest/threads2 vs reference/scalar | -34.16 | 2.38e-08 | 1.31e-06 | -21.61 | yes |
| nest/threads4 vs reference/scalar | -35.48 | 4.69e-08 | 2.53e-06 | -22.44 | yes |
| nest/threads1 vs reference/scalar | -35.61 | 1.72e-07 | 9.11e-06 | -22.52 | yes |
| nengo/reference vs reference/scalar | -28.58 | 1.97e-07 | 1.02e-05 | -18.07 | yes |
| nest/threads2 vs snntorch/cpu | -23.31 | 8.53e-07 | 4.35e-05 | -14.74 | yes |
| reference/scalar vs reference/vectorised | 41.31 | 9.00e-07 | 4.50e-05 | 26.13 | yes |
| nest/threads4 vs snntorch/cpu | -24.12 | 1.28e-06 | 6.29e-05 | -15.25 | yes |
| brian2/numpy vs spikingjelly/cpu | 39.54 | 1.31e-06 | 6.30e-05 | 25.01 | yes |
| brian2/numpy vs nest/threads2 | 42.28 | 1.73e-06 | 8.13e-05 | 26.74 | yes |
| brian2/numpy vs nest/threads4 | 42.35 | 1.75e-06 | 8.13e-05 | 26.79 | yes |
| brian2/numpy vs reference/vectorised | 42.68 | 1.78e-06 | 8.13e-05 | 26.99 | yes |
| brian2/numpy vs nest/threads1 | 42.25 | 1.80e-06 | 8.13e-05 | 26.72 | yes |
| brian2/numpy vs snntorch/cpu | 38.62 | 1.87e-06 | 8.13e-05 | 24.43 | yes |
| brian2/numpy vs nengo/reference | 41.50 | 1.90e-06 | 8.13e-05 | 26.25 | yes |
| brian2/numpy vs reference/scalar | 37.87 | 2.28e-06 | 9.34e-05 | 23.95 | yes |
| nest/threads1 vs snntorch/cpu | -23.79 | 3.11e-06 | 1.24e-04 | -15.05 | yes |
| nengo/reference vs nest/threads4 | 11.38 | 3.23e-06 | 1.26e-04 | 7.20 | yes |
| nengo/reference vs reference/vectorised | 19.92 | 3.34e-06 | 1.27e-04 | 12.60 | yes |
| reference/vectorised vs snntorch/cpu | -27.76 | 6.22e-06 | 2.30e-04 | -17.56 | yes |
| nengo/reference vs snntorch/cpu | -18.19 | 6.26e-06 | 2.30e-04 | -11.51 | yes |
| nengo/reference vs nest/threads1 | 10.62 | 6.73e-06 | 2.36e-04 | 6.72 | yes |
| brian2/cython vs reference/vectorised | 29.60 | 7.73e-06 | 2.63e-04 | 18.72 | yes |
| brian2/cython vs nest/threads2 | 29.37 | 7.78e-06 | 2.63e-04 | 18.57 | yes |
| brian2/cython vs nest/threads4 | 29.41 | 7.78e-06 | 2.63e-04 | 18.60 | yes |
| brian2/cython vs nest/threads1 | 29.33 | 7.93e-06 | 2.63e-04 | 18.55 | yes |
| brian2/cython vs spikingjelly/cpu | 27.78 | 7.98e-06 | 2.63e-04 | 17.57 | yes |
| brian2/cython vs nengo/reference | 28.85 | 8.41e-06 | 2.63e-04 | 18.25 | yes |
| brian2/cython vs snntorch/cpu | 27.09 | 9.69e-06 | 2.71e-04 | 17.13 | yes |
| nengo/reference vs nest/threads2 | 10.00 | 9.78e-06 | 2.71e-04 | 6.32 | yes |
| brian2/cython vs reference/scalar | 26.56 | 1.09e-05 | 2.84e-04 | 16.80 | yes |
| brian2/cpp_standalone vs reference/vectorised | 25.43 | 1.42e-05 | 3.55e-04 | 16.08 | yes |
| brian2/cpp_standalone vs nest/threads4 | 25.42 | 1.42e-05 | 3.55e-04 | 16.07 | yes |
| brian2/cpp_standalone vs nest/threads2 | 25.41 | 1.42e-05 | 3.55e-04 | 16.07 | yes |
| brian2/cpp_standalone vs nest/threads1 | 25.41 | 1.42e-05 | 3.55e-04 | 16.07 | yes |
| brian2/cpp_standalone vs nengo/reference | 25.38 | 1.43e-05 | 3.55e-04 | 16.05 | yes |
| brian2/cpp_standalone vs spikingjelly/cpu | 25.31 | 1.45e-05 | 3.55e-04 | 16.01 | yes |
| brian2/cpp_standalone vs snntorch/cpu | 25.26 | 1.46e-05 | 3.55e-04 | 15.97 | yes |
| brian2/cpp_standalone vs reference/scalar | 25.22 | 1.47e-05 | 3.55e-04 | 15.95 | yes |
| brian2/cpp_standalone vs brian2/cython | 23.25 | 1.86e-05 | 3.55e-04 | 14.71 | yes |
| brian2/cpp_standalone vs brian2/numpy | 23.43 | 1.90e-05 | 3.55e-04 | 14.82 | yes |
| reference/scalar vs spikingjelly/cpu | 9.96 | 2.83e-05 | 4.25e-04 | 6.30 | yes |
| nest/threads2 vs spikingjelly/cpu | -12.11 | 7.13e-05 | 9.98e-04 | -7.66 | yes |
| nest/threads4 vs spikingjelly/cpu | -12.55 | 7.80e-05 | 1.01e-03 | -7.94 | yes |
| reference/vectorised vs spikingjelly/cpu | -14.62 | 1.04e-04 | 1.25e-03 | -9.25 | yes |
| nest/threads1 vs spikingjelly/cpu | -12.02 | 1.34e-04 | 1.47e-03 | -7.60 | yes |
| nest/threads1 vs reference/vectorised | 8.21 | 2.06e-04 | 2.06e-03 | 5.19 | yes |
| nengo/reference vs spikingjelly/cpu | -7.84 | 6.95e-04 | 6.26e-03 | -4.96 | yes |
| snntorch/cpu vs spikingjelly/cpu | 5.37 | 8.33e-04 | 6.67e-03 | 3.40 | yes |
| reference/scalar vs snntorch/cpu | 5.05 | 1.10e-03 | 7.69e-03 | 3.20 | yes |
| nest/threads2 vs reference/vectorised | 5.14 | 3.64e-03 | 2.18e-02 | 3.25 | yes |
| nest/threads4 vs reference/vectorised | 4.73 | 4.55e-03 | 2.27e-02 | 2.99 | yes |
| nest/threads1 vs nest/threads4 | 1.84 | 1.05e-01 | 4.19e-01 | 1.16 | no |
| brian2/cython vs brian2/numpy | 1.70 | 1.35e-01 | 4.19e-01 | 1.07 | no |
| nest/threads1 vs nest/threads2 | 0.97 | 3.61e-01 | 7.23e-01 | 0.62 | no |
| nest/threads2 vs nest/threads4 | 0.68 | 5.16e-01 | 7.23e-01 | 0.43 | no |

Pairs the data does not separate: nest/threads1 vs nest/threads4 (p = 0.419); brian2/cython vs brian2/numpy (p = 0.419); nest/threads1 vs nest/threads2 (p = 0.723); nest/threads2 vs nest/threads4 (p = 0.723). Report these as a failure to detect a difference, not as evidence of equivalence.

## Experiment 3: scalability

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | k | SE(k) | 95% CI | R2 |
|---|---|---|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 1.78560 | 1.89787 | 1.99656 | 1.79876 | 2.12605 | **0.023** | 0.019 | [-0.038, 0.083] | 0.322 |
| brian2/cython | 0.13762 | 0.14830 | 0.13828 | 0.14731 | 0.14853 | **0.014** | 0.009 | [-0.014, 0.043] | 0.454 |
| brian2/numpy | 0.13582 | 0.13848 | 0.13988 | 0.14211 | 0.14868 | **0.017** | 0.004 | [0.005, 0.030] | 0.869 |
| nengo/reference | 0.00446 | 0.01237 | 0.20652 | 1.18957 | 4.15104 | **1.544** | 0.209 | [0.879, 2.210] | 0.948 |
| nest/threads1 | 0.00245 | 0.01363 | 0.02808 | 0.16611 | 0.58103 | **1.159** | 0.057 | [0.979, 1.339] | 0.993 |
| nest/threads2 | 0.00207 | 0.00824 | 0.01770 | 0.11870 | 0.40209 | **1.135** | 0.079 | [0.883, 1.387] | 0.986 |
| nest/threads4 | 0.00182 | 0.00778 | 0.01422 | 0.10609 | 0.35302 | **1.133** | 0.082 | [0.872, 1.395] | 0.984 |
| reference/scalar | 0.01610 | 0.07404 | 0.15375 | 0.72940 | 1.48016 | **0.982** | 0.007 | [0.959, 1.006] | 1.000 |
| reference/vectorised | 0.00131 | 0.00308 | 0.00509 | 0.01998 | 0.03572 | **0.732** | 0.047 | [0.582, 0.882] | 0.988 |
| snntorch/cpu | 0.01243 | 0.01570 | 0.02243 | 0.20586 | 0.77200 | **0.921** | 0.212 | [0.245, 1.597] | 0.862 |
| spikingjelly/cpu | 0.00915 | 0.02040 | 0.02563 | 0.21119 | 0.76422 | **0.960** | 0.160 | [0.450, 1.470] | 0.923 |

Steepest: nengo/reference at k = 1.544. Flattest: brian2/cython at k = 0.014.

### Ranking at the extremes of the sweep

| Rank | Fastest at N=100 | s | Fastest at N=10000 | s |
|---|---|---|---|---|
| 1 | reference/vectorised | 0.00131 | reference/vectorised | 0.03572 |
| 2 | nest/threads4 | 0.00182 | brian2/cython | 0.14853 |
| 3 | nest/threads2 | 0.00207 | brian2/numpy | 0.14868 |
| 4 | nest/threads1 | 0.00245 | nest/threads4 | 0.35302 |
| 5 | nengo/reference | 0.00446 | nest/threads2 | 0.40209 |
| 6 | spikingjelly/cpu | 0.00915 | nest/threads1 | 0.58103 |
| 7 | snntorch/cpu | 0.01243 | spikingjelly/cpu | 0.76422 |
| 8 | reference/scalar | 0.01610 | snntorch/cpu | 0.77200 |
| 9 | brian2/numpy | 0.13582 | reference/scalar | 1.48016 |
| 10 | brian2/cython | 0.13762 | brian2/cpp_standalone | 2.12605 |
| 11 | brian2/cpp_standalone | 1.78560 | nengo/reference | 4.15104 |

The ranking reverses across the measured range.

### Peak process memory (MB)

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | growth |
|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 642.8 | 642.8 | 642.9 | 643.4 | 646.8 | 1.01x |
| brian2/cython | 638.8 | 638.8 | 638.8 | 640.9 | 646.8 | 1.01x |
| brian2/numpy | 631.4 | 631.9 | 632.7 | 637.8 | 644.7 | 1.02x |
| nengo/reference | 641.6 | 651.4 | 683.1 | 1061.7 | 2206.1 | 3.44x |
| nest/threads1 | 91.0 | 123.4 | 163.9 | 487.8 | 891.3 | 9.79x |
| nest/threads2 | 92.0 | 124.6 | 165.8 | 494.0 | 897.8 | 9.76x |
| nest/threads4 | 93.6 | 127.1 | 169.5 | 506.7 | 925.0 | 9.89x |
| reference/scalar | 696.4 | 696.4 | 696.4 | 696.6 | 696.7 | 1.00x |
| reference/vectorised | 695.7 | 695.7 | 695.7 | 696.5 | 696.4 | 1.00x |
| snntorch/cpu | 690.3 | 690.3 | 690.4 | 785.7 | 1071.8 | 1.55x |
| spikingjelly/cpu | 694.0 | 694.7 | 694.7 | 790.5 | 1077.2 | 1.55x |

## Energy proxy and RQ2

E = t x (u_cpu / 100) x 55 W

TDP source: Intel Core i9-14900HX processor base power, Intel ARK datasheet

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | (J) |
|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 746.957 | 722.879 | 674.182 | 700.751 | 702.013 | |
| brian2/cython | 7.572 | 8.158 | 7.607 | 8.103 | 8.169 | |
| brian2/numpy | 7.471 | 7.618 | 7.696 | 7.817 | 8.178 | |
| nengo/reference | 0.246 | 0.682 | 356.140 | 2070.278 | 7257.400 | |
| nest/threads1 | 0.136 | 0.751 | 1.545 | 9.137 | 31.957 | |
| nest/threads2 | 0.341 | 0.894 | 1.855 | 13.128 | 44.335 | |
| nest/threads4 | 0.510 | 1.748 | 3.419 | 22.996 | 78.156 | |
| reference/scalar | 0.888 | 4.076 | 8.458 | 40.027 | 81.397 | |
| reference/vectorised | 0.074 | 0.173 | 0.282 | 1.101 | 1.969 | |
| snntorch/cpu | 0.687 | 0.865 | 1.234 | 11.326 | 41.815 | |
| spikingjelly/cpu | 0.505 | 7.036 | 8.391 | 18.745 | 55.570 | |

### Effective operation count for the model

| N | EFLOP | measured output spikes (median across backends) |
|---|---|---|
| 100 | 11,000 | 108 |
| 500 | 55,000 | 535 |
| 1000 | 110,000 | 1007 |
| 5000 | 550,000 | 5220 |
| 10000 | 1,100,000 | 10509 |

### Rank agreement between the proxy and EFLOP

| Backend | rho | exact p | compile-dominated |
|---|---|---|---|
| brian2/cpp_standalone | -0.60 | 0.3500 | yes |
| brian2/cython | 0.70 | 0.2333 | no |
| brian2/numpy | 1.00 | 0.0167 | no |
| nengo/reference | 1.00 | 0.0167 | no |
| nest/threads1 | 1.00 | 0.0167 | no |
| nest/threads2 | 1.00 | 0.0167 | no |
| nest/threads4 | 1.00 | 0.0167 | no |
| reference/scalar | 1.00 | 0.0167 | no |
| reference/vectorised | 1.00 | 0.0167 | no |
| snntorch/cpu | 1.00 | 0.0167 | no |
| spikingjelly/cpu | 1.00 | 0.0167 | no |

Pooled across compute-bound backends (50 runs): **rho = 0.771**, p = 5.62e-11.

## Experiment 2: training

| Simulator / backend | Hidden | s per epoch | Accuracy (%) | Note |
|---|---|---|---|---|
| nengo/reference | 256 | 2.90 | 85.44 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=65.2; util_wall_s=2.9; NEF decoder |
| spikingjelly/cpu | 256 | 89.94 | 97.46 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=894.9; util_wall_s=899.4; Surrogat |
| snntorch/cpu | 256 | 90.94 | 97.24 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=906.2; util_wall_s=909.4; Surrogat |
| nest/threads4 | 256 | 1361.71 | 8.32 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=47517.7; util_wall_s=13617.1; STDP |
| nest/threads2 | 256 | 2381.81 | 8.24 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=45382.8; util_wall_s=23818.1; STDP |
| nest/threads1 | 256 | 4403.12 | 8.50 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=44011.6; util_wall_s=44031.2; STDP |
| brian2/cython | 256 | 10166.92 | 9.61 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=101664.5; util_wall_s=101671.1; Un |
| brian2/numpy | 256 | 14176.67 | 9.61 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=141754.0; util_wall_s=141768.8; Un |
| brian2/cpp_standalone | 256 | 14852.06 | 9.57 | preset=full; hidden=256; train_n=60000; test_n=10000; epochs=10; util_cpu_s=148507.1; util_wall_s=148523.0; Un |

Chance accuracy on 10 classes is 10%. Simulators at or near chance are reporting the sample budget, not their learning capability.
