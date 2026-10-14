# Big/Little Matcher

Bigs-propose stable matching (Gale-Shapley). Bigs get the best result any stable
matching allows. Littles keep a veto: a pair is allowed only if both people
listed each other in their top 10.

## Setup (VS Code terminal)

    python -m venv .venv
    source .venv/bin/activate        # Windows: .venv\Scripts\activate
    pip install -r requirements.txt

numpy and scipy are optional. Without them the matcher still works but skips
the "most matches possible" comparison.

## Test with fake data first

    python sandbox_test.py                          # 20 Bigs, 27 Littles
    python sandbox_test.py --bigs 35 --littles 27
    python sandbox_test.py --two-every 3            # every 3rd Big takes 2
    python sandbox_test.py --runs 200               # stress test, prints failures only

## Run on real data

Fill in data/bigs.csv and data/littles.csv (examples are included), then:

    python big_little_match.py data/bigs.csv data/littles.csv

## Collect rankings with Google Forms

1. Open google_form/create_forms.gs, paste it into a new project at
   https://script.google.com, fill in the BIGS and LITTLES name lists, and run
   createForms. The log shows the link for Bigs, the link for Littles, and the
   responses Sheet.
2. Send each link to its group. People sign in with Google, pick their name,
   and choose up to 10 people from dropdowns (1st choice, 2nd choice, ...).
   They can edit their answers until you close the form (Responses tab >
   turn off "Accepting responses").
3. In the Sheet, download each tab as CSV (File > Download > .csv): the two
   response tabs and the Roster tab. Then:

       python convert_form_responses.py bigs_responses.csv littles_responses.csv roster.csv
       python big_little_match.py data/real_bigs.csv data/real_littles.csv

   The converter lists who hasn't submitted, who ranked fewer than 10, and
   which email submitted each name. If someone picked the same person twice,
   it keeps the higher pick and tells you. It stops if two responses use the
   same name. Delete the wrong row in the Sheet, download again, and rerun.

## File formats

bigs.csv:     name,capacity,rank1,...,rank10   (capacity 1 or 2, blank = 1)
littles.csv:  name,rank1,...,rank10

Names must match between files (capitalization ignored). Leave unused rank cells empty.

## Notes

- Collect rankings privately and independently.
- Set capacity 2 only for Bigs who said yes to taking two Littles.
- Unmatched people: run a second round with a short list drawn only from the leftovers.
- data/ files are fake examples. Do not commit real rankings to a public repo.
