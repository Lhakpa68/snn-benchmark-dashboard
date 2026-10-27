## 2. Practical-consequence analysis

Eligible set: the 8 backends of the dashboard (9 SNN backends minus Brian2 C++ standalone). Median runtimes are the values the selection uses (session A unless stated). Min-max ranges are the smallest and largest of the five runs of that cell and are shown for context only; overlap of ranges describes the runs, not uncertainty in a combined score.

### 2a. Reusing a Fast-SNN choice across sizes (session A)

Fast SNN winners: N=100: nest/threads4, N=500: nest/threads4, N=1,000: nest/threads4, N=5,000: nest/threads4, N=10,000: brian2/cython.

**Forward: N = 100 winner reused at larger sizes** (nest/threads4)

| N | Reused median (ms) | Best at N | Best median (ms) | Ratio reused/best | Difference (ms) | Run ranges overlap |
|---|---|---|---|---|---|---|
| 100 | 1.8223 (1.727 to 2.268) | nest/threads4 | 1.8223 (1.727 to 2.268) | 1 | 0 | yes |
| 500 | 7.7752 (7.262 to 8.522) | nest/threads4 | 7.7752 (7.262 to 8.522) | 1 | 0 | yes |
| 1,000 | 14.2158 (14.08 to 14.93) | nest/threads4 | 14.2158 (14.08 to 14.93) | 1 | 0 | yes |
| 5,000 | 106.087 (93.67 to 114) | nest/threads4 | 106.087 (93.67 to 114) | 1 | 0 | yes |
| 10,000 | 353.015 (336 to 366.7) | brian2/cython | 148.535 (146.1 to 152.7) | 2.3767 | 204.481 | no |

**Reverse: N = 10,000 winner reused at smaller sizes** (brian2/cython)

| N | Reused median (ms) | Best at N | Best median (ms) | Ratio reused/best | Difference (ms) | Run ranges overlap |
|---|---|---|---|---|---|---|
| 100 | 137.621 (135.1 to 145.9) | nest/threads4 | 1.8223 (1.727 to 2.268) | 75.5218 | 135.799 | no |
| 500 | 148.304 (135.3 to 161.8) | nest/threads4 | 7.7752 (7.262 to 8.522) | 19.074 | 140.529 | no |
| 1,000 | 138.284 (133.9 to 140.5) | nest/threads4 | 14.2158 (14.08 to 14.93) | 9.7275 | 124.068 | no |
| 5,000 | 147.315 (141.8 to 160.2) | nest/threads4 | 106.087 (93.67 to 114) | 1.3886 | 41.228 | no |
| 10,000 | 148.535 (146.1 to 152.7) | brian2/cython | 148.535 (146.1 to 152.7) | 1 | 0 | yes |

### 2b. Session transfer (cells whose choice differs between sessions)

Both backends are scored on session-B measurements. Accuracy comes from the training experiment and is **shared** by both sessions (accuracy-weighted profiles marked *). Score = weighted normalised cost, lower is better; a score difference is a distance under the stated weights, not a significance test.

