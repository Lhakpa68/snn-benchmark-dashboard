"""Part 2: regenerate Tables 19 and 20 with the EXISTING selection functions and compare
with the values published in V6. Read-only. Writes review/reproduce_output.txt."""
import io, contextlib
from _lib import *
import optimization as opt

PUB19 = {100: ('nest/threads4', .244, 'nest/threads2', .254), 500: ('snntorch/cpu', .277, None, None),
         1000: ('snntorch/cpu', .255, None, None), 5000: ('brian2/numpy', .044, 'brian2/cython', .045),
         10000: ('brian2/cython', .000, None, None)}
out = io.StringIO()
def P(*a): print(*a, file=out)

P('TABLE 19 (equal priorities 50/50/50/0, min-max)')
mism = []
for n in SIZES:
    r = opt.evaluate_four(n)
    w, ru = r['rows'][0], r['rows'][1]
    pw, ps, pr, prs = PUB19[n]
    ok = w['id'] == pw and round(w['score'], 3) == ps and (pr is None or (ru['id'] == pr and round(ru['score'], 3) == prs))
    P(f"N={n:>5} winner={w['id']} {w['score']:.4f} runner-up={ru['id']} {ru['score']:.4f} "
      f"wins={w['scenario_wins']}/{r['n_grid_points']} pareto={[x['id'] for x in r['pareto']]}  "
      f"published={pw} {ps}" + (f" / {pr} {prs}" if pr else '') + f"  -> {'MATCH' if ok else 'MISMATCH'}")
    if not ok: mism.append(('T19', n))

P('\nTABLE 20 (profile x size; * = exploratory; MM=min-max, SH=share)')
diff = []; total = 0
for n in SIZES:
    mm = opt.evaluate_profiles(n); sh = opt.evaluate_profiles(n, normalisation='share')
    for key, label, _ in opt.PROFILES:
        a, b = mm['winners'].get(key), sh['winners'].get(key)
        total += 1
        if a != b: diff.append((label, n, a, b))
        P(f'N={n:>5} {label:<22} MM={a!s:<18} SH={b!s:<18}' + ('  DIFF' if a != b else ''))
P(f'\nAgreement: {total-len(diff)} of {total} (published: 41 of 45)')
for d in diff: P('  differs:', d)
pub_diff = {('Balanced', 100), ('Accuracy + speed*', 100), ('Balanced', 5000), ('Speed + memory', 5000)}
got = {(d[0], d[1]) for d in diff}
P('Published differing set :', sorted(pub_diff)); P('Reproduced differing set:', sorted(got))
P('Same set:', got == pub_diff)
s = next(x for x in opt.evaluate_four(10000)['rows'] if x['id'] == 'brian2/cython')
P(f"\nBrian2/Cython fit R2 = {s['scaling_r2']:.4f} (published 0.45), k = {s['scaling_k']:.4f}")
P('Table 19 mismatches:', mism or 'none')
txt = out.getvalue(); print(txt)
(Path(__file__).parent / 'reproduce_output.txt').write_text(txt)
