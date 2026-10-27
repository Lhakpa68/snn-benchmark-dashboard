"""MNIST loading, cached locally so the benchmark does not depend on a network
connection at run time.

Looks in this order:
  1. results/mnist_784.npz next to the suite
  2. any mnist_784.npz found under the project tree
  3. torchvision, if installed
  4. openml via scikit-learn, if installed and the network is reachable
"""
from __future__ import annotations
import os, pathlib
import numpy as np
import snnbench.config as C

_CACHE = C.RESULTS_DIR / "mnist_784.npz"


def _find_existing() -> pathlib.Path | None:
    if _CACHE.exists():
        return _CACHE
    for root in (C.BASE_DIR, C.BASE_DIR.parent):
        for p in root.rglob("mnist_784.npz"):
            return p
    return None


def _download() -> tuple[np.ndarray, np.ndarray]:
    try:
        from torchvision import datasets
        d = datasets.MNIST(str(C.RESULTS_DIR / "mnist"), train=True, download=True)
        X = d.data.numpy().reshape(len(d), -1).astype(np.float32) / 255.0
        y = d.targets.numpy().astype(np.int64)
        return X, y
    except Exception:
        pass
    from sklearn.datasets import fetch_openml
    d = fetch_openml("mnist_784", version=1, as_frame=False, parser="auto")
    return d.data.astype(np.float32) / 255.0, d.target.astype(np.int64)


def load_mnist(train_n: int, test_n: int):
    p = _find_existing()
    if p is not None:
        z = np.load(p)
        key_x = "X" if "X" in z else ("data" if "data" in z else z.files[0])
        key_y = "y" if "y" in z else ("target" if "target" in z else z.files[1])
        X, y = z[key_x], z[key_y]
        X = X.astype(np.float32)
        if X.max() > 1.5:
            X = X / 255.0
        y = y.astype(np.int64)
    else:
        X, y = _download()
        np.savez_compressed(_CACHE, X=X, y=y)

    rng = np.random.default_rng(C.SEED)
    idx = rng.permutation(len(X))
    tr, te = idx[:train_n], idx[train_n:train_n + test_n]
    return (X[tr], y[tr]), (X[te], y[te])