| Profile | N | Backend | Role | B runtime (ms) | B peak RSS (MB) | B growth (MB) | k (R²) | B score | A score |
|---|---|---|---|---|---|---|---|---|---|
| Accuracy + speed* | 100 | nengo/reference | session-A choice | 5.0396 | 641.2 | 0 | 1.5188 (0.952) | 0.17838 | 0.17075 |
| Accuracy + speed* | 100 | spikingjelly/cpu | session-B choice | 5.3367 | 693.71 | 0 | 1.0529 (0.953) | 0.11768 | 0.18658 |
| Accuracy + speed* | 500 | snntorch/cpu | session-A choice | 20.4021 | 689.97 | 0 | 0.8604 (0.88) | 0.16601 | 0.12042 |
| Accuracy + speed* | 500 | spikingjelly/cpu | session-B choice | 16.4513 | 694.36 | 0.652 | 1.0529 (0.953) | 0.12831 | 0.1636 |
| Accuracy + speed* | 1,000 | snntorch/cpu | session-A choice | 29.4871 | 690.04 | 0.062 | 0.8604 (0.88) | 0.13894 | 0.08641 |
| Accuracy + speed* | 1,000 | spikingjelly/cpu | session-B choice | 22.9455 | 694.43 | 0.723 | 1.0529 (0.953) | 0.08821 | 0.11015 |
| Accuracy + speed* | 5,000 | snntorch/cpu | session-A choice | 196.799 | 785.41 | 95.434 | 0.8604 (0.88) | 0.13436 | 0.13837 |
| Accuracy + speed* | 5,000 | spikingjelly/cpu | session-B choice | 189.082 | 790.22 | 96.516 | 1.0529 (0.953) | 0.12498 | 0.14242 |
| Fast SNN | 10,000 | brian2/cython | session-A choice | 158.208 | 646.71 | 8.129 | 0.0206 (0.97) | 0.00193 | 0 |
| Fast SNN | 10,000 | brian2/numpy | session-B choice | 157.21 | 644.14 | 13.008 | 0.0215 (0.832) | 0 | 0.00029 |
| Speed + memory | 500 | snntorch/cpu | session-A choice | 20.4021 | 689.97 | 0 | 0.8604 (0.88) | 0.16478 | 0.11919 |
| Speed + memory | 500 | spikingjelly/cpu | session-B choice | 16.4513 | 694.36 | 0.652 | 1.0529 (0.953) | 0.138 | 0.17334 |
| Speed + memory | 1,000 | snntorch/cpu | session-A choice | 29.4871 | 690.04 | 0.062 | 0.8604 (0.88) | 0.13812 | 0.08559 |
| Speed + memory | 1,000 | spikingjelly/cpu | session-B choice | 22.9455 | 694.43 | 0.723 | 1.0529 (0.953) | 0.09298 | 0.11491 |

Side by side (session B): which backend is lower on each raw criterion, and the score difference (A-choice minus B-choice; negative would favour the A-choice).

| Profile | N | Faster | Lower growth | Lower k | Score diff (A-choice − B-choice) |
|---|---|---|---|---|---|
| Accuracy + speed* | 100 | nengo/reference | equal | spikingjelly/cpu | +0.06070 |
| Accuracy + speed* | 500 | spikingjelly/cpu | snntorch/cpu | snntorch/cpu | +0.03770 |
| Accuracy + speed* | 1,000 | spikingjelly/cpu | snntorch/cpu | snntorch/cpu | +0.05073 |
| Accuracy + speed* | 5,000 | spikingjelly/cpu | snntorch/cpu | snntorch/cpu | +0.00938 |
| Fast SNN | 10,000 | brian2/numpy | brian2/cython | brian2/cython | +0.00193 |
| Speed + memory | 500 | spikingjelly/cpu | snntorch/cpu | snntorch/cpu | +0.02678 |
| Speed + memory | 1,000 | spikingjelly/cpu | snntorch/cpu | snntorch/cpu | +0.04514 |

### 2c. Cells that change with normalisation or with scalability removed

Raw values side by side and the score under each setting. Scores of different normalisations are on different scales and are not comparable in magnitude; only the ordering within a column is meaningful. Accuracy is shared across sessions (all values here are session A).

