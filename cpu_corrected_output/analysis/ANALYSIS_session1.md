# Analysis: every number Chapter 4 is written from

Generated from `corr.db`. Single machine, CPU only.

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
| reference/vectorised | 0.00138 | 0.00015 | 10.8 | 0.00122 | 693.4 | 104.2 | 136 | 0.0778 |
| nest/threads4 | 0.00212 | 0.00017 | 8.1 | 0.01142 | 93.6 | 376.4 | 72 | 0.3358 |
| nest/threads2 | 0.00216 | 0.00011 | 5.1 | 0.01275 | 91.8 | 239.5 | 96 | 0.3397 |
| nest/threads1 | 0.00237 | 0.00028 | 11.7 | 0.01006 | 90.9 | 101.0 | 91 | 0.1315 |
| nengo/reference | 0.00501 | 0.00056 | 11.2 | 0.01174 | 640.7 | 100.6 | 134 | 0.2766 |
| spikingjelly/cpu | 0.00676 | 0.00043 | 6.3 | 0.00239 | 691.8 | 100.6 | 134 | 0.3748 |
| snntorch/cpu | 0.01442 | 0.00163 | 11.3 | 0.00198 | 687.9 | 100.3 | 134 | 0.7945 |
| reference/scalar | 0.01469 | 0.00050 | 3.4 | 0.00123 | 694.1 | 100.3 | 136 | 0.8097 |
| brian2/cython | 0.13358 | 0.00220 | 1.6 | 0.01220 | 639.8 | 100.0 | 108 | 7.3485 |
| brian2/numpy | 0.14266 | 0.01098 | 7.7 | 0.01070 | 628.8 | 100.0 | 108 | 7.8385 |
| brian2/cpp_standalone | 1.66947 | 0.06625 | 4.0 | 0.01140 | 638.7 | 794.1 | 105 | 734.7172 |

Spread across backends excluding the compile-dominated target: **103.72x** (0.14266 s / 0.00138 s).
Peak memory spread: **7.64x** (694.1 MB / 90.9 MB).

### Distributional checks on the raw runs

Chapter 3 specifies these before any parametric test. They are computable here because every individual run is stored.

| Backend | n | Shapiro-Wilk W | p | normal at 0.05 |
|---|---|---|---|---|
| brian2/cpp_standalone | 5 | 0.9498 | 0.7355 | yes |
| brian2/cython | 5 | 0.8340 | 0.1490 | yes |
| brian2/numpy | 5 | 0.9845 | 0.9572 | yes |
| nengo/reference | 5 | 0.8925 | 0.3697 | yes |
| nest/threads1 | 5 | 0.7615 | 0.0379 | no |
| nest/threads2 | 5 | 0.8932 | 0.3736 | yes |
| nest/threads4 | 5 | 0.9341 | 0.6243 | yes |
| reference/scalar | 5 | 0.9666 | 0.8529 | yes |
| reference/vectorised | 5 | 0.9641 | 0.8364 | yes |
| snntorch/cpu | 5 | 0.8811 | 0.3144 | yes |
| spikingjelly/cpu | 5 | 0.9401 | 0.6666 | yes |

Levene's test for homogeneity of variance across 11 backends: W = 6.35, p = 5.960e-06. Variances differ, so Welch's ANOVA is used.

Welch's one-way ANOVA across all backends: F(10, 17.22) = 1898.78, p = 3.931e-24, eta-squared = 0.9986.

#### Pairwise Welch comparisons, Holm-corrected

