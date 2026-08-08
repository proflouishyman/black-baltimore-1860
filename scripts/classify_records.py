#!/usr/bin/env python3
"""Classify every parsed directory record as resident, business or institution.

The directories do not separate these. A Black church, a Black-run eating house
and a Black labourer all sit in the same alphabetical list. But they are three
different kinds of evidence, and separating them turns one map into three:

  institution  churches, schools, cemeteries, benevolent societies. The
               infrastructure a community builds for itself, and the most
               visible claim it makes on the city's map.
  business     proprietors rather than employees: grocers, hucksters, eating
               houses, confectioners, butchers, boarding houses. Ownership,
               not just labour.
  resident     everyone else.

Classification is by occupation string and by name, so it is a heuristic and
will misfile some records. It errs toward leaving things as `resident`, since a
false institution is more misleading on a map than a missed one.

Output: data/work/record_categories.csv
    source_id, row, category, subtype
where `row` is the zero-based index into that source's *_people.csv, so the
join back is positional and needs no shared key.
"""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"

SOURCES = {
    "1819": "afrigeneas_1819_people.csv",
    "1822": "afrigeneas_1822_people.csv",
    "1842": "matchettsbaltimo1842balt_people.csv",
    "1845": "baltimoredirecto1845balt_people.csv",
    "1851": "matchettsbaltimo1851balt_people.csv",
    "1860": "woodsbaltimoreci1860balt_people.csv",
    "1868": "woodsbaltimoreci1868balt_people.csv",
}

# order matters: first match wins
INSTITUTION = [
    ("church", r"\b(church|chapel|meeting ?house|a\.? ?m\.? ?e\.?|bethel|zion)\b"),
    ("school", r"\b(school|academy|seminary|institute)\b"),
    ("cemetery", r"\b(cemeter|burial ?ground|grave ?yard)\b"),
    # "hall" is deliberately absent: it is a common surname, and in 1868 it also
    # matches a clothing advertisement ("Clothing Marble Hall") bound into the
    # listing. Precision matters more than recall here.
    ("society", r"\b(society|association|lodge|benevolent|beneficial|asylum|"
                r"orphan|home for)\b"),
]

# Institution keywords are also surnames (Church, Lodge, Chapel). An entry is
# only an institution if the keyword is part of a longer name rather than the
# whole surname, since "Church, Edward, laborer" is a man and "Bethel Church"
# is a building.
PERSON_LIKE = re.compile(r"^(mr|mrs|miss|rev|capt|dr)\.?$", re.I)

BUSINESS = [
    ("food", r"\b(grocer|grocery|eating ?house|restaurant|confection|butcher|"
             r"baker|oyster (dealer|house)|provision|fruiterer|milk ?dealer)\b"),
    ("lodging", r"\b(boarding|hotel|tavern|inn ?keeper|saloon)\b"),
    ("retail", r"\b(store|shop ?keeper|dealer|merchant|trader|variety|"
               r"second ?hand|junk|coal ?yard|wood ?yard)\b"),
    ("street trade", r"\b(huckster|pedlar|peddler|market ?dealer|vender|vendor)\b"),
    ("service", r"\b(barber|hair ?dresser|undertaker|livery|cupper|"
                r"bleeder|midwife)\b"),
]

# occupations that merely contain a business-sounding word but are wage work
NOT_BUSINESS = re.compile(r"\b(in|at|for)\s+\w+('s)?\s+(store|shop|house)\b", re.I)


def classify(surname, given, occupation):
    blob = f"{surname} {given} {occupation}".strip()
    occ = (occupation or "").strip()

    name = f"{surname} {given}".strip()
    for sub, pat in INSTITUTION:
        m = re.search(pat, name, re.I)
        if m:
            # the keyword must not BE the surname, or every Mr Church qualifies
            if m.group(0).lower() == (surname or "").strip().lower():
                continue
            # institutions do not have trades; people do
            if occ and not re.search(r"\b(colou?red|african|meth|bapt|episc|"
                                     r"presby|cath)\b", occ, re.I):
                continue
            # a person whose trade is teaching is a resident, not a school
            if sub == "school" and re.search(r"\b(teacher|professor)\b", occ, re.I):
                return "resident", ""
            if sub == "church" and re.search(r"\b(minister|preacher|sexton|clergy)\b",
                                             occ, re.I):
                return "resident", ""
            return "institution", sub

    if occ and not NOT_BUSINESS.search(occ):
        for sub, pat in BUSINESS:
            if re.search(pat, occ, re.I):
                return "business", sub
    return "resident", ""


def main():
    rows = []
    tally = {}
    for year, fname in SOURCES.items():
        path = WORK / fname
        if not path.exists():
            continue
        recs = list(csv.DictReader(open(path)))
        counts = {"institution": 0, "business": 0, "resident": 0}
        for i, r in enumerate(recs):
            cat, sub = classify(r.get("surname", ""), r.get("given", ""),
                                r.get("occupation", ""))
            counts[cat] += 1
            if cat != "resident":
                rows.append({"source_id": year, "row": i,
                             "category": cat, "subtype": sub})
        tally[year] = counts

    out = WORK / "record_categories.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=["source_id", "row", "category", "subtype"])
        w.writeheader()
        w.writerows(rows)

    print(f"{len(rows)} non-resident records -> {out.name}\n")
    print(f"{'year':6s} {'institution':>12s} {'business':>10s} {'resident':>10s}")
    for y in sorted(tally):
        c = tally[y]
        print(f"{y:6s} {c['institution']:>12d} {c['business']:>10d} {c['resident']:>10d}")

    from collections import Counter
    print("\ninstitution subtypes:",
          dict(Counter(r["subtype"] for r in rows if r["category"] == "institution")))
    print("business subtypes:  ",
          dict(Counter(r["subtype"] for r in rows if r["category"] == "business")))


if __name__ == "__main__":
    main()
