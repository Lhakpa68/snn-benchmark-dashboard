"""Full machine identification, recorded on every result row.

An earlier version of this project stored the string returned by
platform.system() + platform.machine(), which is "Linux x86_64" on a laptop, a
cloud container and a hosted notebook alike. Merging two exports would then have
pooled two machines silently, which is the one error a multi-machine study
cannot recover from, because it is undetectable afterwards.
"""
from __future__ import annotations
import platform, os, socket, subprocess, json, hashlib


def _cpu_model() -> str:
    try:
        for line in open("/proc/cpuinfo"):
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    try:
        return subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        return platform.processor() or "unknown"


def _logical_cores() -> int:
    return os.cpu_count() or 0


def _ram_gb() -> float:
    try:
        import psutil
        return round(psutil.virtual_memory().total / 1024**3, 1)
    except Exception:
        return 0.0


def _under_wsl() -> bool:
    try:
        return "microsoft" in open("/proc/version").read().lower()
    except Exception:
        return False


def profile() -> dict:
    p = dict(
        hostname=socket.gethostname(),
        os=f"{platform.system()} {platform.release()}",
        arch=platform.machine(),
        cpu=_cpu_model(),
        logical_cores=_logical_cores(),
        ram_gb=_ram_gb(),
        python=platform.python_version(),
        wsl=_under_wsl(),
        accelerator="CPU only",
    )
    p["machine_id"] = (
        f"{p['hostname']} | {p['os']} {p['arch']}"
        f"{' (WSL2)' if p['wsl'] else ''} | {p['cpu']} | {p['logical_cores']} logical cores"
    )
    p["fingerprint"] = hashlib.sha1(
        f"{p['hostname']}|{p['cpu']}|{p['logical_cores']}".encode()).hexdigest()[:12]
    return p


def versions() -> dict:
    """Version of every package that could affect a measurement, captured at
    run time rather than transcribed by hand into a document."""
    out = {}
    for mod in ("numpy", "scipy", "brian2", "nest", "nengo", "snntorch",
                "torch", "spikingjelly", "cython", "psutil"):
        try:
            m = __import__(mod)
            out[mod] = getattr(m, "__version__", None) or getattr(m, "version", "present")
            if mod == "nest":
                out[mod] = m.__version__ if hasattr(m, "__version__") else str(m.version())
        except Exception:
            out[mod] = None
    return {k: (str(v) if v is not None else "not installed") for k, v in out.items()}


if __name__ == "__main__":
    print(json.dumps(dict(machine=profile(), packages=versions()), indent=2))
