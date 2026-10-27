# Analysis: every number Chapter 4 is written from

Generated from `corr2.db`. Single machine, CPU only.

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
| reference/vectorised | 0.00138 | 0.00004 | 3.0 | 0.00153 | 695.7 | 104.0 | 136 | 0.0780 |
| nest/threads4 | 0.00224 | 0.00018 | 8.1 | 0.01194 | 93.5 | 447.3 | 72 | 0.5058 |
| nest/threads2 | 0.00233 | 0.00009 | 3.8 | 0.01223 | 91.9 | 246.3 | 96 | 0.3461 |
| nest/threads1 | 0.00281 | 0.00025 | 8.8 | 0.01281 | 90.9 | 100.9 | 91 | 0.1568 |
| nengo/reference | 0.00507 | 0.00048 | 9.5 | 0.01205 | 641.4 | 100.9 | 134 | 0.2814 |
| spikingjelly/cpu | 0.00673 | 0.00054 | 8.0 | 0.00220 | 694.0 | 100.6 | 134 | 0.3719 |
| snntorch/cpu | 0.01390 | 0.00088 | 6.4 | 0.00245 | 690.3 | 100.2 | 134 | 0.7664 |
| reference/scalar | 0.01498 | 0.00051 | 3.4 | 0.00148 | 696.3 | 100.3 | 136 | 0.8264 |
| brian2/cython | 0.15136 | 0.00931 | 6.1 | 0.01241 | 638.7 | 100.0 | 108 | 8.3253 |
| brian2/numpy | 0.15904 | 0.00511 | 3.2 | 0.01123 | 631.2 | 99.5 | 108 | 8.5354 |
| brian2/cpp_standalone | 1.72174 | 0.01741 | 1.0 | 0.01274 | 639.5 | 791.4 | 90 | 743.8223 |

Spread across backends excluding the compile-dominated target: **115.34x** (0.15904 s / 0.00138 s).
Peak memory spread: **7.66x** (696.3 MB / 90.9 MB).

### Distributional checks on the raw runs

Chapter 3 specifies these before any parametric test. They are computable here because every individual run is stored.

| Backend | n | Shapiro-Wilk W | p | normal at 0.05 |
|---|---|---|---|---|
| brian2/cpp_standalone | 5 | 0.9027 | 0.4248 | yes |
| brian2/cython | 5 | 0.9018 | 0.4200 | yes |
| brian2/numpy | 5 | 0.9138 | 0.4909 | yes |
| nengo/reference | 5 | 0.8386 | 0.1612 | yes |
| nest/threads1 | 5 | 0.9183 | 0.5192 | yes |
| nest/threads2 | 5 | 0.9540 | 0.7657 | yes |
| nest/threads4 | 5 | 0.8736 | 0.2812 | yes |
| reference/scalar | 5 | 0.9057 | 0.4422 | yes |
| reference/vectorised | 5 | 0.9479 | 0.7222 | yes |
| snntorch/cpu | 5 | 0.8850 | 0.3327 | yes |
| spikingjelly/cpu | 5 | 0.9408 | 0.6714 | yes |

Levene's test for homogeneity of variance across 11 backends: W = 8.35, p = 2.058e-07. Variances differ, so Welch's ANOVA is used.

Welch's one-way ANOVA across all backends: F(10, 16.67) = 4435.08, p = 1.605e-26, eta-squared = 0.9999.

#### Pairwise Welch comparisons, Holm-corrected

