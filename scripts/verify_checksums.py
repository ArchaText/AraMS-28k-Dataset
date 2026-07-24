#!/usr/bin/env python3
"""Verify local files against SHA256SUMS.txt."""
import hashlib, sys
from pathlib import Path

def sha256_of(path, chunk_size=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

def main(sums_file="./SHA256SUMS.txt"):
    ok, bad, missing = [], [], []
    for line in Path(sums_file).read_text().splitlines():
        if not line.strip():
            continue
        expected, fname = line.split(maxsplit=1)
        fname = fname.strip()
        if not Path(fname).exists():
            missing.append(fname)
            continue
        actual = sha256_of(fname)
        (ok if actual == expected else bad).append(fname)

    print(f"OK: {len(ok)}  MISMATCH: {len(bad)}  MISSING: {len(missing)}")
    for f in bad:
        print(f"  [MISMATCH] {f}")
    for f in missing:
        print(f"  [MISSING]  {f}")
    sys.exit(1 if bad or missing else 0)

if __name__ == "__main__":
    main()
