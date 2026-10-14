#!/usr/bin/env python3
"""
Big/Little matching with Bigs proposing (Gale-Shapley / Deferred Acceptance).

Bigs get the best result any stable matching allows. Littles get the worst
result any stable matching allows, but a Little can never be matched to a Big
they did not list, and no Big/Little pair will both prefer each other over
their assigned matches.

INPUT FILES (CSV, first row is a header and is skipped)

  bigs.csv     name,capacity,rank1,rank2,...,rank10
  littles.csv  name,rank1,rank2,...,rank10

  capacity is 1 or 2 (blank means 1). Leave unused rank cells empty.

RULE: a pair is allowed only if the Big is in the Little's list AND the
Little is in the Big's list. Anyone not listed is unacceptable.

USAGE
  python big_little_match.py bigs.csv littles.csv
"""
import csv
import sys
from collections import deque


def read_people(path, has_capacity):
    people = {}   # key (lowercase) -> dict
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            row = [c.strip() for c in row]
            if not row or not row[0]:
                continue
            name = row[0]
            key = name.lower()
            if key in people:
                sys.exit(f"Duplicate name in {path}: {name}")
            if has_capacity:
                cap = int(row[1]) if len(row) > 1 and row[1] else 1
                if cap not in (1, 2):
                    sys.exit(f"Capacity for {name} must be 1 or 2, got {cap}")
                prefs = row[2:]
            else:
                cap = 1
                prefs = row[1:]
            prefs = [p.lower() for p in prefs if p]
            if len(set(prefs)) != len(prefs):
                sys.exit(f"{name} lists the same person twice in {path}")
            people[key] = {"name": name, "cap": cap, "prefs": prefs}
    return people


def check_names(people, others, label, other_label):
    for p in people.values():
        for q in p["prefs"]:
            if q not in others:
                print(f"WARNING: {label} '{p['name']}' lists '{q}', "
                      f"who is not in the {other_label} file. Ignored.")


def stats(ranks):
    """ranks: list of 1-based ranks each matched person got."""
    if not ranks:
        return "no matches"
    n = len(ranks)
    top1 = sum(r == 1 for r in ranks)
    top3 = sum(r <= 3 for r in ranks)
    return (f"{n} matched | #1 choice: {top1} | top 3: {top3} | "
            f"worst: #{max(ranks)} | average rank: {sum(ranks) / n:.2f}")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    bigs = read_people(sys.argv[1], True)
    littles = read_people(sys.argv[2], False)

    check_names(bigs, littles, "Big", "Littles")
    check_names(littles, bigs, "Little", "Bigs")

    # Allowed pairs: both listed each other. Keep each Big's own order.
    allowed = {}
    for bk, b in bigs.items():
        allowed[bk] = [lk for lk in b["prefs"]
                       if lk in littles and bk in littles[lk]["prefs"]]
    rank_little = {lk: {bk: i for i, bk in enumerate(l["prefs"])}
                   for lk, l in littles.items()}

    # A Big with capacity 2 becomes two slots with the same list.
    slots = [(bk, i) for bk, b in bigs.items() for i in range(b["cap"])]
    nxt = {s: 0 for s in slots}
    held = {}  # little key -> slot
    free = deque(slots)
    while free:
        s = free.popleft()
        bk = s[0]
        if nxt[s] >= len(allowed[bk]):
            continue  # this slot ran out of options
        lk = allowed[bk][nxt[s]]
        nxt[s] += 1
        if lk not in held:
            held[lk] = s
        else:
            cur = held[lk]
            if rank_little[lk][bk] < rank_little[lk][cur[0]]:
                held[lk] = s
                free.append(cur)
            else:
                free.append(s)

    pairs = sorted(((bigs[s[0]]["name"], littles[lk]["name"], s[0], lk)
                    for lk, s in held.items()))

    print("MATCHES")
    for bn, ln, _, _ in pairs:
        print(f"  {bn}  ->  {ln}")

    matched_littles = set(held)
    filled = {}
    for lk, s in held.items():
        filled[s[0]] = filled.get(s[0], 0) + 1

    print("\nUNMATCHED LITTLES")
    um_l = [l["name"] for lk, l in littles.items() if lk not in matched_littles]
    print("  " + (", ".join(um_l) if um_l else "none"))

    print("\nBIGS WITH OPEN SPOTS")
    open_b = [f"{b['name']} ({b['cap'] - filled.get(bk, 0)} open)"
              for bk, b in bigs.items() if filled.get(bk, 0) < b["cap"]]
    print("  " + (", ".join(open_b) if open_b else "none"))

    big_ranks = [bigs[bk]["prefs"].index(lk) + 1 for _, _, bk, lk in pairs]
    little_ranks = [littles[lk]["prefs"].index(bk) + 1 for _, _, bk, lk in pairs]
    print("\nHOW HAPPY EACH SIDE IS (rank of the person they got, 1 = top choice)")
    print("  Bigs:    " + stats(big_ranks))
    print("  Littles: " + stats(little_ranks))

    # Compare with the largest number of matches possible using allowed pairs.
    try:
        import numpy as np
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import maximum_bipartite_matching
        lk_list = list(littles)
        lidx = {lk: i for i, lk in enumerate(lk_list)}
        rows, cols = [], []
        for si, s in enumerate(slots):
            for lk in allowed[s[0]]:
                rows.append(si)
                cols.append(lidx[lk])
        g = csr_matrix((np.ones(len(rows)), (rows, cols)),
                       shape=(len(slots), len(lk_list)))
        m = maximum_bipartite_matching(g, perm_type="column")
        best = int((m != -1).sum())
        print(f"\nCHECK: this run made {len(pairs)} matches. "
              f"The most possible with these lists is {best}.")
        if best > len(pairs):
            print("  Stability cost you "
                  f"{best - len(pairs)} match(es). Consider a second round "
                  "for the unmatched people.")
    except ImportError:
        print("\n(Install numpy and scipy to see the maximum possible match "
              "count: pip install numpy scipy)")


if __name__ == "__main__":
    main()
