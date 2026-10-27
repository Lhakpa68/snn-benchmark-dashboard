"""Measurement instrumentation.

One run produces one RunSample. Every individual sample is stored, not just a
mean and a standard deviation: the statistical plan in Chapter 3 promises
normality and variance-homogeneity checks, and those cannot be computed from
summaries. The earlier version of this project kept summaries only, which made
its own analysis plan unexecutable.

Processor utilisation (revised 20 Sep 2026)
--------------------------------------------
Utilisation is the CPU time the measured region consumed divided by its wall
time. How the CPU time is read is what matters, and two earlier methods were
both wrong for the short regions this benchmark measures:

1. The August campaign sampled psutil.cpu_percent() from a background thread
   every 5 ms. Native simulator code that holds the GIL starves that thread:
   a 0.48 s NEST simulation received zero samples, and 181 of 501 "measured"
   runs received fewer than a quarter of the samples their duration implies.
   A run with no samples was stored as a literal 100 %. Each remaining sample
   is a tick-count difference over a few milliseconds, which produced
   values up to 388 844 %.
2. The September campaign differenced psutil.cpu_times(). On Linux that
   counter comes from /proc/<pid>/stat in clock ticks of 10 ms (USER_HZ=100),
   so a 1.2 ms region reads either 0 or 10 ms of CPU: 0 %, or 850 %. All 291
   of that campaign's sub-50 ms runs have a CPU time that is an exact
   multiple of 10 ms.

This version reads CLOCK_PROCESS_CPUTIME_ID through time.process_time(). The
kernel keeps that clock in nanoseconds from the scheduler's own accounting, it
covers every thread of the process (NEST's OpenMP threads and the BLAS and
torch pools included), and it does not depend on any thread being scheduled
to observe it. CPU time of child processes that the region starts and waits
for (Brian2's C++ standalone compiler and binary) is added from
getrusage(RUSAGE_CHILDREN).

Peak memory is taken from the kernel's high-water mark (VmHWM), reset at the
start of each region, so a transient allocation is counted however briefly it
lives. With that available no sampler thread runs during the region, so the
instrument adds no CPU time of its own and no GIL contention. cpu_clock_selftest() checks the instrument
against known loads, and each campaign logs its result.
"""
from __future__ import annotations
import gc, os, threading, time
from dataclasses import dataclass

import snnbench.config as config

try:
    import psutil
    _PROC = psutil.Process(os.getpid())
except Exception:            # psutil is required; fail loudly at run time
    psutil = None
    _PROC = None

try:
    import resource as _resource

    def _children_cpu_s() -> float:
        r = _resource.getrusage(_resource.RUSAGE_CHILDREN)
        return r.ru_utime + r.ru_stime
except ImportError:          # Windows: no getrusage; children not counted
    _resource = None

    def _children_cpu_s() -> float:
        return 0.0

CPU_CLOCK = time.get_clock_info("process_time")
CPU_CLOCK_RESOLUTION_S = CPU_CLOCK.resolution
# A clock coarser than a millisecond (Windows ticks at about 15.6 ms) cannot
# resolve the shortest regions here; such a region is reported as unmeasured.
_COARSE_CLOCK = CPU_CLOCK_RESOLUTION_S > 1e-3


def _reset_peak_rss() -> bool:
    """Reset the kernel's peak-RSS mark (VmHWM) for this process. Linux only;
    writing "5" to /proc/self/clear_refs is the documented reset. Returns
    False where unsupported, and the sampler's peak is then used instead."""
    try:
        with open("/proc/self/clear_refs", "w") as f:
            f.write("5")
        return True
    except OSError:
        return False


