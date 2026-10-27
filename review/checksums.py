import hashlib, os, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
out = sys.argv[1]
lines = []
for dp, dn, fn in os.walk(root):
    rel = Path(dp).relative_to(root)
    dn[:] = [d for d in dn if not (rel == Path('.') and d == 'review') and d not in ('venv', '.venv', '.dashboard_venv')]
    for f in fn:
        p = Path(dp) / f
        if p.is_symlink(): continue
        h = hashlib.sha256()
        with open(p, 'rb') as fh:
            for ch in iter(lambda: fh.read(1 << 20), b''): h.update(ch)
        lines.append(f'{h.hexdigest()}  {p.relative_to(root)}')
lines.sort(key=lambda s: s[66:])
Path(__file__).with_name(out).write_text('\n'.join(lines) + '\n')
print(len(lines), 'files ->', out)