| Pair | t | p (raw) | p (Holm) | Cohen's d | separated |
|---|---|---|---|---|---|
| brian2/cpp_standalone vs brian2/cython | 177.30 | 1.41e-12 | 7.73e-11 | 112.14 | yes |
| brian2/cpp_standalone vs brian2/numpy | 192.06 | 2.62e-10 | 1.42e-08 | 121.47 | yes |
| nengo/reference vs reference/scalar | -31.46 | 1.17e-09 | 6.23e-08 | -19.89 | yes |
| brian2/cpp_standalone vs snntorch/cpu | 218.52 | 2.41e-09 | 1.25e-07 | 138.20 | yes |
| brian2/cpp_standalone vs spikingjelly/cpu | 219.64 | 2.49e-09 | 1.27e-07 | 138.91 | yes |
| brian2/cpp_standalone vs nengo/reference | 219.85 | 2.50e-09 | 1.27e-07 | 139.05 | yes |
| brian2/cpp_standalone vs nest/threads1 | 220.19 | 2.53e-09 | 1.27e-07 | 139.26 | yes |
| brian2/cpp_standalone vs nest/threads4 | 220.28 | 2.54e-09 | 1.27e-07 | 139.32 | yes |
| brian2/cpp_standalone vs reference/vectorised | 220.41 | 2.54e-09 | 1.27e-07 | 139.40 | yes |
| brian2/cpp_standalone vs nest/threads2 | 220.29 | 2.55e-09 | 1.27e-07 | 139.32 | yes |
| brian2/cpp_standalone vs reference/scalar | 218.58 | 2.55e-09 | 1.27e-07 | 138.24 | yes |
| reference/scalar vs spikingjelly/cpu | 25.15 | 7.12e-09 | 3.13e-07 | 15.91 | yes |
| nest/threads1 vs reference/scalar | -47.65 | 9.57e-09 | 4.12e-07 | -30.14 | yes |
| nest/threads4 vs reference/scalar | -52.35 | 4.68e-08 | 1.97e-06 | -33.11 | yes |
| brian2/numpy vs snntorch/cpu | 62.60 | 1.89e-07 | 7.75e-06 | 39.59 | yes |
| brian2/numpy vs spikingjelly/cpu | 66.39 | 2.33e-07 | 9.34e-06 | 41.99 | yes |
| brian2/numpy vs nengo/reference | 67.12 | 2.36e-07 | 9.34e-06 | 42.45 | yes |
| brian2/numpy vs nest/threads1 | 68.28 | 2.60e-07 | 9.88e-06 | 43.18 | yes |
| brian2/numpy vs nest/threads4 | 68.57 | 2.63e-07 | 9.88e-06 | 43.37 | yes |
| brian2/numpy vs reference/vectorised | 69.02 | 2.64e-07 | 9.88e-06 | 43.65 | yes |
| brian2/numpy vs nest/threads2 | 68.60 | 2.68e-07 | 9.88e-06 | 43.39 | yes |
| brian2/numpy vs reference/scalar | 62.80 | 3.03e-07 | 1.03e-05 | 39.72 | yes |
| nest/threads2 vs reference/scalar | -54.75 | 3.26e-07 | 1.07e-05 | -34.63 | yes |
| reference/scalar vs reference/vectorised | 59.52 | 4.05e-07 | 1.30e-05 | 37.65 | yes |
| nengo/reference vs snntorch/cpu | -19.72 | 7.95e-07 | 2.47e-05 | -12.47 | yes |
| nest/threads2 vs reference/vectorised | 21.33 | 1.22e-06 | 3.65e-05 | 13.49 | yes |
| snntorch/cpu vs spikingjelly/cpu | 15.91 | 1.57e-06 | 4.56e-05 | 10.06 | yes |
| nest/threads1 vs snntorch/cpu | -26.91 | 2.95e-06 | 8.27e-05 | -17.02 | yes |
| brian2/cython vs reference/vectorised | 36.24 | 3.46e-06 | 9.34e-05 | 22.92 | yes |
| brian2/cython vs nest/threads4 | 36.01 | 3.52e-06 | 9.34e-05 | 22.78 | yes |
| brian2/cython vs nest/threads2 | 36.02 | 3.54e-06 | 9.34e-05 | 22.78 | yes |
| brian2/cython vs nest/threads1 | 35.87 | 3.56e-06 | 9.34e-05 | 22.68 | yes |
| brian2/cython vs nengo/reference | 35.31 | 3.64e-06 | 9.34e-05 | 22.33 | yes |
| brian2/cython vs spikingjelly/cpu | 34.94 | 3.75e-06 | 9.34e-05 | 22.10 | yes |
| nest/threads4 vs snntorch/cpu | -28.82 | 4.04e-06 | 9.34e-05 | -18.23 | yes |
| brian2/cython vs snntorch/cpu | 33.08 | 4.19e-06 | 9.34e-05 | 20.92 | yes |
| brian2/cython vs reference/scalar | 32.95 | 4.78e-06 | 9.34e-05 | 20.84 | yes |
| reference/vectorised vs snntorch/cpu | -31.75 | 5.62e-06 | 1.01e-04 | -20.08 | yes |
| nest/threads2 vs snntorch/cpu | -29.26 | 6.74e-06 | 1.15e-04 | -18.51 | yes |
| nest/threads1 vs spikingjelly/cpu | -13.77 | 1.58e-05 | 2.53e-04 | -8.71 | yes |
| nest/threads4 vs spikingjelly/cpu | -16.66 | 1.71e-05 | 2.57e-04 | -10.53 | yes |
| reference/vectorised vs spikingjelly/cpu | -21.35 | 2.59e-05 | 3.62e-04 | -13.50 | yes |
| nest/threads2 vs spikingjelly/cpu | -17.31 | 4.46e-05 | 5.80e-04 | -10.95 | yes |
| nengo/reference vs reference/vectorised | 16.96 | 6.39e-05 | 7.66e-04 | 10.72 | yes |
| nengo/reference vs nest/threads4 | 11.89 | 6.47e-05 | 7.66e-04 | 7.52 | yes |
| nengo/reference vs nest/threads1 | 8.89 | 1.18e-04 | 1.18e-03 | 5.62 | yes |
| nest/threads1 vs reference/vectorised | 13.59 | 1.20e-04 | 1.18e-03 | 8.59 | yes |
| nengo/reference vs nest/threads2 | 12.47 | 1.61e-04 | 1.29e-03 | 7.89 | yes |
| nest/threads4 vs reference/vectorised | 11.21 | 2.05e-04 | 1.44e-03 | 7.09 | yes |
| nengo/reference vs spikingjelly/cpu | -4.65 | 1.71e-03 | 1.03e-02 | -2.94 | yes |
| nest/threads1 vs nest/threads4 | 4.29 | 3.22e-03 | 1.61e-02 | 2.72 | yes |
| nest/threads1 vs nest/threads2 | 4.97 | 4.16e-03 | 1.66e-02 | 3.14 | yes |
| reference/scalar vs snntorch/cpu | 2.11 | 7.62e-02 | 2.29e-01 | 1.34 | no |
| brian2/cython vs brian2/numpy | -1.45 | 1.96e-01 | 3.92e-01 | -0.92 | no |
| nest/threads2 vs nest/threads4 | 0.05 | 9.59e-01 | 9.59e-01 | 0.03 | no |

