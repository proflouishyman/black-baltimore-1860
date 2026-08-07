#!/usr/bin/env python3
"""Geocode the 1860 Black-resident directory records to points.

Method, and why it sidesteps the 1880s renumbering entirely:

  1. Wood's 1860 Street Directory tells us which house number stood at each
     cross street, in 1860 numbering (scripts/extract_anchors.py).
  2. We locate those intersections geometrically, by intersecting the two
     streets' centrelines.
  3. A person's house number is then placed by interpolating *between the two
     bracketing anchors*, along the street. At no point is an 1860 number
     compared to a modern one.

PROVISIONAL GEOMETRY. This first pass uses modern Baltimore centrelines, which
are known to be wrong in specific, spatially clustered ways: the Jones Falls
corridor was buried, the harbour was filled, urban renewal cleared downtown
blocks, and most of the alleys these people actually lived on no longer exist.
Every output point therefore carries a `confidence` field, and streets that
fail to match modern data are reported rather than silently dropped, because a
missing alley is a silently thinned neighbourhood, not a visible error. Replace
the centreline source with a georeferenced period map before publishing.

Output: data/work/people_1860_geocoded.geojson (EPSG:4326)
"""

import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely.ops import linemerge, unary_union
from rapidfuzz import process as fuzzproc

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"
RAW = ROOT / "data" / "raw"
CRS_M = 6487          # NAD83(2011) / Maryland, metres

# street-type words to drop when comparing 1860 names to modern ones
# Longest forms first: alternation is ordered, so a bare "AL" listed before
# "ALY" would strip only the "AL" and leave a stray "Y". HUE writes alleys as
# "Aly", the 1860 book writes "al", and modern data writes "ALLEY".
SUFFIX = (r"(?:STREET|ST|AVENUE|AVE|AV|ALLEY|ALY|AL|LANE|LA|ROAD|RD|COURT|CT|"
          r"PLACE|PL|WHARF|WHF|SQUARE|SQ|TERRACE|TER|BOULEVARD|BLVD|DRIVE|DR|"
          r"PARKWAY|PKWY|HIGHWAY|HWY|CIRCLE|CIR|TURNPIKE|PIKE|WAY|RUN)")
DIRS = {"N": "N", "S": "S", "E": "E", "W": "W", "NORTH": "N", "SOUTH": "S",
        "EAST": "E", "WEST": "W"}


