"""Bring the training rows of one sample budget from one results database into another.

The two campaigns were written to two databases: the fixed budget that makes
the cross-simulator comparison controlled (6,000 train / 1,000 test, three
epochs) and the full reference budget the specification asks for (60,000 /
10,000, ten epochs). The dashboard can only show both if they live together.

Three things this refuses to do, because each would break a control the study
depends on:

  * merge a row measured on a different machine -- Section 4.8 records a
    partial re-run on another computer as a defect that invalidated results;
  * merge a stale partial run. The source database also holds rows at
    50,000/1, 800/2 and 300/1 from aborted earlier attempts. Only the budget
    named on the command line is copied;
  * merge anything if the destination already holds that budget.

Usage:
  python3 merge_fixed_budget.py <source.db> <dest.db> [--budget 6000/3] [--apply]

Without --apply it reports what it would do and writes nothing.
"""
import sqlite3, sys, shutil, datetime, argparse, os

TRAIN_N = ("substr(notes, instr(notes,'train_n=')+8, "
           "instr(notes,'; test_n=')-instr(notes,'train_n=')-8)")
EPOCHS = ("substr(substr(notes, instr(notes,'epochs=')+7), 1, "
          "instr(substr(notes, instr(notes,'epochs=')+7), ';')-1)")
BKEY = (f"CASE WHEN task='training' AND instr(notes,'train_n=')>0 "
        f"AND instr(notes,'; test_n=')>0 AND instr(notes,'epochs=')>0 "
        f"THEN {TRAIN_N} || '/' || {EPOCHS} ELSE '' END")


def open_ro(p):
    c = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
    c.row_factory = sqlite3.Row
    if c.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        sys.exit("ABORT: %s is malformed." % p)
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source"); ap.add_argument("dest")
    ap.add_argument("--budget", default="6000/3")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    src, dst = open_ro(a.source), open_ro(a.dest)

    # The campaign machine is the one the dashboard itself selects: the machine
    # with the most conditions (dashboard_data._CAMPAIGN_MACHINE does the same
    # over the canonical groups). A database may also hold a few rows from an
    # older machine - the thesis campaign's database does, from an earlier
    # 2-core instance - and the dashboard already excludes those; they do not
    # make the database unusable, but nothing from another machine may be
    # merged in.
    counts = dst.execute("SELECT machine_id, COUNT(*) FROM conditions "
                         "GROUP BY machine_id ORDER BY COUNT(*) DESC").fetchall()
    if not counts:
        sys.exit("ABORT: destination has no conditions.")
    machine = counts[0][0]
    if len(counts) > 1:
        print("note: destination also holds %d row(s) from %d other machine(s); the "
              "dashboard excludes them and they are left untouched."
              % (sum(n for _, n in counts[1:]), len(counts) - 1))

    have = {r[0] for r in dst.execute(
        f"SELECT DISTINCT {BKEY} FROM conditions WHERE task='training'")}
    if a.budget in have:
        sys.exit("ABORT: destination already holds budget %s. Nothing to do." % a.budget)

    rows = src.execute(
        f"SELECT * FROM conditions WHERE task='training' AND ({BKEY})=?", (a.budget,)
    ).fetchall()
    if not rows:
        sys.exit("ABORT: no training rows at budget %s in the source." % a.budget)

    wrong = [r for r in rows if r["machine_id"] != machine]
    if wrong:
        sys.exit("ABORT: %d of %d source rows were measured on a different machine "
                 "than the destination campaign. Merging them would break the "
                 "single-machine control Section 4.8 documents." % (len(wrong), len(rows)))

    # Same budget, same backend, more than once -> keep the newest, exactly as
    # the dashboard's own de-duplication does.
    keep = {}
    for r in rows:
        keep[(r["framework"], r["backend"], r["network_size"], r["phase"])] = r
    chosen = sorted(keep.values(), key=lambda r: r["id"])

    print("source  : %s" % a.source)
    print("dest    : %s" % a.dest)
    print("machine : %s" % machine[:70])
    print("budget  : %s" % a.budget)
    print("rows at that budget: %d, after keeping the newest per backend: %d"
          % (len(rows), len(chosen)))
    print("budgets already in dest: %s" % sorted(b for b in have if b))
    for r in chosen:
        print("   %-24s acc=%-7s s/epoch=%s"
              % (r["framework"] + "/" + r["backend"], r["accuracy_pct"], r["runtime_median_s"]))
    if not a.apply:
        print("\nDry run. Nothing written. Re-run with --apply to perform the merge.")
        return

    bak = "%s.before_merge_%s" % (a.dest, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    shutil.copy(a.dest, bak)
    print("\nbackup: %s" % bak)

    src.close(); dst.close()
    w = sqlite3.connect(a.dest)
    cols = [r[1] for r in w.execute("PRAGMA table_info(conditions)")]
    ins = [c for c in cols if c != "id"]
    n = 0
    for r in chosen:
        w.execute("INSERT INTO conditions (%s) VALUES (%s)"
                  % (",".join(ins), ",".join("?" * len(ins))),
                  [r[c] for c in ins])
        n += 1
    w.commit()
    after = w.execute("SELECT COUNT(*) FROM conditions WHERE task='training'").fetchone()[0]
    print("inserted %d rows; destination now has %d training rows" % (n, after))
    if w.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        sys.exit("ABORT: destination is malformed after the merge -- restore %s" % bak)
    print("integrity: ok")


if __name__ == "__main__":
    main()
