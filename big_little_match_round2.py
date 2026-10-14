#!/usr/bin/env python3
"""
Second-round matching for leftover Bigs and Littles.

Re-runs the round 1 matcher to find who's still unmatched and how many open
spots each Big has left, then runs the same matcher on a new pair of CSVs
(shorter lists, leftover pool only) using those spots as capacity.

The capacity column in the round 2 bigs CSV is ignored and replaced with
each Big's actual remaining open spots from round 1 -- you never hand-edit
capacity numbers.

INPUT FILES

  round1_bigs.csv, round1_littles.csv   the files used for round 1
  round2_bigs.csv                        name,capacity,rank1,...,rank5
  round2_littles.csv                     name,rank1,...,rank5

  (capacity column in round2_bigs.csv is ignored, see above)
  Names in the round 2 files must be a subset of round 1's leftovers.

USAGE
  python big_little_match_round2.py round1_bigs.csv round1_littles.csv round2_bigs.csv round2_littles.csv
"""
import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MATCHER = os.path.join(HERE, "big_little_match.py")


def run_matcher(bigs_path, littles_path):
    r = subprocess.run([sys.executable, MATCHER, bigs_path, littles_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stdout + r.stderr)
    return r.stdout


def section_line(output, header):
    lines = output.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == header:
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    return lines[j].strip()
    sys.exit(f"Could not find '{header}' section in round 1 output.")


def parse_leftovers(round1_output):
    unmatched_line = section_line(round1_output, "UNMATCHED LITTLES")
    unmatched_littles = set() if unmatched_line == "none" else \
        {n.strip().lower() for n in unmatched_line.split(",")}

    open_line = section_line(round1_output, "BIGS WITH OPEN SPOTS")
    open_caps = {}
    if open_line != "none":
        for entry in open_line.split(", "):
            m = re.match(r"^(.*) \((\d+) open\)$", entry.strip())
            if not m:
                sys.exit(f"Could not parse open-spots entry: {entry!r}")
            open_caps[m.group(1).strip().lower()] = int(m.group(2))
    return unmatched_littles, open_caps


def write_adjusted_bigs(round2_bigs_path, open_caps):
    out_path = os.path.splitext(round2_bigs_path)[0] + "_adjusted.csv"
    with open(round2_bigs_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        sys.exit(f"{round2_bigs_path} is empty.")
    header, body = rows[0], rows[1:]

    unknown = []
    out_rows = []
    for row in body:
        row = [c.strip() for c in row]
        if not row or not row[0]:
            continue
        name = row[0]
        key = name.lower()
        if key not in open_caps:
            unknown.append(name)
            continue
        out_rows.append([name, open_caps[key]] + row[2:])
    if unknown:
        sys.exit("These Bigs in the round 2 file are not in round 1's "
                  "'BIGS WITH OPEN SPOTS' list: " + ", ".join(unknown))

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(out_rows)
    return out_path


def check_littles(round2_littles_path, unmatched_littles):
    with open(round2_littles_path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    unknown = []
    for row in rows[1:]:
        row = [c.strip() for c in row]
        if not row or not row[0]:
            continue
        if row[0].lower() not in unmatched_littles:
            unknown.append(row[0])
    if unknown:
        sys.exit("These Littles in the round 2 file are not in round 1's "
                  "'UNMATCHED LITTLES' list: " + ", ".join(unknown))


def main():
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    round1_bigs, round1_littles, round2_bigs, round2_littles = sys.argv[1:5]

    print("Re-running round 1 to find leftovers...\n")
    round1_output = run_matcher(round1_bigs, round1_littles)
    unmatched_littles, open_caps = parse_leftovers(round1_output)

    if not open_caps or not unmatched_littles:
        sys.exit("Round 1 has no open spots and/or no unmatched Littles. "
                  "Nothing to do for round 2.")

    check_littles(round2_littles, unmatched_littles)
    adjusted_bigs = write_adjusted_bigs(round2_bigs, open_caps)
    print(f"Wrote capacities from round 1 leftovers to {adjusted_bigs}\n")

    print("ROUND 2 RESULTS\n")
    print(run_matcher(adjusted_bigs, round2_littles))


if __name__ == "__main__":
    main()
