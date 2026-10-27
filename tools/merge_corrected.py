"""Merge the CPU-corrected inference/scalability sessions into the canonical
results database, and replace the fabricated 0.0 training memory with NULL.

Usage: python merge_corrected.py <target.db> <session.db> [<session.db> ...]
Refuses a session whose machine differs from the target's campaign machine,
and refuses to add a run_group that is already present.
"""
import sqlite3, sys
tgt = sys.argv[1]; srcs = sys.argv[2:]
T = sqlite3.connect(tgt)
camp = T.execute("select machine_id from conditions group by machine_id order by count(*) desc limit 1").fetchone()[0]
for s in srcs:
    S = sqlite3.connect(s)
    groups = [r[0] for r in S.execute("select distinct run_group from conditions")]
    machines = {r[0] for r in S.execute("select distinct machine_id from conditions")}
    assert machines == {camp}, f"machine mismatch in {s}: {machines} vs {camp}"
    for g in groups:
        assert T.execute("select count(*) from conditions where run_group=?", (g,)).fetchone()[0] == 0, f"{g} already present"
    for tbl in ("meta", "runs", "conditions"):
        cols = [r[1] for r in S.execute(f"pragma table_info({tbl})") if r[1] != "id"]
        rows = S.execute(f"select {','.join(cols)} from {tbl} order by id").fetchall()
        T.executemany(f"insert into {tbl} ({','.join(cols)}) values ({','.join('?'*len(cols))})", rows)
        print(s, tbl, len(rows), "rows added", groups)
# Training memory was never observed: the training path wrote peak_rss_mb=0.0
# and rss_delta_mb=0.0 as placeholders. A zero is a value, not an absence.
n1 = T.execute("update runs set peak_rss_mb=NULL, rss_delta_mb=NULL where task='training' and peak_rss_mb=0.0 and rss_delta_mb=0.0").rowcount
n2 = T.execute("update conditions set peak_rss_mb=NULL where task='training' and peak_rss_mb=0.0").rowcount
print("training memory placeholders -> NULL:", n1, "runs,", n2, "conditions")
T.commit()
print("integrity", T.execute("pragma integrity_check").fetchone()[0])