def _peak_rss_mb():
    """Kernel-tracked peak RSS since the last reset, in MB, or None."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmHWM:"):
                    return int(line.split()[1]) / 1024.0
    except OSError:
        pass
    return None


def cpu_now() -> float:
    """CPU seconds consumed so far by this process (all threads) plus its
    reaped children. Take the difference across a region, never the value."""
    return time.process_time() + _children_cpu_s()


def utilisation_pct(cpu_s: float, wall_s: float):
    """Mean utilisation over a region in per cent of one core, or None when
    the clock cannot resolve it. Above 100 means real multi-core parallelism."""
    if wall_s is None or wall_s <= 0:
        return None
    if _COARSE_CLOCK and wall_s < CPU_CLOCK_RESOLUTION_S and cpu_s <= 0.0:
        return None
    return 100.0 * max(cpu_s, 0.0) / wall_s


@dataclass
class RunSample:
    runtime_s: float
    peak_rss_mb: float
    rss_delta_mb: float
    mean_cpu_pct: float
    n_cpu_samples: int
    spikes: int = 0

    def energy_j(self, tdp_w: float = None):
        """Runtime-based energy proxy, equation (3.8), or None if utilisation
        was not measured. A quantity that was never measured must not be
        stored as though it were."""
        if self.mean_cpu_pct is None:
            return None
        tdp_w = config.TDP_CPU_W if tdp_w is None else tdp_w
        return self.runtime_s * (self.mean_cpu_pct / 100.0) * tdp_w


class _Sampler(threading.Thread):
    """Fallback memory sampler (peak RSS), used only where the kernel's
    high-water mark cannot be reset. It never reads utilisation."""

    def __init__(self, period_s: float):
        super().__init__(daemon=True)
        self.period = period_s
        self._halt = threading.Event()
        self.rss = []

    def run(self):
        if _PROC is None:
            return
        while not self._halt.is_set():
            try:
                self.rss.append(_PROC.memory_info().rss / 1024**2)
            except Exception:
                pass
            self._halt.wait(self.period)

    def stop(self):
        self._halt.set()
        self.join(timeout=2.0)


def measure(fn, period_s: float = None) -> RunSample:
    """Run `fn` once under the instruments and return one RunSample.

    `fn` may return an integer spike count; if it does, it is recorded.
    The timed region is exactly the call, with garbage collection disabled so
    that a collection triggered by unrelated allocation cannot land inside it.
    """
    period_s = config.SAMPLE_S if period_s is None else period_s
    if _PROC is None:
        raise RuntimeError("psutil is required for measurement; pip install psutil")

    rss0 = _PROC.memory_info().rss / 1024**2
    gc.collect()
    # Where the kernel keeps a resettable high-water mark (Linux, incl. WSL2)
    # no sampler thread runs at all: it would add its own CPU time to the
    # utilisation being measured and compete with the simulator for the GIL.
    # The thread is only a fallback on systems without that facility.
    hwm_ok = _reset_peak_rss()
    sampler = None if hwm_ok else _Sampler(period_s)
    gc_was_on = gc.isenabled()
    gc.disable()
    if sampler:
        sampler.start()
    c0 = cpu_now()
    t0 = time.perf_counter()
    try:
        out = fn()
    finally:
        t1 = time.perf_counter()
        c1 = cpu_now()
        if sampler:
            sampler.stop()
        if gc_was_on:
            gc.enable()

    rss1 = _PROC.memory_info().rss / 1024**2
    peak = max(sampler.rss) if (sampler and sampler.rss) else max(rss0, rss1)
    # The sampler can miss a short-lived allocation inside the region (it is
    # starved by native code just as the old utilisation sampler was); the
    # kernel's own high-water mark cannot, so it is used wherever available.
    hwm = _peak_rss_mb() if hwm_ok else None
    if hwm is not None:
        peak = max(peak, hwm)
    wall_s = t1 - t0
    mean_cpu = utilisation_pct(c1 - c0, wall_s)
    return RunSample(
        runtime_s=wall_s,
        peak_rss_mb=max(peak, rss1),
        rss_delta_mb=rss1 - rss0,
        mean_cpu_pct=mean_cpu,
        # Utilisation now comes from one pair of CPU-clock readings per run,
        # so this is 1 when it was measured and 0 when it was not. The column
        # keeps its name for schema compatibility.
        n_cpu_samples=0 if mean_cpu is None else 1,
        spikes=int(out) if isinstance(out, (int, float)) and out is not None else 0,
    )


def peak_rss_self_mb():
    """Peak resident memory of this process over its lifetime, in MB, from
    getrusage (kernel-maintained high-water mark, not a sample). None where
    getrusage is unavailable."""
    if _resource is None:
        return None
    return _resource.getrusage(_resource.RUSAGE_SELF).ru_maxrss / 1024.0


class RegionClock:
    """Accumulates wall and CPU time over many short timed stretches, for the
    training loops, which time each sample or batch and sum. Its state is two
    floats, so it is saved in the training checkpoints with the rest."""

    def __init__(self, wall_s: float = 0.0, cpu_s: float = 0.0):
        self.wall_s, self.cpu_s = wall_s, cpu_s

    def start(self):
        self._c0 = cpu_now()
        self._t0 = time.perf_counter()

    def stop(self) -> float:
        dt = time.perf_counter() - self._t0
        self.cpu_s += cpu_now() - self._c0
        self.wall_s += dt
        return dt

    def pct(self):
        return utilisation_pct(self.cpu_s, self.wall_s)


# --------------------------------------------------------------------------
def _spin(seconds):
    end = time.perf_counter() + seconds
    x = 0
    while time.perf_counter() < end:
        x += 1
    return x


def cpu_clock_selftest(durations=(0.001, 0.01, 0.1), repeats=20):
    """Check the utilisation instrument against loads whose answer is known,
    at the region lengths this benchmark measures. Returns a list of dicts
    and an overall pass flag. Known answers: sleeping ~0 %; one busy Python
    thread ~100 %; two
    threads outside the GIL ~200 %; a child process kept busy for the whole region ~100 % on
    top of the parent's own (near-idle) wait."""
    import statistics, subprocess, sys
    rows, ok = [], True

    def one(label, fn, d, lo, hi):
        nonlocal ok
        vals = []
        for _ in range(repeats):
            c0, t0 = cpu_now(), time.perf_counter()
            fn(d)
            wall = time.perf_counter() - t0
            vals.append(utilisation_pct(cpu_now() - c0, wall))
        vals = [v for v in vals if v is not None]
        med = statistics.median(vals) if vals else None
        passed = med is not None and lo <= med <= hi
        ok &= passed
        rows.append(dict(load=label, region_ms=d * 1000, median_pct=med,
                         min_pct=min(vals) if vals else None,
                         max_pct=max(vals) if vals else None,
                         expected=f"{lo:g}-{hi:g}", passed=passed))

    for d in durations:
        one("sleep", time.sleep, d, 0, 10)
        one("spin 1 thread", _spin, d, 90, 110)
    def two_threads(d):
        import hashlib
        buf = b"x" * (1 << 20)

        def work():
            end = time.perf_counter() + d
            while time.perf_counter() < end:
                hashlib.sha256(buf).digest()   # releases the GIL
        ts = [threading.Thread(target=work) for _ in range(2)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
    if (os.cpu_count() or 1) >= 2:
        one("2 threads, GIL released", two_threads, 0.1, 150, 210)
    # the full measure() path, as the benchmark calls it
    vals = [measure(lambda: _spin(0.005) and 0).mean_cpu_pct for _ in range(repeats)]
    med = statistics.median(vals)
    m_ok = 90 <= med <= 110
    ok &= m_ok
    rows.append(dict(load="measure(): spin 5 ms", region_ms=5.0, median_pct=med,
                     min_pct=min(vals), max_pct=max(vals), expected="90-110",
                     passed=m_ok))
    # memory: a 200 MB buffer allocated and freed inside the region
    def alloc():
        b = bytearray(200 * 1024 * 1024)
        b[::4096] = b"x" * len(b[::4096])
        del b
        return 0
    base = _PROC.memory_info().rss / 1024**2
    ms = measure(alloc)
    mem_ok = ms.peak_rss_mb - base >= 180
    ok &= mem_ok
    rows.append(dict(load="transient 200 MB allocation", region_ms=ms.runtime_s*1000,
                     peak_above_start_mb=ms.peak_rss_mb - base,
                     expected=">=180 MB", passed=mem_ok))
    child = [sys.executable, "-c",
             "import time,sys\nend=time.perf_counter()+float(sys.argv[1])\n"
             "while time.perf_counter()<end: pass", "0.3"]
    one("child process spin 0.3 s",
        lambda d: subprocess.run(child, check=True), 0.3, 80, 130)
    return rows, ok


if __name__ == "__main__":
    import json
    print("clock:", CPU_CLOCK)
    rows, ok = cpu_clock_selftest()
    for r in rows:
        print(json.dumps(r))
    print("SELFTEST", "PASS" if ok else "FAIL")


def reset_peak_rss() -> bool:
    """Public form of the peak-RSS reset, for the training adapters. They run
    far longer than one measure() region and keep their own accumulators."""
    return _reset_peak_rss()


def peak_rss_mb():
    """Public form of the kernel peak-RSS reading, for the training adapters."""
    return _peak_rss_mb()