| Change | Profile | N | Backend | Role | Runtime (ms) | Growth (MB) | k | Score min-max | Score share | Score min-max, no scal. | Tied set without scalability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| normalisation | Accuracy + speed* | 100 | nengo/reference | min-max winner | 4.456 | 0 | 1.5444 | 0.17075 | 0.02259 | n/a | - |
| normalisation | Accuracy + speed* | 100 | spikingjelly/cpu | share winner | 9.1499 | 0 | 0.9598 | 0.18658 | 0.01763 | n/a | - |
| normalisation | Balanced | 100 | nest/threads4 | min-max winner | 1.8223 | 0 | 1.1335 | 0.24382 | 0.05687 | 0.0 | - |
| normalisation | Balanced | 100 | spikingjelly/cpu | share winner | 9.1499 | 0 | 0.9598 | 0.33036 | 0.05645 | 0.18658 | - |
| normalisation | Balanced | 5,000 | brian2/numpy | min-max winner | 142.115 | 6.473 | 0.0173 | 0.04447 | 0.02273 | 0.0657 | - |
| normalisation | Balanced | 5,000 | brian2/cython | share winner | 147.315 | 2.109 | 0.0142 | 0.04528 | 0.02255 | 0.06792 | - |
| normalisation | Speed + memory | 5,000 | brian2/numpy | min-max winner | 142.115 | 6.473 | 0.0173 | 0.0657 | 0.03284 | n/a | - |
| normalisation | Speed + memory | 5,000 | brian2/cython | share winner | 147.315 | 2.109 | 0.0142 | 0.06792 | 0.03278 | n/a | - |
| scalability removal | Memory + scaling | 100 | brian2/cython | min-max winner | 137.621 | 0 | 0.0142 | 0 | 0.00103 | 0.0 | nest/threads4|nest/threads2|nest/threads1|nengo/reference|spikingjelly/cpu|snntorch/cpu|brian2/numpy|brian2/cython |
| scalability removal | Memory + scaling | 100 | nest/threads4 | winner without scalability (tie-break pick) | 1.8223 | 0 | 1.1335 | 0.36572 | 0.08232 | 0.0 | nest/threads4|nest/threads2|nest/threads1|nengo/reference|spikingjelly/cpu|snntorch/cpu|brian2/numpy|brian2/cython |
| scalability removal | Memory + scaling | 500 | brian2/cython | min-max winner | 148.304 | 0 | 0.0142 | 0 | 0.00103 | 0.0 | snntorch/cpu|brian2/cython |
| scalability removal | Memory + scaling | 500 | snntorch/cpu | winner without scalability (tie-break pick) | 15.7015 | 0 | 0.9212 | 0.29634 | 0.0669 | 0.0 | snntorch/cpu|brian2/cython |
| scalability removal | Scaling + accuracy* | 100 | snntorch/cpu | min-max winner | 12.4261 | 0 | 0.9212 | 0.29758 | 0.0698 | 0.00247 | - |
| scalability removal | Scaling + accuracy* | 100 | spikingjelly/cpu | winner without scalability (tie-break pick) | 9.1499 | 0 | 0.9598 | 0.30897 | 0.07238 | 0.0 | - |
| scalability removal | Scaling + accuracy* | 500 | snntorch/cpu | min-max winner | 15.7015 | 0 | 0.9212 | 0.29758 | 0.0698 | 0.00247 | - |
| scalability removal | Scaling + accuracy* | 500 | spikingjelly/cpu | winner without scalability (tie-break pick) | 20.4024 | 0.652 | 0.9598 | 0.30897 | 0.07238 | 0.0 | - |
| scalability removal | Scaling + accuracy* | 1,000 | snntorch/cpu | min-max winner | 22.4264 | 0.062 | 0.9212 | 0.29758 | 0.0698 | 0.00247 | - |
| scalability removal | Scaling + accuracy* | 1,000 | spikingjelly/cpu | winner without scalability (tie-break pick) | 25.633 | 0.723 | 0.9598 | 0.30897 | 0.07238 | 0.0 | - |
| scalability removal | Scaling + accuracy* | 5,000 | snntorch/cpu | min-max winner | 205.856 | 95.434 | 0.9212 | 0.29758 | 0.0698 | 0.00247 | - |
| scalability removal | Scaling + accuracy* | 5,000 | spikingjelly/cpu | winner without scalability (tie-break pick) | 211.186 | 96.516 | 0.9598 | 0.30897 | 0.07238 | 0.0 | - |
| scalability removal | Scaling + accuracy* | 10,000 | snntorch/cpu | min-max winner | 772.004 | 381.535 | 0.9212 | 0.29758 | 0.0698 | 0.00247 | - |
| scalability removal | Scaling + accuracy* | 10,000 | spikingjelly/cpu | winner without scalability (tie-break pick) | 764.225 | 383.145 | 0.9598 | 0.30897 | 0.07238 | 0.0 | - |