Pairs the data does not separate: reference/scalar vs snntorch/cpu (p = 0.229); brian2/cython vs brian2/numpy (p = 0.392); nest/threads2 vs nest/threads4 (p = 0.959). Report these as a failure to detect a difference, not as evidence of equivalence.

## Experiment 3: scalability

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | k | SE(k) | 95% CI | R2 |
|---|---|---|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 1.69188 | 1.74024 | 1.67681 | 1.67569 | 1.68723 | **-0.003** | 0.005 | [-0.018, 0.011] | 0.139 |
| brian2/cython | 0.15338 | 0.14958 | 0.15425 | 0.15922 | 0.16325 | **0.015** | 0.006 | [-0.004, 0.035] | 0.677 |
| brian2/numpy | 0.14563 | 0.14994 | 0.14436 | 0.15867 | 0.16738 | **0.029** | 0.010 | [-0.003, 0.061] | 0.733 |
| nengo/reference | 0.00510 | 0.01333 | 0.11357 | 1.23255 | 4.66472 | **1.545** | 0.181 | [0.969, 2.121] | 0.960 |
| nest/threads1 | 0.00283 | 0.01139 | 0.02506 | 0.18512 | 0.68121 | **1.182** | 0.090 | [0.896, 1.468] | 0.983 |
| nest/threads2 | 0.00241 | 0.00891 | 0.01876 | 0.14233 | 0.49653 | **1.154** | 0.094 | [0.854, 1.454] | 0.980 |
| nest/threads4 | 0.00208 | 0.00788 | 0.01624 | 0.13791 | 0.46282 | **1.176** | 0.096 | [0.870, 1.482] | 0.980 |
| reference/scalar | 0.01560 | 0.07622 | 0.14858 | 0.76050 | 1.56295 | **1.000** | 0.007 | [0.979, 1.021] | 1.000 |
| reference/vectorised | 0.00132 | 0.00284 | 0.00540 | 0.02009 | 0.03812 | **0.747** | 0.055 | [0.571, 0.922] | 0.984 |
| snntorch/cpu | 0.01392 | 0.01652 | 0.02125 | 0.20583 | 0.78812 | **0.901** | 0.226 | [0.183, 1.619] | 0.842 |
| spikingjelly/cpu | 0.00634 | 0.01874 | 0.02394 | 0.21695 | 0.81631 | **1.047** | 0.147 | [0.579, 1.514] | 0.944 |

Steepest: nengo/reference at k = 1.545. Flattest: brian2/cpp_standalone at k = -0.003.

### Ranking at the extremes of the sweep

