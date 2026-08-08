#!/usr/bin/env python3
"""Summarise every census-validation round into one table the site can show.

Reads all `ancestry_checks*.csv`, recomputes ward agreement against the CURRENT
geocode (the CSVs record the ward assigned at lookup time, which goes stale as
soon as the geocoder is fixed), and measures whether mismatches are adjacent
wards or genuine misplacements by computing boundary distance from the ward
polygons rather than eyeballing a map.

Output: data/work/validation_summary.json
"""

import csv
import glob
import json
from collections import defaultdict
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"
WARDS = ROOT / "data" / "raw" / "hue" / "HUE_Baltimore_Wards" / "baltimore_wards_1846_1860.shp"

GOOD = {"high", "medium"}


def key(surname, given):
    g = (given or "").strip().split()
    return f"{(surname or '').strip().lower()}|{g[0].lower() if g else ''}"


def main():
    live, tier_of = {}, {}
    f = WORK / "people_1860_wards.geojson"
    if f.exists():
        g = gpd.read_file(f)
        for _, r in g.iterrows():
            k = key(r.get("surname"), r.get("given"))
            w = r.get("Ward_Num")
            if w is not None and str(w) != "nan":
                live.setdefault(k, int(float(w)))
                tier_of.setdefault(k, r.get("confidence"))

    wg = gpd.read_file(WARDS).to_crs(epsg=6487)
    geom = {int(r["Ward_Num"]): r.geometry for _, r in wg.iterrows()}

    def adjacent(a, b):
        if a not in geom or b not in geom:
            return None
        return geom[a].distance(geom[b]) < 1.0

    rows, by_tier = [], defaultdict(lambda: {"n": 0, "found": 0, "ward": 0,
                                             "match": 0, "adjacent": 0})
    for path in sorted(glob.glob(str(WORK / "ancestry_checks*.csv"))):
        rnd = Path(path).stem.replace("ancestry_checks", "").strip("_") or "1"
        for r in csv.DictReader(open(path)):
            k = key(r.get("surname"), r.get("given"))
            tier = (r.get("our_tier") or tier_of.get(k) or "unknown").strip()
            conf = (r.get("match_confidence") or "").strip().lower()
            found = (r.get("census_found") or "").strip().lower() == "yes" and conf in GOOD
            cen = (r.get("census_ward") or "").strip()
            our = live.get(k)
            t = by_tier[tier]
            t["n"] += 1
            match = adj = None
            if found:
                t["found"] += 1
                if cen.isdigit() and our is not None:
                    t["ward"] += 1
                    match = int(cen) == our
                    if match:
                        t["match"] += 1
                    else:
                        adj = adjacent(our, int(cen))
                        if adj:
                            t["adjacent"] += 1
            rows.append({"round": rnd, "surname": r.get("surname"),
                         "given": r.get("given"), "tier": tier,
                         "found": found, "our_ward": our,
                         "census_ward": int(cen) if cen.isdigit() else None,
                         "match": match, "adjacent": adj})

    tot = {"n": sum(t["n"] for t in by_tier.values()),
           "found": sum(t["found"] for t in by_tier.values()),
           "ward": sum(t["ward"] for t in by_tier.values()),
           "match": sum(t["match"] for t in by_tier.values()),
           "adjacent": sum(t["adjacent"] for t in by_tier.values())}
    out = {"tiers": {k: dict(v) for k, v in by_tier.items()},
           "total": tot, "records": rows}
    (WORK / "validation_summary.json").write_text(json.dumps(out, separators=(",", ":")))

    print(f"{'tier':22s} {'n':>4} {'found':>6} {'ward':>5} {'match':>6} {'adj':>4}")
    for k, v in sorted(by_tier.items()):
        print(f"{k:22s} {v['n']:>4} {v['found']:>6} {v['ward']:>5} {v['match']:>6} {v['adjacent']:>4}")
    print(f"{'TOTAL':22s} {tot['n']:>4} {tot['found']:>6} {tot['ward']:>5} "
          f"{tot['match']:>6} {tot['adjacent']:>4}")
    mism = tot["ward"] - tot["match"]
    if mism:
        print(f"\nmismatches: {mism}, of which adjacent wards: {tot['adjacent']} "
              f"({tot['adjacent']/mism*100:.0f}%)")
    if tot["n"]:
        print(f"find rate: {tot['found']}/{tot['n']} = {tot['found']/tot['n']*100:.0f}%")


if __name__ == "__main__":
    main()
