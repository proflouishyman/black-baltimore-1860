#!/usr/bin/env python3
"""Geocode the 1842 Black-householder records to block faces.

Matchett's 1842 predates systematic house numbering in Baltimore, so it gives
relative addresses instead of numbers:

    Bordley James, labourer, Pitt st w of Ann
    Barney Philip, caulker, w side Strawberry al n of Gough st

There is no number to interpolate, so the 1860 method does not apply. What the
book does give is a *block face*: a named street, a named cross street, and a
bearing from that corner. That resolves to the stretch of one street between
two intersections, which in dense antebellum Baltimore is a short run.

Placement:
  1. Intersect the street with its cross street to get the corner.
  2. Walk along the street in the stated compass bearing.
  3. Stop partway to the next intersection, so the point sits in the block
     rather than on the corner.
  4. If the book also gives a side of the street, offset perpendicular to the
     line on that side.

This is deliberately coarser than the 1860 output and is labelled as such:
every point carries confidence "block_face", or "corner" where the entry names
an intersection outright. It should never be presented as a house location.

Output: data/work/people_1842_geocoded.geojson (EPSG:4326)
"""

import csv
from bisect import bisect_left, bisect_right
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point
from rapidfuzz import process as fuzzproc

from geocode_1860 import (norm_street, load_streets, CRS_M, WARD_DIR,
                          load_aliases, resolve_street)

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"

YEARS = {
    "1842": {"people": "matchettsbaltimo1842balt_people.csv",
             "wards": "baltimore_wards_1841_1845.shp"},
    # our own OCR of the 1822 volume placed only 8 of 213; the AfriGeneas hand
    # transcription of the same book is used instead, and 1819 exists only there
    "1822": {"people": "afrigeneas_1822_people.csv",
             "wards": "baltimore_wards_1818_1831.shp"},
    "1819": {"people": "afrigeneas_1819_people.csv",
             "wards": "baltimore_wards_1818_1831.shp"},
}
BLOCK_FRACTION = 0.4      # how far into the block to sit, 0 = on the corner
MAX_STEP = 55.0           # metres; keeps huge suburban blocks from overshooting
MIN_STEP = 12.0
SIDE_OFFSET = 7.0         # metres perpendicular, when a side is named


def intersection_table(streets):
    """Distances, along each street, at which any other street crosses it.

    Used to find where the current block ends. Built once with a spatial index,
    since testing every street against every other is needlessly quadratic."""
    names = list(streets)
    gdf = gpd.GeoDataFrame({"core": names},
                           geometry=[streets[n] for n in names], crs=f"EPSG:{CRS_M}")
    sindex = gdf.sindex
    table = defaultdict(list)
    for i, core in enumerate(names):
        geom = streets[core]
        for j in sindex.query(geom, predicate="intersects"):
            if j == i:
                continue
            inter = geom.intersection(gdf.geometry.iloc[j])
            if inter.is_empty:
                continue
            pts = [inter] if inter.geom_type == "Point" else \
                  [g for g in getattr(inter, "geoms", []) if g.geom_type == "Point"]
            for p in pts:
                table[core].append(geom.project(p))
    for core in table:
        table[core] = sorted(set(round(d, 2) for d in table[core]))
    return table


def bearing_sign(geom, d0, bearing):
    """Which way along the line is 'north' (or s/e/w) from distance d0?

    Returns +1 or -1, or 0 if the bearing cannot be resolved."""
    probe = min(20.0, geom.length / 20 or 1.0)
    a = geom.interpolate(max(0.0, d0 - probe))
    b = geom.interpolate(min(geom.length, d0 + probe))
    dx, dy = b.x - a.x, b.y - a.y
    b = bearing.lower()[:1]
    if b == "n":
        return 1 if dy > 0 else -1
    if b == "s":
        return 1 if dy < 0 else -1
    if b == "e":
        return 1 if dx > 0 else -1
    if b == "w":
        return 1 if dx < 0 else -1
    return 0


def next_crossing(dists, d0, sign):
    """Distance of the next intersection beyond d0 in the given direction."""
    if not dists:
        return None
    if sign > 0:
        i = bisect_right(dists, d0 + 1.0)
        return dists[i] if i < len(dists) else None
    i = bisect_left(dists, d0 - 1.0) - 1
    return dists[i] if i >= 0 else None


