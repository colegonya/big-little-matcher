#!/usr/bin/env python3
"""
Sandbox for big_little_match.py. Generates fake rankings, runs the matcher,
and independently checks the result. Nothing here touches real data.

Put this file in the same folder as big_little_match.py, then:

  python sandbox_test.py                          # 20 Bigs, 27 Littles
  python sandbox_test.py --bigs 35 --littles 27   # try other sizes
  python sandbox_test.py --two-every 3            # every 3rd Big takes 2
  python sandbox_test.py --skew 0                 # no popularity skew
  python sandbox_test.py --runs 200               # repeat with 200 seeds, only report failures

Fake files are written to ./sandbox/ so you can open them and see the format.
"""
import argparse
import csv
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MATCHER = os.path.join(HERE, "big_little_match.py")
OUT = os.path.join(HERE, "sandbox")


def ranked(pool, weights, k, rng):
    pool, weights, out = list(pool), list(weights), []
    for _ in range(min(k, len(pool))):
        i = rng.choices(range(len(pool)), weights)[0]
        out.append(pool.pop(i))
        weights.pop(i)
    return out


def make_data(n_bigs, n_lit, two_every, skew, top_k, seed):
    rng = random.Random(seed)
    bigs = [f"Big{i + 1}" for i in range(n_bigs)]
    lits = [f"Little{i + 1}" for i in range(n_lit)]
    # skew > 0 means early names are more popular. 0 means everyone equal.
    bw = [1 / (i + 1) ** skew for i in range(n_bigs)]
    lw = [1 / (i + 1) ** skew for i in range(n_lit)]
    big_rows, lit_rows = [], []
    for i, b in enumerate(bigs):
        cap = 2 if two_every and i % two_every == 0 else 1
        big_rows.append([b, cap] + ranked(lits, lw, top_k, rng))
    for l in lits:
        lit_rows.append([l] + ranked(bigs, bw, top_k, rng))
    return big_rows, lit_rows


def write_csvs(big_rows, lit_rows, folder):
    os.makedirs(folder, exist_ok=True)
    k = max(len(r) for r in big_rows) - 2
    bp, lp = os.path.join(folder, "bigs.csv"), os.path.join(folder, "littles.csv")
    with open(bp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "capacity"] + [f"rank{i}" for i in range(1, k + 1)])
        w.writerows(big_rows)
    with open(lp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name"] + [f"rank{i}" for i in range(1, k + 1)])
        w.writerows(lit_rows)
    return bp, lp


def run_matcher(bp, lp):
    r = subprocess.run([sys.executable, MATCHER, bp, lp],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stdout + r.stderr
    return r.stdout, None


def check(big_rows, lit_rows, output):
    """Return a list of problems. Empty list means the result is valid and stable."""
    bigs = {r[0]: (int(r[1]), [x for x in r[2:] if x]) for r in big_rows}
    lit = {r[0]: [x for x in r[1:] if x] for r in lit_rows}
    match = {}
    for line in output.splitlines():
        g = re.match(r"\s+(\S+)  ->  (\S+)$", line)
        if g:
            match[g.group(2)] = g.group(1)
    problems = []
    load = {}
    for l, b in match.items():
        load[b] = load.get(b, 0) + 1
        if b not in lit[l] or l not in bigs[b][1]:
            problems.append(f"{b}-{l} is not a mutual pair")
    for b, n in load.items():
        if n > bigs[b][0]:
            problems.append(f"{b} has {n} Littles but capacity {bigs[b][0]}")
    for b, (cap, plist) in bigs.items():
        mine = [l for l, x in match.items() if x == b]
        for l in plist:
            if b not in lit[l] or match.get(l) == b:
                continue
            big_wants = len(mine) < cap or any(plist.index(l) < plist.index(x) for x in mine)
            lit_wants = l not in match or lit[l].index(b) < lit[l].index(match[l])
            if big_wants and lit_wants:
                problems.append(f"blocking pair: {b} and {l}")
    return problems, len(match)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bigs", type=int, default=20)
    p.add_argument("--littles", type=int, default=27)
    p.add_argument("--two-every", type=int, default=3,
                   help="every Nth Big takes 2 Littles (0 = nobody does)")
    p.add_argument("--skew", type=float, default=0.5,
                   help="popularity skew, 0 = none, 1 = strong")
    p.add_argument("--top", type=int, default=10, help="length of each ranking")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--runs", type=int, default=1,
                   help="if above 1, repeat with many seeds and report failures only")
    a = p.parse_args()

    if not os.path.exists(MATCHER):
        sys.exit(f"Can't find {MATCHER}. Keep both files in the same folder.")

    if a.runs > 1:
        bad = 0
        for s in range(a.seed, a.seed + a.runs):
            br, lr = make_data(a.bigs, a.littles, a.two_every, a.skew, a.top, s)
            bp, lp = write_csvs(br, lr, OUT)
            out, err = run_matcher(bp, lp)
            if err:
                print(f"seed {s}: matcher crashed\n{err}")
                bad += 1
                continue
            problems, _ = check(br, lr, out)
            if problems:
                bad += 1
                print(f"seed {s}: {problems}")
        print(f"{a.runs} runs, {bad} failed")
        sys.exit(1 if bad else 0)

    br, lr = make_data(a.bigs, a.littles, a.two_every, a.skew, a.top, a.seed)
    bp, lp = write_csvs(br, lr, OUT)
    print(f"Fake data written to {OUT}\n")
    out, err = run_matcher(bp, lp)
    if err:
        sys.exit(err)
    print(out)
    problems, n = check(br, lr, out)
    print("INDEPENDENT CHECK")
    if problems:
        print("  FAILED")
        for x in problems:
            print("  -", x)
        sys.exit(1)
    print(f"  OK: {n} matches, all mutual, capacities respected, no blocking pairs")


if __name__ == "__main__":
    main()
