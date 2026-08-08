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
WARD_DIR = RAW / "hue" / "HUE_Baltimore_Wards"
WARD_SHP = WARD_DIR / "baltimore_wards_1846_1860.shp"


def city_limits(ward_shp=None):
    """The 1846-1860 ward polygons dissolved into the city boundary.

    Street geometry must be clipped to this before anything is placed on it.
    The street file is a c.1930 survey, by which date arteries like Harford
    Avenue ran miles past the 1860 city line. Proportional placement along an
    unclipped street therefore flings residents into what was open country in
    1860. Everyone in this directory lived inside these wards, so the boundary
    is the correct domain, not a cosmetic crop."""
    wg = gpd.read_file(ward_shp or WARD_SHP).to_crs(epsg=CRS_M)
    return unary_union(wg.geometry.values).buffer(0)


def load_streets(ward_shp=None):
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
    dbuckets = defaultdict(list)      # keyed by (core, direction)
    source_of = {}
    city = city_limits(ward_shp)

    hue = gpd.read_file(HUE_SHP).to_crs(epsg=CRS_M)
    for name, geom in zip(hue["Full_Name"], hue.geometry):
        core, d = norm_street(name)
        if core:
            buckets[core].append(geom)
            # HUE distinguishes the halves of a split street ("N Caroline St",
            # "S Caroline St"). Keeping them apart matters: north and south
            # Caroline are different streets with different numbering, and
            # merging them puts people on the wrong side of Baltimore street.
            if d:
                dbuckets[(core, d)].append(geom)
            source_of.setdefault(core, "hue")

    gdf = gpd.read_file(RAW / "balt_streets.geojson").to_crs(epsg=CRS_M)
    gdf = gdf[gdf["ROAD_NAME"].notna()]
    for name, geom in zip(gdf["ROAD_NAME"], gdf.geometry):
        core, d = norm_street(name)
        if core and core not in source_of:
            buckets[core].append(geom)
            if d:
                dbuckets[(core, d)].append(geom)
            source_of[core] = "modern"

    def merge(geoms):
        g = unary_union(geoms).intersection(city)
        if g.is_empty:
            return None
        if g.geom_type == "MultiLineString":
            g = linemerge(g)
        if g.geom_type == "MultiLineString":
            g = max(g.geoms, key=lambda p: p.length)
        return g if g.geom_type == "LineString" and g.length > 0 else None

    merged = {}
    for key, geoms in dbuckets.items():
        g = merge(geoms)
        if g is not None:
            merged[key] = g
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


def pick_geom(streets, core, dirn):
    """Prefer the directional half of a split street when we know which half."""
    if dirn and (core, dirn) in streets:
        return streets[(core, dirn)], (core, dirn)
    return streets.get(core), core


def load_aliases():
    """Historic street name -> later name, from the Gunby index.

    Without this, the streets that fail to match are overwhelmingly the alleys
    the Black population lived on, because most were renamed rather than
    demolished: Strawberry became Dallas, Brandy became Perry, Happy became
    Durham. Matching without aliases silently thins the densest blocks."""
    path = WORK / "street_aliases.csv"
    idx = {}
    if path.exists():
        for r in csv.DictReader(open(path)):
            idx.setdefault(r["old"], []).append(r["new"])
    return idx


def resolve_street(core, streets, aliases):
    """Map a directory street name onto a key in the geometry table."""
    if not core:
        return None
    if core in streets:
        return core
    for alt in aliases.get(core, []):
        if alt in streets:
            return alt
    names = [k for k in streets if isinstance(k, str)]
    hit = fuzzproc.extractOne(core, names, score_cutoff=92)
    if hit:
        return hit[0]
    for alt in aliases.get(core, []):
        hit = fuzzproc.extractOne(alt, names, score_cutoff=92)
        if hit:
            return hit[0]
    return None


ALIASES = {}


def resolve_intersections(street_geom, anchors, streets):
    """Locate each cross street on this street, as a distance along the line.

    A cross street can touch the same street more than once, so candidates are
    disambiguated greedily using the directory's own printed row order (`seq`):
    we walk the anchors in book order and always take the nearest candidate
    that lies further along the line than the previous one."""
    placed = []
    last = -1.0
    for a in anchors:
        ccore, cdir = norm_street(a["cross_street"])
        key = resolve_street(ccore, streets, ALIASES)
        cross = pick_geom(streets, key, cdir)[0] if key else None
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
    """Two monotone number->distance ladders, one per side of the street.

    The digitised line may run either way relative to the house numbering: on
    N Caroline, distance along the line *decreases* as numbers rise, because
    the geometry was drawn north to south. Requiring increasing distance threw
    away every anchor but the first there, collapsing the ladder to a single
    point at the wrong end of the street. So the run direction is detected and
    monotonicity enforced in whichever direction the street actually runs."""
    out = {}
    for side in ("left", "right"):
        pts = []
        for p in placed:
            v = p[side]
            if v and v.isdigit():
                pts.append((int(v), p["dist"]))
        pts.sort(key=lambda t: t[0])
        if len(pts) < 2:
            out[side] = pts
            continue
        # does distance rise or fall as the numbers rise?
        rising = sum(1 for a, b in zip(pts, pts[1:]) if b[1] > a[1])
        falling = len(pts) - 1 - rising
        sign = 1 if rising >= falling else -1
        clean, lastd = [], None
        for num, d in pts:
            if lastd is None or (d - lastd) * sign > 0:
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


