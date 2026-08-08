#!/usr/bin/env python3
"""Merge every census-linkage round into one lookup the map can use.

Residents we have checked against the 1860 federal census carry more than a
name and an address: an age, a household, a recorded colour, an occupation as
the enumerator wrote it, and a ward the census assigned independently of our
geocoding. Those people should look different on the map and say more when you
hover them.

This reads all `ancestry_checks*.csv` rounds, keeps only records where the
identification was actually credible, and writes a single lookup keyed by
`year|surname|given` (lowercased). Adding another round of lookups needs no
change here: drop the CSV in and re-run.

Verification status is carried through honestly. A resident whose census ward
disagrees with ours is marked as such rather than quietly shown as confirmed,
because the disagreement is the interesting part.

Output: data/work/census_links.json
"""

import csv
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"

# only these are strong enough to show a viewer as a census match
GOOD = {"high", "medium"}


def key(year, surname, given):
    g = (given or "").strip().split()[0] if (given or "").strip() else ""
    return f"{year}|{(surname or '').strip().lower()}|{g.lower()}"


def current_wards():
    """Our ward for each 1860 resident, as the geocoder places them TODAY.

    The check CSVs record the ward we assigned at the time of the lookup, which
    goes stale the moment the geocoder is fixed. Agreement must be recomputed
    against the current placement or the map will keep reporting disagreements
    we have already corrected."""
    import geopandas as gpd
    f = WORK / "people_1860_wards.geojson"
    if not f.exists():
        return {}
    g = gpd.read_file(f)
    out = {}
    for _, r in g.iterrows():
        gv = str(r.get("given") or "").strip().split()
        k = key("1860", r.get("surname"), gv[0] if gv else "")
        w = r.get("Ward_Num")
        if w is not None and str(w) != "nan":
            out.setdefault(k, str(int(float(w))))
    return out


def main():
    out, rounds, skipped = {}, 0, 0
    live = current_wards()
    for path in sorted(glob.glob(str(WORK / "ancestry_checks*.csv"))):
        rounds += 1
        for r in csv.DictReader(open(path)):
            conf = (r.get("match_confidence") or "").strip().lower()
            found = (r.get("census_found") or "").strip().lower()
            if conf not in GOOD or found != "yes":
                skipped += 1
                continue
            k = key("1860", r.get("surname"), r.get("given"))
            recorded = (r.get("our_ward") or "").strip()
            our = live.get(k, recorded)      # current placement wins
            cen = (r.get("census_ward") or "").strip()
            agree = None
            if our and cen and our.isdigit() and cen.isdigit():
                agree = int(our) == int(cen)
            rec = {
                "ward_census": cen or None,
                "ward_ours": our or None,
                "agree": agree,
                "age": (r.get("census_age") or "").strip() or None,
                "sex": (r.get("census_sex") or "").strip() or None,
                "colour": (r.get("census_colour") or "").strip() or None,
                "occupation": (r.get("census_occupation") or "").strip() or None,
                "ward_when_checked": recorded or None,
                "confidence": conf,
                "url": (r.get("record_url") or "").strip() or None,
                "accessed": (r.get("accessed") or "").strip() or None,
                "notes": (r.get("notes") or "").strip()[:220] or None,
            }
            out[k] = rec

    dest = WORK / "census_links.json"
    dest.write_text(json.dumps(out, separators=(",", ":")))
    agree = sum(1 for v in out.values() if v["agree"] is True)
    disagree = sum(1 for v in out.values() if v["agree"] is False)
    print(f"rounds read      : {rounds}")
    print(f"linked residents : {len(out)}  -> {dest.name}")
    print(f"  ward agrees    : {agree}")
    print(f"  ward disagrees : {disagree}")
    print(f"  rejected (weak or not found): {skipped}")
    moved = sum(1 for v in out.values()
                if v["ward_when_checked"] and v["ward_ours"] != v["ward_when_checked"])
    if moved:
        print(f"  NOTE: {moved} residents have moved ward since they were checked "
              f"(geocoder fixes); agreement recomputed against current placement")


if __name__ == "__main__":
    main()
