#!/usr/bin/env python3
"""Build the shared payload for every page of the site.

All year maps share one projection and extent, so a dot in the same screen
position means the same ground position on every page and the years are
directly comparable.

Occupation counts are taken from *every parsed record*, not only the geocoded
ones, because occupation does not depend on our ability to place someone. The
demography is therefore broader than the maps.

Output: data/work/map_payload.json
"""

import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from classify_records import classify

import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"
RAW = ROOT / "data" / "raw"
CRS_M = 6487
W = H = 1600
PAD = 24
MARGIN = 200
SIMPLIFY = 6

YEARS = ["1819", "1822", "1842", "1845", "1851", "1860", "1868"]
PEOPLE_CSV = {
    "1819": "afrigeneas_1819_people.csv",
    "1822": "afrigeneas_1822_people.csv",
    "1842": "matchettsbaltimo1842balt_people.csv",
    "1845": "baltimoredirecto1845balt_people.csv",
    "1851": "matchettsbaltimo1851balt_people.csv",
    "1860": "woodsbaltimoreci1860balt_people.csv",
    "1868": "woodsbaltimoreci1868balt_people.csv",
}

# OCR mangles occupations badly and the books abbreviate inconsistently; fold
# the obvious variants together so the counts mean something.
OCC_FIX = [
    (r"^(labou?rer|iabou?rer|laborc?r|labr)\b.*", "laborer"),
    (r"^(washer(wo)?man|washer|wash'?r|laundress)\b.*", "laundress"),
    (r"^(drayman|dray)\b.*", "drayman"),
    (r"^(carter|cartman)\b.*", "carter"),
    (r"^(waiter|waitress)\b.*", "waiter"),
    (r"^(porter)\b.*", "porter"),
    (r"^(seaman|sailor|mariner)\b.*", "sailor"),
    (r"^(cook)\b.*", "cook"),
    (r"^(barber)\b.*", "barber"),
    (r"^(shoemaker|bootmaker|boot and shoemaker)\b.*", "shoemaker"),
    (r"^(caulker|calker)\b.*", "caulker"),
    (r"^(brickmaker|brick maker)\b.*", "brickmaker"),
    (r"^(whitewasher|white washer)\b.*", "whitewasher"),
    (r"^(hucks?ter)\b.*", "huckster"),
    (r"^(servant|domestic)\b.*", "servant"),
    (r"^(stevedore|stevadore)\b.*", "stevedore"),
    (r"^(hostler|ostler)\b.*", "hostler"),
    (r"^(blacksmith|smith)\b.*", "blacksmith"),
    (r"^(carpenter)\b.*", "carpenter"),
    (r"^(sawyer)\b.*", "sawyer"),
    (r"^(minister|preacher|clergyman)\b.*", "minister"),
    (r"^(teacher)\b.*", "teacher"),
    (r"^(nurse)\b.*", "nurse"),
    (r"^(seamstress|sempstress|dressmaker)\b.*", "seamstress"),
    (r"^(cooper)\b.*", "cooper"),
    (r"^(grocer)\b.*", "grocer"),
    (r"^(driver)\b.*", "driver"),
    (r"^(wagoner|waggoner)\b.*", "wagoner"),
    (r"^(bricklayer)\b.*", "bricklayer"),
    (r"^(painter)\b.*", "painter"),
    (r"^(oysterman|oyster)\b.*", "oysterman"),
    (r"^(coachman)\b.*", "coachman"),
    (r"^(chimney ?sweep)\b.*", "chimney sweep"),
    (r"^(fisherman)\b.*", "fisherman"),
]


