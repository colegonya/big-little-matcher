#!/usr/bin/env python3
"""
Turn the Google Form response Sheet into the CSVs big_little_match.py reads.

In the responses Sheet, open each tab and use File > Download >
Comma-separated values (.csv). You get one file for the Bigs form, one for
the Littles form, and one for the Roster tab. Then:

  python convert_form_responses.py bigs_responses.csv littles_responses.csv roster.csv

The roster file is optional. With it, you also see who hasn't submitted yet.

Writes data/real_bigs.csv and data/real_littles.csv (ignored by git). Then run
the matcher on those two files.
"""
import csv
import os
import re
import sys

BIG_NAME_COL = "Which Big are you?"
LITTLE_NAME_COL = "Which Little are you?"
RANK_COL = re.compile(r"^(\d+)(?:st|nd|rd|th) choice$")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def read_rows(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    if not rows:
        sys.exit(f"{path} is empty.")
    return rows[0], rows[1:]


def read_responses(path, is_bigs):
    header, body = read_rows(path)
    name_col, other_col = ((BIG_NAME_COL, LITTLE_NAME_COL) if is_bigs
                           else (LITTLE_NAME_COL, BIG_NAME_COL))
    if name_col not in header:
        if other_col in header:
            sys.exit(f"{path} looks like the {'Littles' if is_bigs else 'Bigs'} "
                     "responses. Pass the Bigs file first, then the Littles file.")
        sys.exit(f"{path} has no '{name_col}' column. Is it a form response export?")
    name_i = header.index(name_col)
    email_i = header.index("Email Address") if "Email Address" in header else None
    rank_cols = sorted((int(m.group(1)), i) for i, h in enumerate(header)
                       if (m := RANK_COL.match(h)))

    people, emails = {}, {}
    for row in body:
        row += [""] * (len(header) - len(row))
        name = row[name_i].strip()
        if not name:
            continue
        email = row[email_i].strip() if email_i is not None else "?"
        emails.setdefault(name, []).append(email)
        prefs = []
        for rank, i in rank_cols:
            pick = row[i].strip()
            if not pick:
                continue
            if pick in prefs:
                print(f"NOTE: {name} picked {pick} twice. "
                      f"Kept #{prefs.index(pick) + 1}, dropped the #{rank} pick.")
                continue
            prefs.append(pick)
        people[name] = (1, prefs)  # every Big takes exactly one Little

    dupes = {n: e for n, e in emails.items() if len(e) > 1}
    if dupes:
        print(f"ERROR: more than one response for the same name in {path}:")
        for n, e in dupes.items():
            print(f"  {n}: submitted by {', '.join(e)}")
        sys.exit("Delete the wrong row(s) in the Sheet, download again, rerun.")
    return people, emails


def read_roster(path):
    header, body = read_rows(path)
    if header[:2] != ["Bigs", "Littles"]:
        sys.exit(f"{path} doesn't look like the Roster tab (expected columns Bigs, Littles).")
    bigs = [r[0].strip() for r in body if r and r[0].strip()]
    littles = [r[1].strip() for r in body if len(r) > 1 and r[1].strip()]
    return bigs, littles


def write_csv(path, people, with_cap):
    k = max([len(p) for _, p in people.values()] + [1])
    head = ["name"] + (["capacity"] if with_cap else []) + \
        [f"rank{i}" for i in range(1, k + 1)]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(head)
        for name, (cap, prefs) in sorted(people.items()):
            w.writerow([name] + ([cap] if with_cap else []) + prefs)


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    bigs, big_emails = read_responses(sys.argv[1], True)
    littles, little_emails = read_responses(sys.argv[2], False)
    roster = read_roster(sys.argv[3]) if len(sys.argv) == 4 else None

    os.makedirs(OUT_DIR, exist_ok=True)
    bp = os.path.join(OUT_DIR, "real_bigs.csv")
    lp = os.path.join(OUT_DIR, "real_littles.csv")
    write_csv(bp, bigs, True)
    write_csv(lp, littles, False)

    print()
    for side, (label, people) in enumerate((("Bigs", bigs), ("Littles", littles))):
        short = [f"{n} ({len(p)})" for n, (_, p) in sorted(people.items())
                 if len(p) < 10]
        if roster:
            missing = sorted(set(roster[side]) - set(people))
            print(f"{label}: {len(people)} of {len(roster[side])} submitted")
            print("  not submitted yet: " + (", ".join(missing) or "none"))
        else:
            print(f"{label}: {len(people)} submitted")
        print("  ranked fewer than 10: " + (", ".join(short) or "none"))
    if not roster:
        print("(Add the Roster tab CSV as a third file to see who hasn't submitted.)")

    print("\nWHO SUBMITTED EACH NAME (check for anyone answering as someone else)")
    for name, e in sorted({**big_emails, **little_emails}.items()):
        print(f"  {name}: {e[0]}")

    print(f"\nWrote {bp} and {lp}. Next:")
    print(f"  python big_little_match.py {os.path.relpath(bp)} {os.path.relpath(lp)}")


if __name__ == "__main__":
    main()
