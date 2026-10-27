"""Completeness audit: is every planned experiment a real, recorded measurement?

Usage:  python tools/audit_completeness.py "<path to SNN Simulator Benchmark - Final>"

Checks every inference, scalability and training condition the thesis and the
dashboard use (results/benchmarks.db, exactly the run_groups the dashboard's data
layer serves), the CPU-corrected replication session, and the full-scale
campaign's raw database, and reports any gap. For the rows the thesis uses it
also checks that every run carries a real processor-utilisation reading, an
energy value and a peak-memory value, and that no training row carries the old
0.0 placeholder for memory.
"""
import sqlite3, sys, os
F = sys.argv[1]
BACKENDS = ["brian2/numpy","brian2/cython","brian2/cpp_standalone","nest/threads1","nest/threads2",
            "nest/threads4","nengo/reference","snntorch/cpu","spikingjelly/cpu",
            "reference/vectorised","reference/scalar"]
TRAIN = [b for b in BACKENDS if not b.startswith("reference/")]
SIZES = [100,500,1000,5000,10000]
problems, notes = [], []
def P(msg): problems.append(msg); print("   PROBLEM:", msg)
def N(msg): notes.append(msg); print("   note:", msg)

def audit(label, db, infscal_groups=None, train_groups=None, mach=None, need_cpu=True, training=True):
    c = sqlite3.connect("file:%s?mode=ro&immutable=1" % db, uri=True); c.row_factory = sqlite3.Row
    def where(groups):
        if not groups: return "", []
        return " AND run_group IN (%s) AND machine_id=?" % ",".join("?"*len(groups)), list(groups)+[mach]
    w_is, a_is = where(infscal_groups); w_tr, a_tr = where(train_groups)
    print("\n==== %s" % label)
    cpu_missing = mem_missing = 0
    for task, sizes in (("inference",[100]),("scalability",SIZES)):
        ok = tot = 0
        for b in BACKENDS:
            fw, be = b.split("/")
            for n in sizes:
                for ph in ("setup","simulate"):
                    tot += 1
                    r = c.execute("SELECT * FROM conditions WHERE task=? AND framework=? AND backend=? AND network_size=? AND phase=?"
                                  + w_is + " ORDER BY id DESC", [task, fw, be, n, ph] + a_is).fetchall()
                    if not r: P("%s %s N=%d %s: NO CONDITION RECORDED" % (task,b,n,ph)); continue
                    r = r[0]
                    runs = c.execute("SELECT cpu_pct, energy_j, peak_rss_mb FROM runs WHERE run_group=? AND framework=? AND backend=?"
                                     " AND task=? AND network_size=? AND phase=?", (r["run_group"],fw,be,task,n,ph)).fetchall()
                    bad = []
                    if r["runtime_median_s"] is None: bad.append("no runtime")
                    if r["n_runs"] != 5: bad.append("n_runs=%s" % r["n_runs"])
                    if len(runs) < 5: bad.append("only %d individual runs stored" % len(runs))
                    if task=="scalability" and ph=="simulate" and not r["peak_rss_mb"]: bad.append("no peak memory")
                    nc = sum(1 for x in runs if x["cpu_pct"] is None or x["energy_j"] is None)
                    nm = sum(1 for x in runs if not x["peak_rss_mb"])
                    cpu_missing += nc; mem_missing += nm
                    if need_cpu and nc: bad.append("%d run(s) without utilisation/energy" % nc)
                    if need_cpu and nm: bad.append("%d run(s) without peak memory" % nm)
                    if bad: P("%s %s N=%d %s: %s" % (task,b,n,ph,", ".join(bad)))
                    else: ok += 1
        print("  %-12s %3d of %3d conditions complete (5 measured runs each, individual runs stored%s)"
              % (task, ok, tot, ", utilisation + energy + memory on every run" if need_cpu else ""))
    if not need_cpu and cpu_missing:
        N("%d inference/scalability runs here have no utilisation reading; these rows are not used by the thesis "
          "or the dashboard" % cpu_missing)
    if not training: return
    for budget in (("6000","3"),("60000","10")):
        ok = 0
        for b in TRAIN:
            fw, be = b.split("/")
            r = c.execute("SELECT * FROM conditions WHERE task='training' AND framework=? AND backend=? AND notes LIKE ? AND notes LIKE ?"
                          + w_tr + " ORDER BY id DESC", [fw,be,"%%train_n=%s;%%"%budget[0],"%%epochs=%s;%%"%budget[1]] + a_tr).fetchall()
            if not r: continue
            r = r[0]; bad = []
            if r["accuracy_pct"] is None: bad.append("no accuracy")
            if r["runtime_median_s"] is None: bad.append("no time")
            if "hidden=256;" not in (r["notes"] or ""): bad.append("wrong width")
            exp_test = "10000" if budget[0]=="60000" else "1000"
            if "test_n=%s;"%exp_test not in (r["notes"] or ""): bad.append("test set not %s"%exp_test)
            nr = c.execute("SELECT COUNT(*) FROM runs WHERE run_group=? AND framework=? AND backend=? AND task='training'",
                           (r["run_group"],fw,be)).fetchone()[0]
            if nr < 1: bad.append("individual run not stored")
            if infscal_groups and r["peak_rss_mb"] == 0.0: bad.append("memory stored as 0.0 placeholder")
            if bad: P("training %s %s/%s: %s" % (b,budget[0],budget[1],", ".join(bad)))
            else: ok += 1
        if ok or budget[0]=="60000":
            print("  training %-9s %d of %d backends complete (accuracy + time, hidden 256, full test set, run stored)"
                  % ("%s/%s"%budget, ok, len(TRAIN)))
            if ok < len(TRAIN): P("training %s/%s: only %d of %d backends" % (budget[0],budget[1],ok,len(TRAIN)))
    if infscal_groups:
        print("  training utilisation / energy / memory: not measured (documented limitation, thesis Section 4.6)")

sys.path.insert(0, os.path.join(F,"dashboard")); os.environ["SNN_RESULTS_DIR"] = os.path.join(F,"results")
import dashboard_data as D
DB = os.path.join(F,"results","benchmarks.db")
mach = sqlite3.connect("file:%s?mode=ro&immutable=1" % DB, uri=True).execute(D._CAMPAIGN_MACHINE).fetchone()[0]
audit("THESIS / DASHBOARD DATA  (results/benchmarks.db: CPU-corrected session for inference and scalability, "
      "Aug + Sep campaigns for training)", DB, D.INFSCAL_RUN_GROUPS, D.TRAINING_RUN_GROUPS, mach)
rep = [g for g, lab in D.REPLICATION_RUN_GROUPS.items() if lab.startswith("CPU-corrected")]
audit("REPLICATION  (CPU-corrected session 2, same database)", DB, rep, None, mach, training=False)
audit("FULL-SCALE CAMPAIGN  (full_run_output/benchmarks.db, 11-20 Sep; its inference/scalability utilisation is not used)",
      os.path.join(F,"full_run_output","benchmarks.db"), need_cpu=False)
print("\nPROBLEMS FOUND: %d" % len(problems))
