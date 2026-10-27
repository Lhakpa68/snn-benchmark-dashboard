#!/usr/bin/env python3
"""SNN CPU benchmark suite, command-line entry point.

  python run.py check          what is installed, and what will run
  python run.py validate       equivalence check against a reference implementation
  python run.py bench          the full experiment (this is the one you want)
  python run.py bench --quick  a short version, for confirming it works end to end
  python run.py analyse        statistics and result tables from the database
"""
from __future__ import annotations
import argparse, json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import snnbench.config as C


def cmd_check(a):
    from snnbench import machine, registry
    m, p = machine.profile(), machine.versions()
    print("\nMACHINE")
    for k, v in m.items():
        print(f"  {k:<15} {v}")
    print("\nPACKAGES")
    for k, v in p.items():
        print(f"  {k:<15} {v}")
    print("\nFRAMEWORKS AND BACKENDS")
    runnable = 0
    for row in registry.inventory():
        mark = "OK " if row["importable"] else "-- "
        print(f"  {mark}{row['label']:<14} {row['version_or_reason']}")
        for b in row["backends"]:
            state = "available" if b["available"] else f"UNAVAILABLE: {b['reason']}"
            runnable += int(b["available"])
            print(f"       {b['key']:<16} {state}")
            if b["note"]:
                print(f"       {'':<16} note: {b['note']}")
    print(f"\n{runnable} execution backends will be measured.")
    if runnable < 4:
        print("\nFewer than four backends are available. Install the missing "
              "simulators before running the full experiment:")
        print("  pip install brian2 nest-simulator nengo snntorch spikingjelly norse")


def cmd_validate(a):
    from snnbench import registry
    rows = registry.validate(n=a.size)
    print(f"\nEquivalence validation at N={a.size}, tolerance {35}% of the "
          f"reference firing rate\n")
    print(f"  {'simulator/backend':<30} {'status':<16} {'rate Hz':>9} {'ref Hz':>9} {'rel':>7}")
    for r in rows:
        name = f"{r['framework']}/{r.get('backend') or '-'}"
        print(f"  {name:<30} {r['status']:<16} "
              f"{r.get('rate_hz','-'):>9} {r.get('ref_rate_hz','-'):>9} "
              f"{r.get('rel_diff','-'):>7}"
              + (f"   {r['reason']}" if r.get("reason") else ""))
    bad = [r for r in rows if r["status"] in ("rate mismatch", "error")]
    print(f"\n{len(rows)-len(bad)} of {len(rows)} entries passed or were skipped cleanly.")
    if bad:
        print("Entries needing attention are listed above with a reason.")


def cmd_bench(a):
    from snnbench import runner
    tasks = tuple(a.tasks.split(",")) if a.tasks else ("inference", "scalability", "training")
    sizes = [int(x) for x in a.sizes.split(",")] if a.sizes else None
    if a.quick:
        tasks = ("inference", "scalability")
        sizes = [100, 500]
        a.warmup, a.measured = 1, 2
    runner.run(tasks=tasks, sizes=sizes, warmup=a.warmup, measured=a.measured,
               train_preset=a.preset, train_override=_train_override(a),
               only=set(a.only.split(",")) if a.only else None,
               only_backends=set(a.backends.split(",")) if a.backends else None)


def cmd_analyse(a):
    from snnbench import analyse
    analyse.main(pathlib.Path(a.db) if a.db else C.DB_PATH)


def _train_override(a):
    """Explicit training-size overrides. The preset stays the label; these let
    one simulator's cost be measured at a size that fits the time available,
    with the size recorded on the row so nothing is compared across sizes by
    accident."""
    keys = dict(train_n="train_n", test_n="test_n", hidden="hidden", epochs="epochs")
    out = {k: getattr(a, k, None) for k in keys}
    out = {k: v for k, v in out.items() if v is not None}
    return out or None


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=False)

    sub.add_parser("check").set_defaults(fn=cmd_check)

    v = sub.add_parser("validate"); v.add_argument("--size", type=int, default=500)
    v.set_defaults(fn=cmd_validate)

    b = sub.add_parser("bench")
    b.add_argument("--tasks", default=None,
                   help="comma-separated: inference,scalability,training")
    b.add_argument("--sizes", default=None, help="comma-separated network sizes")
    b.add_argument("--warmup", type=int, default=None)
    b.add_argument("--measured", type=int, default=None)
    b.add_argument("--preset", default=C.DEFAULT_TRAIN_PRESET,
                   choices=list(C.TRAIN_PRESETS))
    b.add_argument("--train-n", type=int, default=None)
    b.add_argument("--test-n", type=int, default=None)
    b.add_argument("--hidden", type=int, default=None)
    b.add_argument("--epochs", type=int, default=None)
    b.add_argument("--only", default=None, help="comma-separated simulator keys")
    b.add_argument("--backends", default=None,
                   help="comma-separated backend keys, e.g. cpp_standalone")
    b.add_argument("--quick", action="store_true",
                   help="short end-to-end confirmation run, not thesis data")
    b.set_defaults(fn=cmd_bench)

    an = sub.add_parser("analyse"); an.add_argument("--db", default=None)
    an.set_defaults(fn=cmd_analyse)

    a = p.parse_args()

    # Pressing Run in an IDE passes no arguments. Rather than exiting with an
    # argparse usage error, which looks like a crash, show the environment
    # report and say what to do next.
    if not getattr(a, "cmd", None):
        cmd_check(a)
        print("\n" + "=" * 66)
        print(" No command was given, so the environment report above is all")
        print(" that ran. Nothing was measured and nothing was changed.")
        print("=" * 66)
        print("\n To run the experiment, use RUN_ME.py, or pass a command:\n")
        print("   python run.py bench --quick     short check that it all works")
        print("   python run.py bench             the real run")
        print("   python run.py validate          equivalence check only")
        print("   python run.py analyse           statistics from an existing database")
        print("\n In PyCharm: right-click RUN_ME.py in the project tree and")
        print(" choose Run. It takes no arguments.\n")
        return

    a.fn(a)


if __name__ == "__main__":
    main()