| Rank | Fastest at N=100 | s | Fastest at N=10000 | s |
|---|---|---|---|---|
| 1 | reference/vectorised | 0.00132 | reference/vectorised | 0.03812 |
| 2 | nest/threads4 | 0.00208 | brian2/cython | 0.16325 |
| 3 | nest/threads2 | 0.00241 | brian2/numpy | 0.16738 |
| 4 | nest/threads1 | 0.00283 | nest/threads4 | 0.46282 |
| 5 | nengo/reference | 0.00510 | nest/threads2 | 0.49653 |
| 6 | spikingjelly/cpu | 0.00634 | nest/threads1 | 0.68121 |
| 7 | snntorch/cpu | 0.01392 | snntorch/cpu | 0.78812 |
| 8 | reference/scalar | 0.01560 | spikingjelly/cpu | 0.81631 |
| 9 | brian2/numpy | 0.14563 | reference/scalar | 1.56295 |
| 10 | brian2/cython | 0.15338 | brian2/cpp_standalone | 1.68723 |
| 11 | brian2/cpp_standalone | 1.69188 | nengo/reference | 4.66472 |

The ranking reverses across the measured range.

### Peak process memory (MB)

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | growth |
|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 639.5 | 639.6 | 639.7 | 641.6 | 646.3 | 1.01x |
| brian2/cython | 638.7 | 638.7 | 638.7 | 640.8 | 646.8 | 1.01x |
| brian2/numpy | 631.2 | 631.8 | 632.5 | 637.6 | 644.2 | 1.02x |
| nengo/reference | 641.4 | 650.8 | 682.2 | 1061.7 | 2206.1 | 3.44x |
| nest/threads1 | 91.0 | 123.4 | 163.8 | 484.8 | 889.3 | 9.77x |
| nest/threads2 | 91.9 | 124.7 | 165.8 | 492.0 | 897.9 | 9.77x |
| nest/threads4 | 93.5 | 127.2 | 169.6 | 503.5 | 923.4 | 9.88x |
| reference/scalar | 696.3 | 696.3 | 696.3 | 696.6 | 696.6 | 1.00x |
| reference/vectorised | 695.7 | 695.7 | 695.7 | 696.4 | 696.3 | 1.00x |
| snntorch/cpu | 690.3 | 690.3 | 690.3 | 785.7 | 1071.8 | 1.55x |
| spikingjelly/cpu | 694.0 | 694.6 | 694.7 | 790.5 | 1077.1 | 1.55x |

## Energy proxy and RQ2

E = t x (u_cpu / 100) x 55 W

TDP source: Intel Core i9-14900HX processor base power, Intel ARK datasheet

| Backend | N=100 | N=500 | N=1000 | N=5000 | N=10000 | (J) |
|---|---|---|---|---|---|---|
| brian2/cpp_standalone | 728.340 | 762.000 | 728.879 | 722.184 | 728.461 | |
| brian2/cython | 8.437 | 8.228 | 8.485 | 8.759 | 8.981 | |
| brian2/numpy | 8.003 | 8.246 | 7.941 | 8.728 | 9.207 | |
| nengo/reference | 0.283 | 0.737 | 189.876 | 2163.558 | 8141.006 | |
| nest/threads1 | 0.158 | 0.628 | 1.380 | 10.182 | 37.467 | |
| nest/threads2 | 0.205 | 0.965 | 2.104 | 15.561 | 54.588 | |
| nest/threads4 | 0.465 | 1.756 | 3.518 | 30.578 | 102.016 | |
| reference/scalar | 0.861 | 4.194 | 8.171 | 41.823 | 85.946 | |
| reference/vectorised | 0.075 | 0.158 | 0.299 | 1.108 | 2.090 | |
| snntorch/cpu | 0.769 | 0.913 | 1.171 | 11.324 | 42.291 | |
| spikingjelly/cpu | 0.351 | 6.902 | 6.117 | 19.393 | 57.986 | |

### Effective operation count for the model

| N | EFLOP | measured output spikes (median across backends) |
|---|---|---|
| 100 | 11,000 | 108 |
| 500 | 55,000 | 537 |
| 1000 | 110,000 | 1007 |
| 5000 | 550,000 | 5220 |
| 10000 | 1,100,000 | 10509 |

### Rank agreement between the proxy and EFLOP

| Backend | rho | exact p | compile-dominated |
|---|---|---|---|
| brian2/cpp_standalone | -0.20 | 0.7833 | yes |
| brian2/cython | 0.90 | 0.0833 | no |
| brian2/numpy | 0.70 | 0.2333 | no |
| nengo/reference | 1.00 | 0.0167 | no |
| nest/threads1 | 1.00 | 0.0167 | no |
| nest/threads2 | 1.00 | 0.0167 | no |
| nest/threads4 | 1.00 | 0.0167 | no |
| reference/scalar | 1.00 | 0.0167 | no |
| reference/vectorised | 1.00 | 0.0167 | no |
| snntorch/cpu | 1.00 | 0.0167 | no |
| spikingjelly/cpu | 0.90 | 0.0833 | no |

Pooled across compute-bound backends (50 runs): **rho = 0.771**, p = 5.62e-11.
