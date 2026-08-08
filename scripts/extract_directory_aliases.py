#!/usr/bin/env python3
"""Extract street renamings from the directories' own street-directory text.

The Gunby index (1993) gives us renamings recorded a century later. But the
directories themselves record renamings *as they happened*, in the extent note
printed beside each street:

    LEREW'S AL — now Tyson street
    CARPENTER'S AL — now King-st
    HARGROVE AL, (formerly Gravel al)

This is a period-authoritative alias source, and a better one than a modern
index for our purposes, because it reflects what the name meant in the year the
directory was canvassed. It also covers small alleys that a later index may
never have bothered to record — and alleys are exactly where our coverage is
worst. "Lerew's alley" alone accounts for 69 lost 1860 residents.

Direction of the mapping matters. "X — now Y" means X is what the book calls
the street and Y is the newer name, so we want X -> Y, pointing at the name
modern geometry is likelier to use. "X (formerly Y)" is the reverse: Y is the
older name, so Y -> X.

Output: appends to data/work/street_aliases.csv, which the geocoders already
read. Existing pairs are preserved; only new ones are added.
"""

import csv
import glob
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from geocode_1860 import norm_street

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"
ALIASES = WORK / "street_aliases.csv"

# "now Tyson street", "now King-st", "now called Pearl"
NOW = re.compile(r"\bnow(?:\s+called)?\s+([A-Z][A-Za-z'’\.\- ]{2,28})", re.I)
# "(formerly Gravel al)", "late Gravel alley"
FORMER = re.compile(r"\b(?:formerly|late)\s+([A-Z][A-Za-z'’\.\- ]{2,28})", re.I)

STOP = re.compile(r"^(the|and|from|to|of|going|between|north|south|east|west|"
                  r"near|part|opened|closed|a|an)\b", re.I)


def clean(s):
    s = re.sub(r"\s+", " ", s).strip(" .,;:-")
    # cut at a trailing clause the regex may have swallowed
    s = re.split(r"\b(?:from|to|between|going|near|north|south|east|west)\b", s, 1)[0]
    return s.strip(" .,;:-")


def main():
    pairs, seen = [], set()
    if ALIASES.exists():
        for r in csv.DictReader(open(ALIASES)):
            seen.add((r["old"], r["new"]))

    files = sorted(glob.glob(str(WORK / "street_extents_*.csv")))
    found = 0
    for f in files:
        for r in csv.DictReader(open(f)):
            street, extent = r["street"], r.get("extent") or ""
            if not extent:
                continue
            for rx, reverse in ((NOW, False), (FORMER, True)):
                m = rx.search(extent)
                if not m:
                    continue
                other = clean(m.group(1))
                if not other or STOP.match(other):
                    continue
                a, b = (other, street) if reverse else (street, other)
                ac, bc = norm_street(a)[0], norm_street(b)[0]
                if not ac or not bc or ac == bc:
                    continue
                found += 1
                if (ac, bc) in seen:
                    continue
                seen.add((ac, bc))
                pairs.append({"old": ac, "new": bc,
                              "relation": "formerly" if reverse else "now",
                              "raw": f"{street}: {extent[:90]}"})

    if pairs:
        exists = ALIASES.exists()
        with ALIASES.open("a", newline="", encoding="utf8") as fh:
            w = csv.DictWriter(fh, fieldnames=["old", "new", "relation", "raw"])
            if not exists:
                w.writeheader()
            w.writerows(pairs)

    print(f"extent files read       : {len(files)}")
    print(f"rename notes found      : {found}")
    print(f"new alias pairs added   : {len(pairs)}")
    for p in pairs[:12]:
        print(f"    {p['old']:18s} -> {p['new']:18s} ({p['relation']})")


if __name__ == "__main__":
    main()
