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

## Integrating with myalphasigma

The site's family tree already stores each brother's Big, Littles, family,
and pledge class, so the matcher's job is to produce the Big-to-Little pairs
the tree should record.

- **Names to slugs.** Brothers are keyed by a slug like `/brothers/first-last`
  (lowercase, words joined by hyphens). The matcher only compares names
  case-insensitively, so the safest setup is to fill the form dropdowns (and
  the CSV name columns) from the site's brother list, then look each name up
  by slug when importing. Any name that doesn't map to a slug should stop the
  import instead of creating a new brother.
- **Output to import.** Each line under MATCHES is one `Big -> Little` pair.
  For the tree, that becomes: set the Little's Big to that brother, and give
  the Little the Big's family. A Big with capacity 2 shows up on two lines.
  Unmatched Littles stay without a Big until a second round
  (`big_little_match_round2.py`) places them.
- **Open question: where do Littles come from?** New members aren't in the
  Brothers list yet, and Rush only holds rushees from check-ins. Decide
  whether matching runs on the Rush list (rushees with a bid) or on a new
  pledge class added to Brothers before matching. That choice sets where the
  Littles' names and slugs come from.

## Notes

- Collect rankings privately and independently.
- Set capacity 2 only for Bigs who said yes to taking two Littles.
- Unmatched people: run a second round with a short list drawn only from the leftovers.
- data/ files are fake examples. Do not commit real rankings to a public repo.