| Pair | t | p (raw) | p (Holm) | Cohen's d | separated |
|---|---|---|---|---|---|
| brian2/cython vs snntorch/cpu | 96.79 | 1.01e-12 | 5.53e-11 | 61.22 | yes |
| brian2/cython vs nengo/reference | 125.20 | 3.57e-09 | 1.93e-07 | 79.18 | yes |
| nengo/reference vs reference/scalar | -27.72 | 3.67e-09 | 1.94e-07 | -17.53 | yes |
| nest/threads1 vs reference/scalar | -46.86 | 3.69e-09 | 1.94e-07 | -29.64 | yes |
| brian2/cython vs reference/scalar | 116.69 | 7.04e-09 | 3.59e-07 | 73.80 | yes |
| reference/scalar vs spikingjelly/cpu | 26.10 | 7.19e-09 | 3.60e-07 | 16.51 | yes |
| brian2/cython vs spikingjelly/cpu | 125.20 | 7.92e-09 | 3.88e-07 | 79.18 | yes |
| brian2/cython vs nest/threads1 | 130.91 | 1.26e-08 | 6.07e-07 | 82.80 | yes |
| brian2/cython vs nest/threads4 | 131.99 | 1.65e-08 | 7.73e-07 | 83.48 | yes |
| brian2/cython vs reference/vectorised | 132.86 | 1.68e-08 | 7.73e-07 | 84.03 | yes |
| brian2/cython vs nest/threads2 | 132.17 | 1.82e-08 | 8.21e-07 | 83.59 | yes |
| nest/threads4 vs reference/scalar | -52.47 | 6.11e-08 | 2.69e-06 | -33.18 | yes |
| reference/scalar vs reference/vectorised | 56.37 | 7.96e-08 | 3.42e-06 | 35.65 | yes |
| nest/threads2 vs reference/scalar | -53.92 | 2.41e-07 | 1.01e-05 | -34.10 | yes |
| nest/threads1 vs spikingjelly/cpu | -19.00 | 3.52e-07 | 1.44e-05 | -12.02 | yes |
| brian2/cpp_standalone vs brian2/numpy | 51.53 | 4.55e-07 | 1.82e-05 | 32.59 | yes |
| brian2/cpp_standalone vs reference/vectorised | 56.99 | 5.68e-07 | 2.21e-05 | 36.04 | yes |
| brian2/cpp_standalone vs nest/threads4 | 56.97 | 5.69e-07 | 2.21e-05 | 36.03 | yes |
| brian2/cpp_standalone vs nest/threads2 | 56.96 | 5.69e-07 | 2.21e-05 | 36.03 | yes |
| brian2/cpp_standalone vs nest/threads1 | 56.95 | 5.69e-07 | 2.21e-05 | 36.02 | yes |
| brian2/cpp_standalone vs nengo/reference | 56.86 | 5.72e-07 | 2.21e-05 | 35.96 | yes |
| brian2/cpp_standalone vs spikingjelly/cpu | 56.80 | 5.75e-07 | 2.21e-05 | 35.93 | yes |
| brian2/cpp_standalone vs snntorch/cpu | 56.55 | 5.77e-07 | 2.21e-05 | 35.77 | yes |
| brian2/cpp_standalone vs reference/scalar | 56.54 | 5.85e-07 | 2.21e-05 | 35.76 | yes |
| brian2/cpp_standalone vs brian2/cython | 52.53 | 7.66e-07 | 2.37e-05 | 33.23 | yes |
| reference/vectorised vs spikingjelly/cpu | -27.28 | 1.37e-06 | 4.10e-05 | -17.25 | yes |
| nest/threads4 vs spikingjelly/cpu | -23.13 | 1.76e-06 | 5.10e-05 | -14.63 | yes |
| nest/threads2 vs spikingjelly/cpu | -23.87 | 6.29e-06 | 1.76e-04 | -15.10 | yes |
| brian2/numpy vs reference/vectorised | 28.73 | 8.71e-06 | 2.35e-04 | 18.17 | yes |
| brian2/numpy vs nest/threads4 | 28.57 | 8.89e-06 | 2.35e-04 | 18.07 | yes |
| brian2/numpy vs nest/threads2 | 28.57 | 8.92e-06 | 2.35e-04 | 18.07 | yes |
| brian2/numpy vs nest/threads1 | 28.48 | 8.94e-06 | 2.35e-04 | 18.01 | yes |
| brian2/numpy vs snntorch/cpu | 25.91 | 8.99e-06 | 2.35e-04 | 16.39 | yes |
| brian2/numpy vs nengo/reference | 27.90 | 9.36e-06 | 2.35e-04 | 17.65 | yes |
| brian2/numpy vs spikingjelly/cpu | 27.58 | 1.00e-05 | 2.35e-04 | 17.45 | yes |
| brian2/numpy vs reference/scalar | 26.00 | 1.25e-05 | 2.50e-04 | 16.45 | yes |
| nest/threads2 vs reference/vectorised | 9.85 | 1.73e-05 | 3.28e-04 | 6.23 | yes |
| nengo/reference vs reference/vectorised | 14.99 | 4.71e-05 | 8.48e-04 | 9.48 | yes |
| reference/vectorised vs snntorch/cpu | -17.00 | 6.25e-05 | 1.06e-03 | -10.75 | yes |
| nest/threads1 vs snntorch/cpu | -15.21 | 7.47e-05 | 1.19e-03 | -9.62 | yes |
| nest/threads4 vs reference/vectorised | 7.51 | 7.58e-05 | 1.19e-03 | 4.75 | yes |
| nest/threads4 vs snntorch/cpu | -15.94 | 7.81e-05 | 1.19e-03 | -10.08 | yes |
| nengo/reference vs nest/threads1 | 9.64 | 8.42e-05 | 1.19e-03 | 6.09 | yes |
| nest/threads2 vs snntorch/cpu | -15.92 | 8.56e-05 | 1.19e-03 | -10.07 | yes |
| nengo/reference vs nest/threads4 | 11.94 | 1.03e-04 | 1.19e-03 | 7.55 | yes |
| nengo/reference vs snntorch/cpu | -11.10 | 1.12e-04 | 1.19e-03 | -7.02 | yes |
| nest/threads1 vs reference/vectorised | 8.51 | 1.29e-04 | 1.19e-03 | 5.38 | yes |
| nengo/reference vs nest/threads2 | 12.05 | 1.78e-04 | 1.42e-03 | 7.62 | yes |
| snntorch/cpu vs spikingjelly/cpu | 9.18 | 4.18e-04 | 2.93e-03 | 5.81 | yes |
| nengo/reference vs spikingjelly/cpu | -5.18 | 1.04e-03 | 6.27e-03 | -3.28 | yes |
| nest/threads1 vs nest/threads4 | 2.99 | 2.16e-02 | 1.08e-01 | 1.89 | no |
| nest/threads1 vs nest/threads2 | 2.88 | 3.30e-02 | 1.32e-01 | 1.82 | no |
| brian2/cython vs brian2/numpy | -1.97 | 1.15e-01 | 3.46e-01 | -1.24 | no |
| reference/scalar vs snntorch/cpu | 1.03 | 3.53e-01 | 7.05e-01 | 0.65 | no |
| nest/threads2 vs nest/threads4 | 0.57 | 5.88e-01 | 7.05e-01 | 0.36 | no |