def norm_occ(raw):
    s = (raw or "").lower().strip(" .,;:'\"")
    s = re.sub(r"[^a-z' ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s or len(s) < 3:
        return None
    for pat, rep in OCC_FIX:
        if re.match(pat, s):
            return rep
    if len(s.split()) > 3 or len(s) > 22:
        return None            # almost certainly an address that leaked in
    return s


def main():
    pts = {}
    for y in YEARS:
        f = WORK / f"people_{y}_geocoded.geojson"
        if f.exists():
            pts[y] = gpd.read_file(f).to_crs(epsg=CRS_M)

    ward_dir = RAW / "hue" / "HUE_Baltimore_Wards"
    wards60 = gpd.read_file(ward_dir / "baltimore_wards_1846_1860.shp").to_crs(epsg=CRS_M)
    wards68 = gpd.read_file(ward_dir / "baltimore_wards_1861_1882.shp").to_crs(epsg=CRS_M)
    # 1820 used twelve wards on an entirely different boundary set, so it needs
    # its own polygons rather than new attributes on the 1846-1860 ones
    wards20 = gpd.read_file(ward_dir / "baltimore_wards_1818_1831.shp").to_crs(epsg=CRS_M)

    allg = [g for gdf in pts.values() for g in gdf.geometry] + \
           list(wards60.geometry) + list(wards68.geometry)
    minx, miny, maxx, maxy = gpd.GeoSeries(allg, crs=f"EPSG:{CRS_M}").total_bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    half = max(maxx - minx, maxy - miny) / 2 + MARGIN
    x0, y0 = cx - half, cy - half
    scale = (W - 2 * PAD) / (2 * half)
    clip = box(x0, y0, cx + half, cy + half)

    def sx(x):
        return round(PAD + (x - x0) * scale, 1)

    def sy(y):
        return round(H - PAD - (y - y0) * scale, 1)

    city = unary_union(list(wards60.geometry) + list(wards68.geometry)).buffer(0)
    streets = gpd.read_file(
        RAW / "hue" / "HUE_Baltimore_Streets" / "CPE_Baltimore_Streets_HUE_v1.shp"
    ).to_crs(epsg=CRS_M)
    streets = streets[streets.intersects(city)].copy()
    streets["geometry"] = streets.geometry.intersection(city).simplify(SIMPLIFY)
    paths = []
    for g in streets.geometry:
        if g.is_empty:
            continue
        parts = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
        for p in parts:
            if p.geom_type == "LineString" and len(p.coords) >= 2:
                f = []
                for x, y in p.coords:
                    f += [sx(x), sy(y)]
                paths.append(f)

    # Modern centrelines, purely for orientation. Simplified harder than the
    # period network because it is never measured against, only glanced at.
    modern = []
    labels = []
    mpath = RAW / "balt_streets.geojson"
    if mpath.exists():
        mg = gpd.read_file(mpath).to_crs(epsg=CRS_M)
        mg = mg[mg.intersects(city)].copy()
        mg["geometry"] = mg.geometry.intersection(city).simplify(SIMPLIFY * 3)

        # Group clipped geometry by street name so we can pick the major
        # arteries for labelling (total length) and know where their longest
        # unbroken run sits (label placement), while still emitting every
        # segment into `modern` for drawing.
        by_name = defaultdict(list)
        for name, g in zip(mg["ROAD_NAME"], mg.geometry):
            if g.is_empty or not name:
                continue
            parts = [g] if g.geom_type == "LineString" else list(getattr(g, "geoms", []))
            for pp in parts:
                if pp.geom_type == "LineString" and len(pp.coords) >= 2:
                    by_name[name].append(pp)
                    f = []
                    for x, y in pp.coords:
                        f += [sx(x), sy(y)]
                    modern.append(f)

        EXCLUDE_NAMES = {"NO NAME", "UNNAMED", "UNKNOWN", ""}
        MIN_TOTAL_LEN = 800  # metres; drops alleys/service roads from the ranking
        NUM_LABELS = 35

        totals = {
            n: sum(p.length for p in parts) for n, parts in by_name.items()
            if n.strip().upper() not in EXCLUDE_NAMES and not n.strip().isdigit()
        }
        chosen = sorted(
            ((n, t) for n, t in totals.items() if t >= MIN_TOTAL_LEN),
            key=lambda kv: -kv[1],
        )[:NUM_LABELS]

        def cap_word(w):
            # Baltimore is thick with "Mc" surnames-as-streets; plain
            # str.capitalize() would flatten "MCHENRY" to "Mchenry".
            lw = w.lower()
            if lw.startswith("mc") and len(lw) > 2:
                return "Mc" + lw[2].upper() + lw[3:]
            return w.capitalize()

        DIRS = {"N", "S", "E", "W", "NE", "NW", "SE", "SW"}
        SUFFIXES = {
            "ST": "St", "AVE": "Ave", "AV": "Ave", "RD": "Rd", "BLVD": "Blvd",
            "DR": "Dr", "LN": "Ln", "CT": "Ct", "PL": "Pl", "PKWY": "Pkwy",
            "HWY": "Hwy", "TER": "Ter", "CIR": "Cir", "WAY": "Way",
            "EXPWY": "Expwy",
        }

        def norm_name(raw):
            out = []
            for w in raw.split():
                if w in DIRS:
                    out.append(w)
                elif w in SUFFIXES:
                    out.append(SUFFIXES[w])
                else:
                    out.append(cap_word(w))
            return " ".join(out)

        print(f"labels: {len(chosen)} major streets chosen")
        for n, t in chosen:
            print(f"  {t:7.0f}m  {norm_name(n)}")

        for name, total in chosen:
            longest = max(by_name[name], key=lambda p: p.length)
            if longest.length < 30:
                continue
            mid = longest.length / 2
            eps = min(20.0, longest.length / 4)
            mx, my = longest.interpolate(mid).coords[0]
            p0 = longest.interpolate(max(mid - eps, 0.0))
            p1 = longest.interpolate(min(mid + eps, longest.length))
            x0s, y0s = sx(p0.x), sy(p0.y)
            x1s, y1s = sx(p1.x), sy(p1.y)
            if x0s == x1s and y0s == y1s:
                continue
            a = math.atan2(y1s - y0s, x1s - x0s)
            if a > math.pi / 2 or a < -math.pi / 2:
                a += math.pi
            labels.append({
                "t": norm_name(name), "x": sx(mx), "y": sy(my), "a": round(a, 4),
            })

    cen = {int(r["ward"]): r for r in csv.DictReader(open(WORK / "ward_census_1860.csv"))}
    cen50 = {int(r["ward"]): r for r in csv.DictReader(open(WORK / "ward_census_1850.csv"))}
    ward_feats = []
    for num, geom in zip(wards60["Ward_Num"], wards60.geometry):
        geom = geom.intersection(clip).simplify(SIMPLIFY)
        if geom.is_empty:
            continue
        polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        rings = []
        for poly in polys:
            f = []
            for x, y in poly.exterior.coords:
                f += [sx(x), sy(y)]
            rings.append(f)
        c = cen.get(int(num))
        c50 = cen50.get(int(num))
        if not c:
            continue
        feat = {
            "ward": int(num), "rings": rings,
            # 1850 and 1860 share this boundary set, so one polygon carries both
            "y1860": {"black_pct": float(c["black_pct"]), "black": int(c["black_total"]),
                      "white": int(c["white"]), "slave": int(c["slave"]),
                      "free_colored": int(c["free_colored"]),
                      "aggregate": int(c["aggregate"])},
        }
        if c50:
            feat["y1850"] = {"black_pct": float(c50["black_pct"]),
                             "black": int(c50["black_total"]), "white": int(c50["white"]),
                             "slave": int(c50["slave"]),
                             "free_colored": int(c50["free_colored"]),
                             "aggregate": int(c50["aggregate"])}
        # centroid in SVG space, for drawing the ward number on the map
        cxs = [r[0::2] for r in rings]; cys = [r[1::2] for r in rings]
        allx = [v for r in cxs for v in r]; ally = [v for r in cys for v in r]
        feat["cx"] = round(sum(allx) / len(allx), 1)
        feat["cy"] = round(sum(ally) / len(ally), 1)
        ward_feats.append(feat)

    # 1820 ward polygons carrying the Fourth Census counts
    cen20 = {int(r["ward"]): r for r in csv.DictReader(open(WORK / "ward_census_1820.csv"))}
    ward20_feats = []
    for num, geom in zip(wards20["Ward_Num"], wards20.geometry):
        geom = geom.intersection(clip).simplify(SIMPLIFY)
        if geom.is_empty:
            continue
        polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        rings = []
        for poly in polys:
            f = []
            for x, y in poly.exterior.coords:
                f += [sx(x), sy(y)]
            rings.append(f)
        c = cen20.get(int(num))
        if not c:
            continue
        cxs = [r[0::2] for r in rings]; cys = [r[1::2] for r in rings]
        allx = [v for r in cxs for v in r]; ally = [v for r in cys for v in r]
        ward20_feats.append({
            "cx": round(sum(allx) / len(allx), 1), "cy": round(sum(ally) / len(ally), 1),
            "ward": int(num), "rings": rings,
            "y1820": {"black_pct": float(c["black_pct"]), "black": int(c["black_total"]),
                      "white": int(c["white"]), "slave": int(c["slave"]),
                      "free_colored": int(c["free_colored"]),
                      "aggregate": int(c["aggregate"])},
        })

    # 1869 new construction, on the 1861-1882 wards it was reported under.
    # These are NOT the 1846-1860 wards of the census choropleth.
    val = {int(r["ward"]): r for r in csv.DictReader(open(WORK / "ward_valuation_1869.csv"))}
    ward69_feats = []
    for num, geom in zip(wards68["Ward_Num"], wards68.geometry):
        geom = geom.intersection(clip).simplify(SIMPLIFY)
        if geom.is_empty:
            continue
        polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        rings = []
        for poly in polys:
            f = []
            for x, y in poly.exterior.coords:
                f += [sx(x), sy(y)]
            rings.append(f)
        c = val.get(int(num))
        if not c:
            continue
        allx = [v for r in rings for v in r[0::2]]; ally = [v for r in rings for v in r[1::2]]
        ward69_feats.append({
            "ward": int(num), "rings": rings,
            "cx": round(sum(allx)/len(allx), 1), "cy": round(sum(ally)/len(ally), 1),
            "y1869": {"value": int(c["value"]), "dwellings": int(c["dwellings"]),
                      "improvements": int(c["improvements"]),
                      "per_dwelling": int(c["value_per_dwelling"])},
        })

    # residents we have checked against the 1860 census carry extra detail
    links = {}
    lp = WORK / "census_links.json"
    if lp.exists():
        links = json.loads(lp.read_text(encoding="utf8"))

    tier = {"bracketed": 0, "single_anchor": 1, "extrapolated": 1,
            "street_proportional": 2, "block_face": 0, "corner": 0}
    people = {}
    for y, gdf in pts.items():
        rows = []
        for r, g in zip(gdf.to_dict("records"), gdf.geometry):
            where = r.get("street_raw") or ""
            if r.get("cross_street"):
                where = f"{where} {r.get('bearing','')} of {r['cross_street']}".strip()
            cat, sub = classify(r.get("surname", ""), r.get("given", ""),
                                r.get("occupation", ""))
            # 0 resident, 1 business, 2 institution - kept numeric to stay small
            code = {"resident": 0, "business": 1, "institution": 2}[cat]
            gv = (r.get("given") or "").strip().split()
            lk = links.get(f"{y}|{(r.get('surname') or '').strip().lower()}|"
                           f"{gv[0].lower() if gv else ''}")
            rows.append([sx(g.x), sy(g.y), tier.get(r["confidence"], 2),
                         r["surname"], r["given"], (r["occupation"] or "")[:40],
                         where, r.get("house_no", ""), code, sub, lk])
        people[y] = rows

    # occupations from every parsed record, geocoded or not
    occ = {}
    parsed_counts = {}
    for y, fname in PEOPLE_CSV.items():
        f = WORK / fname
        if not f.exists():
            continue
        recs = list(csv.DictReader(open(f)))
        parsed_counts[y] = len(recs)
        c = Counter()
        for r in recs:
            o = norm_occ(r.get("occupation"))
            if o:
                c[o] += 1
        occ[y] = c.most_common(40)

    payload = {"w": W, "h": H, "streets": paths, "modern": modern, "labels": labels,
               "wards": ward_feats, "wards1820": ward20_feats, "wards1869": ward69_feats,
               "people": people, "occupations": occ, "parsed": parsed_counts,
               "metres_per_unit": round(1 / scale, 3)}
    out = WORK / "map_payload.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print("streets", len(paths), "modern", len(modern), "labels", len(labels),
          "wards", len(ward_feats))
    for y in YEARS:
        print(f"  {y}: {len(people.get(y, [])):5d} placed, "
              f"{parsed_counts.get(y,0):5d} parsed, "
              f"{len(occ.get(y,[])):3d} occupations")
    print(f"payload {out.stat().st_size/1_000_000:.2f} MB")


if __name__ == "__main__":
    main()
