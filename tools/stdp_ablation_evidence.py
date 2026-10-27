"""
Evidence for Chapter 4, Section 4.2 (Table 4.bb).

Question: why do the six unsupervised-STDP backends sit at chance accuracy?
Method:   reproduce the Experiment 2 plastic-layer specification independently
          (same LIF dynamics, pair-based STDP constants, Poisson input regime,
          25 ms presentation window, divisive weight normalisation) and ablate
          two architectural mechanisms that specification omits:
             - lateral inhibition (soft winner-take-all)
             - adaptive membrane threshold
Diagnostics: classification accuracy, mean pairwise correlation between learned
          receptive fields, and the number of classes the labelling readout uses.

Run:  python3 stdp_ablation_evidence.py
Needs: results/mnist_784.npz (the same cache the benchmark suite uses)

Result (three seeds, 100 neurons, 2,000 samples, 1 epoch):
  neither mechanism   ->  9.7%      RF corr 1.000        1 of 10 classes
  inhibition only     ->  9.7%      RF corr 0.743-0.744  1 of 10 classes
  adaptive thr. only  ->  9.7%      RF corr 0.980-0.994  1 of 10 classes
  both                -> 45.9-48.3% RF corr 0.577-0.580  10 of 10 classes

Conclusion: neither mechanism alone breaks the receptive-field collapse; both
are required. Chance accuracy is the predicted behaviour of the specification
used in Experiment 2, not a simulator defect.
"""
import os, sys, time
import numpy as np

TAU_MS = 10.0; TAUPRE = TAUPOST = 20.0; DT = 1.0; SIM_MS = 25.0
RATE = 100.0; GMAX = 1.0; dApre = 0.01; dApost = -dApre * 1.05
W0 = 0.02; NIN = 784; NCLS = 10; SEED = 1234
STEPS = int(round(SIM_MS / DT))

def _find_mnist():
    for c in (os.path.join(os.path.dirname(__file__), "..", "results", "mnist_784.npz"),
              "results/mnist_784.npz", "mnist_784.npz"):
        if os.path.exists(c):
            return c
    sys.exit("mnist_784.npz not found - point this at the suite's results/ cache")

_z = np.load(_find_mnist())
_kx = "X" if "X" in _z else _z.files[0]
_ky = "y" if "y" in _z else _z.files[1]
X = _z[_kx].astype(np.float32); Y = _z[_ky].astype(np.int64)
if X.max() > 1.5:
    X = X / 255.0
IDX = np.random.default_rng(SEED).permutation(len(X))


def run(hidden=100, train_n=2000, test_n=1000,
        inhibition=False, adaptive=False, seed=SEED):
    tr, te = IDX[:train_n], IDX[train_n:train_n + test_n]
    xtr, ytr, xte, yte = X[tr], Y[tr], X[te], Y[te]
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.0, W0, size=(NIN, hidden)).astype(np.float64)
    target_sum = W0 * 0.5 * NIN
    d_pre = np.exp(-DT / TAUPRE); d_post = np.exp(-DT / TAUPOST); d_v = np.exp(-DT / TAU_MS)
    theta = np.zeros(hidden); THETA_PLUS = 0.05; THETA_TAU = 1e4

    def normalise(w):
        s = w.sum(axis=0); s[s <= 0] = 1.0
        return w * (target_sum / s)

    def present(x, w, learn=True):
        v = np.zeros(hidden); apre = np.zeros(NIN); apost = np.zeros(hidden)
        cnt = np.zeros(hidden, dtype=np.int64)
        p = x * RATE * (DT / 1000.0)
        for _ in range(STEPS):
            pre = rng.random(NIN) < p
            apre *= d_pre; apost *= d_post; v *= d_v
            if pre.any():
                j = np.nonzero(pre)[0]
                v += w[j].sum(axis=0)
                if learn:
                    w[j] = np.clip(w[j] + apost[None, :], 0, GMAX)
                    apre[j] += dApre
            thr = 1.0 + theta if adaptive else 1.0
            fired = np.nonzero(v >= thr)[0]
            if fired.size:
                if inhibition:                      # soft winner-take-all
                    fired = np.array([fired[np.argmax(v[fired])]])
                    v[:] = 0.0
                else:
                    v[fired] = 0.0
                cnt[fired] += 1
                if adaptive:
                    theta[fired] += THETA_PLUS
                if learn:
                    w[:, fired] = np.clip(w[:, fired] + apre[:, None], 0, GMAX)
                    apost[fired] += dApost
            if inhibition:
                v[fired] = 0.0
        if adaptive:
            theta[:] *= np.exp(-SIM_MS / THETA_TAU)
        return cnt, w

    counts = np.zeros((hidden, NCLS))
    for i in range(train_n):
        c, w = present(xtr[i], w, learn=True)
        w = normalise(w)
        counts[:, ytr[i]] += c
    labels = counts.argmax(axis=1)
    labels[counts.sum(axis=1) == 0] = -1

    correct = 0
    for i in range(test_n):
        c, _ = present(xte[i], w, learn=False)
        scores = np.full(NCLS, -1.0)
        for k in range(NCLS):
            m = labels == k
            if m.any():
                scores[k] = c[m].mean()
        correct += int(scores.argmax() == yte[i])

    wn = w / (np.linalg.norm(w, axis=0, keepdims=True) + 1e-12)
    corr = wn.T @ wn; iu = np.triu_indices(hidden, 1)
    used = labels[labels >= 0]
    return dict(acc=100.0 * correct / test_n,
                rf_corr=float(corr[iu].mean()),
                classes=int(len(set(used.tolist()))),
                top_share=float(np.bincount(used, minlength=NCLS).max() / max(1, used.size)))


if __name__ == "__main__":
    conds = [("neither (as specified)", {}),
             ("lateral inhibition only", dict(inhibition=True)),
             ("adaptive threshold only", dict(adaptive=True)),
             ("both", dict(inhibition=True, adaptive=True))]
    print(f"{'mechanisms':26}{'seed':>6}{'acc %':>9}{'RF corr':>10}{'classes':>9}{'top share':>11}")
    print("-" * 71)
    for seed in (1234, 7, 99):
        for name, kw in conds:
            t = time.time(); r = run(seed=seed, **kw)
            print(f"{name:26}{seed:>6}{r['acc']:>9.2f}{r['rf_corr']:>10.3f}"
                  f"{r['classes']:>6} /10{r['top_share']*100:>10.1f}%")
        print()