YEARS = {
    # each volume geocodes against the ward boundary in force at the time:
    # Baltimore redrew its wards in 1861, between these two directories.
    "1860": {"people": "woodsbaltimoreci1860balt_people.csv",
             "anchors": "street_anchors_1860.csv",
             "extents": "street_extents_1860.csv",
             "wards": "baltimore_wards_1846_1860.shp"},
    # 1845 and 1851 print no anchor table of their own, so they borrow 1860's.
    # That is defensible because Baltimore did not renumber until the 1880s, so
    # all three volumes share one numbering scheme; it is still an
    # approximation across 15 and 9 years of infill, and is labelled as one.
    "1845": {"people": "baltimoredirecto1845balt_people.csv",
             "anchors": "street_anchors_1860.csv",
             "extents": "street_extents_1860.csv",
             "wards": "baltimore_wards_1841_1845.shp"},
    "1851": {"people": "matchettsbaltimo1851balt_people.csv",
             "anchors": "street_anchors_1860.csv",
             "extents": "street_extents_1860.csv",
             "wards": "baltimore_wards_1846_1860.shp"},
    "1868": {"people": "woodsbaltimoreci1868balt_people.csv",
             "anchors": "street_anchors_1868.csv",
             "extents": "street_extents_1868.csv",
             "wards": "baltimore_wards_1861_1882.shp"},
}


def main(year="1860"):
    global ALIASES
    ALIASES = load_aliases()
    cfg = YEARS[year]
    streets = load_streets(WARD_DIR / cfg["wards"])
    print(f"modern streets merged      : {len(streets)}")

    anchors_by_street = defaultdict(list)
    for r in csv.DictReader(open(WORK / cfg["anchors"])):
        r["seq"] = int(r["seq"])
        anchors_by_street[r["street"]].append(r)
    for v in anchors_by_street.values():
        v.sort(key=lambda r: r["seq"])

    # resolve each 1860 street to modern geometry + its number ladders
    resolved, unmatched_streets = {}, []
    for st, anchors in anchors_by_street.items():
        core_raw, dirn = norm_street(st)
        core = resolve_street(core_raw, streets, ALIASES)
        geom, _k = pick_geom(streets, core, dirn) if core else (None, None)
        if geom is None:
            unmatched_streets.append(st)
            continue
        placed = resolve_intersections(geom, anchors, streets)
        if not placed:
            continue
        # Key by direction as well as name. "CHARLES (N.)" and "CHARLES (S.)"
        # are two separate ladders running opposite ways from Baltimore street,
        # and both normalise to CHARLES. Keying by name alone let the second
        # silently overwrite the first, so half of every split street was placed
        # off the wrong ladder - which put people on the wrong side of the city.
        resolved[(core, dirn)] = {"geom": geom, "ladders": build_ladders(placed),
                                  "anchors": len(placed), "label": st}
    print(f"1860 streets with a ladder : {len(resolved)}")
    print(f"1860 streets unmatched     : {len(unmatched_streets)}")

    # Tier 2 support. Most streets in the book have no printed number table, but
    # HUE still has their geometry. Rather than drop those residents (which would
    # silently thin the alley neighbourhoods most of all), spread them along the
    # street in house-number order. The directory's extent note says which end
    # numbering starts from, so the run can be oriented rather than guessed.
    extents = {}
    for r in csv.DictReader(open(WORK / cfg["extents"])):
        core, _d = norm_street(r["street"])
        if core and core not in extents:
            extents[core] = r["extent"].lower()

    people = list(csv.DictReader(open(WORK / cfg["people"])))

    # observed house-number range per street, used to scale tier-2 placement
    span = defaultdict(list)
    for p in people:
        if p["addr_type"] == "numbered" and p["house_no"].isdigit():
            c2, d2 = norm_street(p["street"])
            if c2:
                span[(c2, d2)].append(int(p["house_no"]))

    def tier2(core, num, dirn=""):
        """Proportional placement along a street with no printed ladder."""
        geom = pick_geom(streets, core, dirn)[0]
        key = (core, dirn) if (core, dirn) in span else None
        if key is None:
            alt = [k for k in span if k[0] == core]
            key = alt[0] if len(alt) == 1 else None
        if geom is None or key is None:
            return None
        nums = span[key]
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
        core_raw, pdir = norm_street(p["street"])
        core = resolve_street(core_raw, streets, ALIASES) or core_raw
        num = int(p["house_no"])
        r = resolved.get((core, pdir))
        if r is None:
            # the entry gave no direction, or gave one the book does not use.
            # Choose among the candidate ladders by which one actually brackets
            # this house number, rather than by whichever was stored last.
            cands = [v for (c, _d), v in resolved.items() if c == core]
            if len(cands) == 1:
                r = cands[0]
            elif cands:
                def brackets(v):
                    best = 0
                    for side in ("left", "right"):
                        lad = v["ladders"][side]
                        if len(lad) >= 2 and lad[0][0] <= num <= lad[-1][0]:
                            best = max(best, len(lad))
                    return best
                scored = sorted(cands, key=brackets, reverse=True)
                r = scored[0] if brackets(scored[0]) else None
        if r is None:
            # no printed ladder: fall back to proportional placement if the
            # street's geometry is known at all
            pt = tier2(core, num, pdir)
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
    out = WORK / f"people_{year}_geocoded.geojson"
    gdf.to_file(out, driver="GeoJSON")

    print(f"\ngeocoded                   : {len(gdf)} of {len(people)} records")
    print(f"  skipped, no house number : {miss_num}")
    print(f"  skipped, street unmatched: {sum(miss_street.values())}")
    print("  confidence:", dict(gdf["confidence"].value_counts()))
    print("\ntop unmatched streets (these are the silent-loss risk):")
    for s, n in sorted(miss_street.items(), key=lambda t: -t[1])[:15]:
        print(f"    {n:5d}  {s}")
    pd.Series(miss_street).sort_values(ascending=False).to_csv(
        WORK / f"unmatched_streets_{year}.csv", header=["count"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "1860")