def offset_side(geom, d, side, sign):
    """Shift perpendicular to the street for an e/w/n/s side note."""
    if not side:
        return 0.0, 0.0
    probe = min(10.0, geom.length / 20 or 1.0)
    a = geom.interpolate(max(0.0, d - probe))
    b = geom.interpolate(min(geom.length, d + probe))
    dx, dy = b.x - a.x, b.y - a.y
    n = (dx * dx + dy * dy) ** 0.5
    if n == 0:
        return 0.0, 0.0
    # unit normal to the street
    nx, ny = -dy / n, dx / n
    s = side.lower()[:1]
    want = {"e": (1, 0), "w": (-1, 0), "n": (0, 1), "s": (0, -1)}.get(s)
    if not want:
        return 0.0, 0.0
    if nx * want[0] + ny * want[1] < 0:
        nx, ny = -nx, -ny
    return nx * SIDE_OFFSET, ny * SIDE_OFFSET


def main(year="1842"):
    cfg = YEARS[year]
    streets = load_streets(WARD_DIR / cfg["wards"])
    print(f"streets inside the 1841-45 city : {len(streets)}")
    xtab = intersection_table(streets)
    print(f"streets with known crossings    : {len(xtab)}")

    aliases = load_aliases()

    def match(name):
        return resolve_street(norm_street(name)[0], streets, aliases)

    people = list(csv.DictReader(open(WORK / cfg["people"])))
    rows = []
    miss_street, miss_cross, no_bearing = defaultdict(int), defaultdict(int), 0

    for p in people:
        if p["addr_type"] not in ("relative", "near", "corner") or not p["cross_street"]:
            continue
        s_core = match(p["street"])
        if s_core is None:
            miss_street[p["street"]] += 1
            continue
        c_core = match(p["cross_street"])
        if c_core is None:
            miss_cross[p["cross_street"]] += 1
            continue

        geom, cross = streets[s_core], streets[c_core]
        inter = geom.intersection(cross)
        if inter.is_empty:
            miss_cross[p["cross_street"]] += 1
            continue
        pts = [inter] if inter.geom_type == "Point" else \
              [g for g in getattr(inter, "geoms", []) if g.geom_type == "Point"]
        if not pts:
            miss_cross[p["cross_street"]] += 1
            continue
        d0 = geom.project(pts[0])

        # "near X" and "cor. X and Y" name an intersection outright, with no
        # direction to walk in, so they sit on the corner itself
        if p["addr_type"] in ("near", "corner"):
            conf, d, sign = p["addr_type"], d0, 0
        else:
            sign = bearing_sign(geom, d0, p["bearing"])
        if p["addr_type"] == "relative" and sign == 0:
            conf, d = "corner", d0
            no_bearing += 1
        elif p["addr_type"] == "relative":
            nxt = next_crossing(xtab.get(s_core, []), d0, sign)
            step = MIN_STEP if nxt is None else \
                min(MAX_STEP, max(MIN_STEP, abs(nxt - d0) * BLOCK_FRACTION))
            d = max(0.0, min(geom.length, d0 + sign * step))
            conf = "block_face"

        pt = geom.interpolate(d)
        ox, oy = offset_side(geom, d, p["side"], sign)
        rows.append({
            "surname": p["surname"], "given": p["given"],
            "occupation": p["occupation"],
            "street_raw": p["street"], "cross_street": p["cross_street"],
            "bearing": p["bearing"], "side": p["side"],
            "street_matched": s_core, "confidence": conf,
            "geometry": Point(pt.x + ox, pt.y + oy),
        })

    gdf = gpd.GeoDataFrame(rows, crs=f"EPSG:{CRS_M}").to_crs(epsg=4326)
    gdf.to_file(WORK / f"people_{year}_geocoded.geojson", driver="GeoJSON")

    rel = sum(1 for p in people
              if p["addr_type"] in ("relative", "near", "corner") and p["cross_street"])
    print(f"\nplaced          : {len(gdf)} of {rel} relative records "
          f"({len(people)} parsed in total)")
    print("  confidence:", dict(gdf["confidence"].value_counts()))
    print(f"  bearing unresolved, placed on the corner: {no_bearing}")
    print(f"  street unmatched : {sum(miss_street.values())}")
    print(f"  cross unmatched  : {sum(miss_cross.values())}")
    print("\ntop unmatched streets:")
    for s, n in sorted(miss_street.items(), key=lambda t: -t[1])[:10]:
        print(f"    {n:4d}  {s}")


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "1842")
