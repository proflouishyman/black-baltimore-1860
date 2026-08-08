#!/usr/bin/env python3
"""Build a historic-to-later street name alias table for Baltimore.

Source: Gunby, "Index of Streets and Alleys", Baltimore City Archives, 1993
(msa.maryland.gov). It is a card index of street name changes, and unusually
for these scans it carries a clean text layer. Entries take the form:

    Strawberry Alley: now Dallas
    Brandy Alley: now Perry St
    German St: became Redwood St
    Potter St: now Chestnut
    Academy Alley: was John Alley
    Accomodation Alley: see Aetna Alley or Lane

This is the single fix for the project's largest source of silent loss. The
street names that fail to geocode are overwhelmingly the alleys where the Black
population actually lived, and most of them did not vanish so much as get
renamed: Strawberry, Brandy, Bottle, Happy, Honey are all present in the modern
and c.1930 data under later names.

Direction matters. "X: now Y" and "X: became Y" mean X is the older name, so we
want X -> Y. "X: was Y" is the reverse, Y is older, so we want Y -> X. "see"
is a cross-reference in either direction and is recorded both ways.

Output: data/work/street_aliases.csv with columns old, new, relation, raw
"""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geocode_1860 import norm_street

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
WORK = ROOT / "data" / "work"
SRC = RAW / "gunby.txt"

# "Name: <relation> <other name>" - stop at a year or archival citation, which
# is where the descriptive tail of an entry begins
REL_RE = re.compile(
    r"^(?P<a>[^:]{2,60}):\s*(?P<rel>now part of|became part of|now|was|became|see)\s+"
    r"(?P<b>[^,;]+?)\s*(?:\b(?:1[6-9]\d\d|20\d\d)\b|n\.d\.|$)", re.I)

# an alias target must look like a street name, not a sentence fragment
BAD_TARGET = re.compile(r"\b(?:street|streets|alley|alleys|and|from|between|"
                        r"to|the|city|part|of|no|not|never|opened|closed|"
                        r"vacated|condemned|widened|extended)\s*$", re.I)


def clean_name(s):
    s = s.strip().strip('"“”\'')
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)
    s = re.sub(r"\s+", " ", s).strip(" .,;:")
    return s


def main():
    if not SRC.exists():
        sys.exit(f"missing {SRC}: run pdftotext -layout on gunby_streets.pdf first")

    pairs, seen = [], set()
    for line in SRC.read_text(encoding="utf8", errors="ignore").split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        m = REL_RE.match(line)
        if not m:
            continue
        a, b = clean_name(m.group("a")), clean_name(m.group("b"))
        rel = m.group("rel").lower()
        if not a or not b or len(b) < 3 or BAD_TARGET.search(b):
            continue

        # "was" points backwards: the other name is the older one
        old, new = (b, a) if rel == "was" else (a, b)
        ac, bc = norm_street(old)[0], norm_street(new)[0]
        if not ac or not bc or ac == bc:
            continue

        for o, n in ([(ac, bc)] if rel != "see" else [(ac, bc), (bc, ac)]):
            key = (o, n)
            if key in seen:
                continue
            seen.add(key)
            pairs.append({"old": o, "new": n, "relation": rel, "raw": line[:120]})

    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "street_aliases.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=["old", "new", "relation", "raw"])
        w.writeheader()
        w.writerows(pairs)

    print(f"alias pairs: {len(pairs)}  (distinct old names: {len({p['old'] for p in pairs})})")
    print("\nspot check against the streets that were failing:")
    idx = {}
    for p in pairs:
        idx.setdefault(p["old"], []).append(p["new"])
    for probe in ["Strawberry alley", "Brandy alley", "Bottle alley", "Happy alley",
                  "German st", "Potter st", "Honey alley", "Lerew's alley"]:
        c = norm_street(probe)[0]
        print(f"   {probe:18s} -> {idx.get(c, ['(none)'])[:3]}")


if __name__ == "__main__":
    main()
