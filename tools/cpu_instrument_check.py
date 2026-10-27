"""Reproduces the two utilisation defects and checks the corrected instrument.

Runs loads whose true utilisation is known and measures each with all three
methods this project has used:

  A  Aug 2026  background thread sampling psutil.cpu_percent() every 5 ms;
               a region with no samples was stored as 100 %
  B  Sep 2026  psutil.cpu_times() difference (Linux: 10 ms clock ticks)
  C  current   time.process_time() (CLOCK_PROCESS_CPUTIME_ID, nanoseconds)
               plus reaped children, as in snnbench/profiler.py

All three read the same region in the same run. Method A needs its sampler
thread running, so in this comparison C also counts that thread's small CPU
cost; the self-test at the end measures C alone, as the benchmark uses it.

Usage:  python tools/cpu_instrument_check.py  [> report.txt]
"""
import os, sys, time, threading, statistics, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psutil
from snnbench import profiler

P = psutil.Process(os.getpid())


class OldSampler(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True); self.halt = threading.Event(); self.cpu = []
    def run(self):
        P.cpu_percent(None)
        while not self.halt.is_set():
            self.cpu.append(P.cpu_percent(None)); self.halt.wait(0.005)


def run_all(fn):
    s = OldSampler(); s.start()
    ct0 = P.cpu_times(); c0 = profiler.cpu_now(); t0 = time.perf_counter()
    fn()
    t1 = time.perf_counter(); c1 = profiler.cpu_now(); ct1 = P.cpu_times()
    s.halt.set(); s.join()
    wall = t1 - t0
    a = (sum(s.cpu) / len(s.cpu)) if s.cpu else 100.0
    b = 100.0 * ((ct1.user - ct0.user) + (ct1.system - ct0.system)) / wall
    c = profiler.utilisation_pct(c1 - c0, wall)
    return wall, a, b, c, len(s.cpu)


def spin(d):
    def f():
        end = time.perf_counter() + d
        while time.perf_counter() < end:
            pass
    return f


def gil_held(n):
    # list.sort() on a large list runs in C and holds the GIL throughout,
    # like a native simulator kernel that does not release it.
    data = list(range(n, 0, -1))
    def f():
        data.sort(); data.reverse()  # sort then un-sort: same work each call
    return f


LOADS = [("spin 1 ms (true 100 %)", spin(0.001), 100),
         ("spin 10 ms (true 100 %)", spin(0.010), 100),
         ("spin 100 ms (true 100 %)", spin(0.100), 100),
         ("sleep 10 ms (true ~0 %)", lambda: time.sleep(0.010), 0),
         ("native code holding the GIL (true 100 %)", gil_held(10_000_000), 100)]

if __name__ == "__main__":
    print("python", sys.version.split()[0], "| process_time clock:",
          time.get_clock_info("process_time").implementation,
          "| cores:", os.cpu_count())
    out = []
    for name, fn, truth in LOADS:
        fn()  # warm
        rs = [run_all(fn) for _ in range(15)]
        row = dict(load=name, true_pct=truth,
                   wall_ms=round(statistics.median(r[0] for r in rs) * 1000, 2))
        for k, i in (("A_aug_sampler", 1), ("B_sep_cpu_times", 2), ("C_current", 3)):
            v = [r[i] for r in rs]
            row[k] = dict(median=round(statistics.median(v), 1),
                          min=round(min(v), 1), max=round(max(v), 1))
        row["A_runs_with_no_sample_(stored_as_100)"] = sum(1 for r in rs if r[4] == 0)
        out.append(row)
        print(json.dumps(row))
    rows, ok = profiler.cpu_clock_selftest()
    for r in rows:
        print(json.dumps(r))
    print("SELFTEST", "PASS" if ok else "FAIL")