Pairs the data does not separate: nest/threads1 vs nest/threads4 (p = 0.108); nest/threads1 vs nest/threads2 (p = 0.132); brian2/cython vs brian2/numpy (p = 0.346); reference/scalar vs snntorch/cpu (p = 0.705); nest/threads2 vs nest/threads4 (p = 0.705). Report these as a failure to detect a difference, not as evidence of equivalence.

## Experiment 3: scalability

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | k | SE(k) | 95% CI | R2 |
|---|---|---|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 1.67823 | 1.66320 | 1.65968 | 1.65624 | 1.69111 | **0.001** | 0.003 | [-0.008, 0.009] | 0.013 |
| brian2/cython | 0.13373 | 0.13632 | 0.19428 | 0.16388 | 0.16518 | **0.048** | 0.040 | [-0.078, 0.175] | 0.330 |
| brian2/numpy | 0.12908 | 0.13475 | 0.14393 | 0.13838 | 0.14661 | **0.023** | 0.009 | [-0.005, 0.052] | 0.688 |
| nengo/reference | 0.00500 | 0.01215 | 0.12402 | 1.25233 | 4.52970 | **1.550** | 0.193 | [0.937, 2.164] | 0.956 |
| nest/threads1 | 0.00257 | 0.01276 | 0.02575 | 0.19788 | 0.68057 | **1.199** | 0.072 | [0.970, 1.427] | 0.989 |
| nest/threads2 | 0.00228 | 0.00941 | 0.01886 | 0.12935 | 0.49840 | **1.151** | 0.091 | [0.861, 1.441] | 0.982 |
| nest/threads4 | 0.00198 | 0.00804 | 0.01609 | 0.13401 | 0.50412 | **1.195** | 0.100 | [0.878, 1.512] | 0.980 |
| reference/scalar | 0.01532 | 0.07568 | 0.15032 | 0.73764 | 1.49235 | **0.993** | 0.002 | [0.987, 0.999] | 1.000 |
| reference/vectorised | 0.00133 | 0.00286 | 0.00500 | 0.01849 | 0.03749 | **0.735** | 0.059 | [0.548, 0.921] | 0.981 |
| snntorch/cpu | 0.01322 | 0.01925 | 0.02301 | 0.20705 | 0.76384 | **0.895** | 0.203 | [0.248, 1.543] | 0.866 |
| spikingjelly/cpu | 0.00690 | 0.01825 | 0.02649 | 0.21777 | 0.78418 | **1.026** | 0.140 | [0.579, 1.473] | 0.947 |

Steepest: nengo/reference at k = 1.550. Flattest: brian2/cpp_standalone at k = 0.001.

### Ranking at the extremes of the sweep