def norm_street(raw):
    """Reduce a street name to (core, direction) for matching across sources.

    Handles the 1860 book's forms ('CHARLES (N.)', 'BALTIMORE, (W)',
    'HARMONY LA'), the directory entries' forms ('s Castle al', 'L. McElderry')
    and modern ROAD_NAME forms ('N CHARLES ST')."""
    if not raw:
        return "", ""
    s = raw.upper().replace(".", " ").replace(",", " ")
    s = re.sub(r"[^A-Z0-9' ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    direction = ""
    # trailing parenthetical or bare direction token, e.g. "CHARLES (N)" -> N
    m = re.search(rf"\b({'|'.join(DIRS)})\b\s*$", s)
    if m and len(s.split()) > 1:
        direction = DIRS[m.group(1)]
        s = s[:m.start()].strip()
    # leading direction, e.g. "N CHARLES ST" or "s Castle al"
    m = re.match(rf"^({'|'.join(DIRS)})\b\s+(.+)$", s)
    if m and len(m.group(2).split()) >= 1:
        direction = direction or DIRS[m.group(1)]
        s = m.group(2)

    s = re.sub(rf"\b{SUFFIX}\b", " ", s)
    s = re.sub(r"^L\b|^LITTLE\b", "LITTLE", s)      # "L. McElderry" = Little
    s = re.sub(r"\s+", " ", s).strip()
    return s, direction


HUE_SHP = RAW / "hue" / "HUE_Baltimore_Streets" / "CPE_Baltimore_Streets_HUE_v1.shp"
WARD_SHP = RAW / "hue" / "HUE_Baltimore_Wards" / "baltimore_wards_1846_1860.shp"


def city_limits():
    """The 1846-1860 ward polygons dissolved into the city boundary.

    Street geometry must be clipped to this before anything is placed on it.
    The street file is a c.1930 survey, by which date arteries like Harford
    Avenue ran miles past the 1860 city line. Proportional placement along an
    unclipped street therefore flings residents into what was open country in
    1860. Everyone in this directory lived inside these wards, so the boundary
    is the correct domain, not a cosmetic crop."""
    wg = gpd.read_file(WARD_SHP).to_crs(epsg=CRS_M)
    return unary_union(wg.geometry.values).buffer(0)


def load_streets():
    """One merged geometry per normalised street name.

    Primary source is the HUE Baltimore street file (Center for Population
    Economics, ICPSR 35617): a circa-1930 grid, roughly half of it hand
    digitised off period maps. It is preferred over modern centrelines for one
    decisive reason: it still carries the alleys. Camel St, Pin Aly and Welcome
    Aly are all present there and absent from modern data, and those alleys are
    where much of the Black population actually lived, so using modern data
    alone silently thins exactly the densest neighbourhoods.

    Modern centrelines are then layered underneath, supplying only names HUE
    does not have, so nothing is lost by the swap."""
    buckets = defaultdict(list)
    source_of = {}
    city = city_limits()

    hue = gpd.read_file(HUE_SHP).to_crs(epsg=CRS_M)
    for name, geom in zip(hue["Full_Name"], hue.geometry):
        core, _d = norm_street(name)
        if core:
            buckets[core].append(geom)
            source_of.setdefault(core, "hue")

    gdf = gpd.read_file(RAW / "balt_streets.geojson").to_crs(epsg=CRS_M)
    gdf = gdf[gdf["ROAD_NAME"].notna()]
    for name, geom in zip(gdf["ROAD_NAME"], gdf.geometry):
        core, _d = norm_street(name)
        if core and core not in source_of:
            buckets[core].append(geom)
            source_of[core] = "modern"

    merged = {}
    for core, geoms in buckets.items():
        g = unary_union(geoms).intersection(city)
        if g.is_empty:
            continue
        # linemerge rejects a geometry that is already a single LineString
        if g.geom_type == "MultiLineString":
            g = linemerge(g)
        if g.geom_type == "MultiLineString":
            # linear referencing needs a single line; take the longest run
            g = max(g.geoms, key=lambda p: p.length)
        if g.geom_type == "LineString" and g.length > 0:
            merged[core] = g
    return merged


def resolve_intersections(street_geom, anchors, streets):
    """Locate each cross street on this street, as a distance along the line.

    A cross street can touch the same street more than once, so candidates are
    disambiguated greedily using the directory's own printed row order (`seq`):
    we walk the anchors in book order and always take the nearest candidate
    that lies further along the line than the previous one."""
    placed = []
    last = -1.0
    for a in anchors:
        core, _d = norm_street(a["cross_street"])
        cross = streets.get(core)
        if cross is None:
            hit = fuzzproc.extractOne(core, list(streets), score_cutoff=90)
            cross = streets[hit[0]] if hit else None
        if cross is None:
            continue
        inter = street_geom.intersection(cross)
        if inter.is_empty:
            continue
        pts = [inter] if inter.geom_type == "Point" else \
              [g for g in getattr(inter, "geoms", []) if g.geom_type == "Point"]
        if not pts:
            continue
        ds = sorted(street_geom.project(p) for p in pts)
        forward = [d for d in ds if d > last]
        d = forward[0] if forward else ds[0]
        last = max(last, d)
        placed.append({"seq": a["seq"], "dist": d,
                       "left": a["left_no"], "right": a["right_no"],
                       "cross": a["cross_street"]})
    return placed


def build_ladders(placed):
    """Two monotone number->distance ladders, one per side of the street."""
    out = {}
    for side in ("left", "right"):
        pts = []
        for p in placed:
            v = p[side]
            if v and v.isdigit():
                pts.append((int(v), p["dist"]))
        pts.sort(key=lambda t: t[0])
        # keep strictly increasing distance so interpolation stays sane
        clean, lastd = [], None
        for num, d in pts:
            if lastd is None or d > lastd:
                clean.append((num, d))
                lastd = d
        out[side] = clean
    return out


def interpolate(ladder, house_no):
    """Return (distance_along_line, confidence) for a house number."""
    if not ladder:
        return None, None
    if len(ladder) == 1:
        return ladder[0][1], "single_anchor"
    for (n0, d0), (n1, d1) in zip(ladder, ladder[1:]):
        if n0 <= house_no <= n1:
            if n1 == n0:
                return d0, "bracketed"
            f = (house_no - n0) / (n1 - n0)
            return d0 + f * (d1 - d0), "bracketed"
    # outside the anchored range: extrapolate from the nearest pair
    if house_no < ladder[0][0]:
        (n0, d0), (n1, d1) = ladder[0], ladder[1]
    else:
        (n0, d0), (n1, d1) = ladder[-2], ladder[-1]
    if n1 == n0:
        return d0, "extrapolated"
    f = (house_no - n0) / (n1 - n0)
    return d0 + f * (d1 - d0), "extrapolated"


def main():
    streets = load_streets()
    print(f"modern streets merged      : {len(streets)}")

    anchors_by_street = defaultdict(list)
    for r in csv.DictReader(open(WORK / "street_anchors.csv")):
        r["seq"] = int(r["seq"])
        anchors_by_street[r["street"]].append(r)
    for v in anchors_by_street.values():
        v.sort(key=lambda r: r["seq"])

    # resolve each 1860 street to modern geometry + its number ladders
    resolved, unmatched_streets = {}, []
    for st, anchors in anchors_by_street.items():
        core, _d = norm_street(st)
        geom = streets.get(core)
        if geom is None:
            hit = fuzzproc.extractOne(core, list(streets), score_cutoff=92)
            if hit:
                geom = streets[hit[0]]
        if geom is None:
            unmatched_streets.append(st)
            continue
        placed = resolve_intersections(geom, anchors, streets)
        if not placed:
            continue
        resolved[core] = {"geom": geom, "ladders": build_ladders(placed),
                          "anchors": len(placed), "label": st}
    print(f"1860 streets with a ladder : {len(resolved)}")
    print(f"1860 streets unmatched     : {len(unmatched_streets)}")

    # Tier 2 support. Most streets in the book have no printed number table, but
    # HUE still has their geometry. Rather than drop those residents (which would
    # silently thin the alley neighbourhoods most of all), spread them along the
    # street in house-number order. The directory's extent note says which end
    # numbering starts from, so the run can be oriented rather than guessed.
    extents = {}
    for r in csv.DictReader(open(WORK / "street_extents.csv")):
        core, _d = norm_street(r["street"])
        if core and core not in extents:
            extents[core] = r["extent"].lower()

    people = list(csv.DictReader(open(WORK / "woodsbaltimoreci1860balt_people.csv")))

    # observed house-number range per street, used to scale tier-2 placement
    span = defaultdict(list)
    for p in people:
        if p["addr_type"] == "numbered" and p["house_no"].isdigit():
            core, _d = norm_street(p["street"])
            if core:
                span[core].append(int(p["house_no"]))

    def tier2(core, num):
        """Proportional placement along a street with no printed ladder."""
        geom = streets.get(core)
        if geom is None or core not in span:
            return None
        nums = span[core]
        lo, hi = min(nums), max(nums)
        if hi == lo:
            return geom.interpolate(0.5, normalized=True)
        f = (num - lo) / (hi - lo)
        # orient the run using the book's own extent note where it exists
        note = extents.get(core, "")
        a, b = Point(geom.coords[0]), Point(geom.coords[-1])
        flip = False
        if "north" in note:
            flip = a.y > b.y
        elif "south" in note:
            flip = a.y < b.y
        elif "east" in note:
            flip = a.x > b.x
        elif "west" in note:
            flip = a.x < b.x
        if flip:
            f = 1.0 - f
        return geom.interpolate(f, normalized=True)

    rows, miss_street, miss_num = [], defaultdict(int), 0
    for p in people:
        if p["addr_type"] != "numbered" or not p["house_no"].isdigit():
            miss_num += 1
            continue
        core, _d = norm_street(p["street"])
        num = int(p["house_no"])
        r = resolved.get(core)
        if r is None:
            # no printed ladder: fall back to proportional placement if the
            # street's geometry is known at all
            if core not in streets:
                hit = fuzzproc.extractOne(core, list(streets), score_cutoff=90)
                core = hit[0] if hit else core
            pt = tier2(core, num)
            if pt is None:
                miss_street[p["street"]] += 1
                continue
            rows.append({
                "surname": p["surname"], "given": p["given"],
                "occupation": p["occupation"], "house_no": num,
                "street_raw": p["street"], "street_matched": core,
                "side": "", "confidence": "street_proportional",
                "anchors_on_street": 0, "geometry": Point(pt.x, pt.y),
            })
            continue
        # odd/even side convention is not documented for 1860 Baltimore, so try
        # the side with a usable ladder and record which was used
        best = None
        for side in ("left", "right"):
            d, conf = interpolate(r["ladders"][side], num)
            if d is None:
                continue
            if best is None or (conf == "bracketed" and best[2] != "bracketed"):
                best = (side, d, conf)
        if best is None:
            miss_street[p["street"]] += 1
            continue
        side, dist, conf = best
        pt = r["geom"].interpolate(max(0.0, min(dist, r["geom"].length)))
        rows.append({
            "surname": p["surname"], "given": p["given"],
            "occupation": p["occupation"], "house_no": num,
            "street_raw": p["street"], "street_matched": r["label"],
            "side": side, "confidence": conf, "anchors_on_street": r["anchors"],
            "geometry": Point(pt.x, pt.y),
        })

    gdf = gpd.GeoDataFrame(rows, crs=f"EPSG:{CRS_M}").to_crs(epsg=4326)
    out = WORK / "people_1860_geocoded.geojson"
    gdf.to_file(out, driver="GeoJSON")

    print(f"\ngeocoded                   : {len(gdf)} of {len(people)} records")
    print(f"  skipped, no house number : {miss_num}")
    print(f"  skipped, street unmatched: {sum(miss_street.values())}")
    print("  confidence:", dict(gdf["confidence"].value_counts()))
    print("\ntop unmatched streets (these are the silent-loss risk):")
    for s, n in sorted(miss_street.items(), key=lambda t: -t[1])[:15]:
        print(f"    {n:5d}  {s}")
    pd.Series(miss_street).sort_values(ascending=False).to_csv(
        WORK / "unmatched_streets_1860.csv", header=["count"])


if __name__ == "__main__":
    main()