| Rank | Fastest at N=100 | s | Fastest at N=10000 | s |
|---|---|---|---|---|
| 1 | reference/vectorised | 0.00133 | reference/vectorised | 0.03749 |
| 2 | nest/threads4 | 0.00198 | brian2/numpy | 0.14661 |
| 3 | nest/threads2 | 0.00228 | brian2/cython | 0.16518 |
| 4 | nest/threads1 | 0.00257 | nest/threads2 | 0.49840 |
| 5 | nengo/reference | 0.00500 | nest/threads4 | 0.50412 |
| 6 | spikingjelly/cpu | 0.00690 | nest/threads1 | 0.68057 |
| 7 | snntorch/cpu | 0.01322 | snntorch/cpu | 0.76384 |
| 8 | reference/scalar | 0.01532 | spikingjelly/cpu | 0.78418 |
| 9 | brian2/numpy | 0.12908 | reference/scalar | 1.49235 |
| 10 | brian2/cython | 0.13373 | brian2/cpp_standalone | 1.69111 |
| 11 | brian2/cpp_standalone | 1.67823 | nengo/reference | 4.52970 |

The ranking reverses across the measured range.

### Peak process memory (MB)

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | growth |
|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 638.7 | 638.7 | 638.9 | 639.5 | 644.3 | 1.01x |
| brian2/cython | 639.8 | 639.8 | 639.8 | 639.8 | 644.1 | 1.01x |
| brian2/numpy | 628.8 | 629.4 | 630.2 | 635.2 | 641.7 | 1.02x |
| nengo/reference | 640.7 | 650.1 | 681.5 | 1059.4 | 2203.8 | 3.44x |
| nest/threads1 | 90.9 | 123.4 | 163.8 | 487.7 | 886.4 | 9.75x |
| nest/threads2 | 91.9 | 124.7 | 165.7 | 491.5 | 897.6 | 9.77x |
| nest/threads4 | 93.5 | 127.3 | 169.6 | 505.3 | 923.3 | 9.88x |
| reference/scalar | 694.1 | 694.1 | 694.1 | 694.3 | 694.4 | 1.00x |
| reference/vectorised | 693.4 | 693.4 | 693.5 | 694.2 | 694.1 | 1.00x |
| snntorch/cpu | 687.9 | 687.9 | 688.0 | 783.4 | 1069.5 | 1.55x |
| spikingjelly/cpu | 691.8 | 692.4 | 692.5 | 788.3 | 1074.9 | 1.55x |

## Energy proxy and RQ2

E = t x (u_cpu / 100) x 55 W

TDP source: Intel Core i9-14900HX processor base power, Intel ARK datasheet

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | (J) |
|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 726.886 | 728.924 | 728.617 | 727.280 | 722.790 | |
| brian2/cython | 7.357 | 7.500 | 10.687 | 9.016 | 9.087 | |
| brian2/numpy | 7.101 | 7.412 | 7.915 | 7.611 | 8.063 | |
| nengo/reference | 0.278 | 0.669 | 209.550 | 2177.966 | 7891.433 | |
| nest/threads1 | 0.143 | 0.703 | 1.417 | 10.884 | 37.433 | |
| nest/threads2 | 0.342 | 0.967 | 2.139 | 14.085 | 54.694 | |
| nest/threads4 | 0.415 | 1.751 | 3.510 | 29.266 | 110.781 | |
| reference/scalar | 0.845 | 4.163 | 8.271 | 40.567 | 82.073 | |
| reference/vectorised | 0.075 | 0.160 | 0.277 | 1.019 | 2.064 | |
| snntorch/cpu | 0.727 | 1.060 | 1.267 | 11.389 | 41.988 | |
| spikingjelly/cpu | 0.381 | 7.081 | 7.101 | 20.138 | 57.448 | |

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
| brian2/cpp_standalone | -0.40 | 0.5167 | yes |
| brian2/cython | 0.70 | 0.2333 | no |
| brian2/numpy | 0.90 | 0.0833 | no |
| nengo/reference | 1.00 | 0.0167 | no |
| nest/threads1 | 1.00 | 0.0167 | no |
| nest/threads2 | 1.00 | 0.0167 | no |
| nest/threads4 | 1.00 | 0.0167 | no |
| reference/scalar | 1.00 | 0.0167 | no |
| reference/vectorised | 1.00 | 0.0167 | no |
| snntorch/cpu | 1.00 | 0.0167 | no |
| spikingjelly/cpu | 1.00 | 0.0167 | no |

Pooled across compute-bound backends (50 runs): **rho = 0.769**, p = 6.73e-11.
