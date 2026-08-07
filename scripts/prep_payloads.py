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
import re
from collections import Counter
from pathlib import Path

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

YEARS = ["1842", "1845", "1851", "1860", "1868"]
PEOPLE_CSV = {
    "1822": "baltimoredirecto1822keen_people.csv",
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

    cen = {int(r["ward"]): r for r in csv.DictReader(open(WORK / "ward_census_1860.csv"))}
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
        if not c:
            continue
        ward_feats.append({
            "ward": int(num), "rings": rings, "black_pct": float(c["black_pct"]),
            "black": int(c["black_total"]), "white": int(c["white"]),
            "slave": int(c["slave"]), "free_colored": int(c["free_colored"]),
            "aggregate": int(c["aggregate"]),
        })

    tier = {"bracketed": 0, "single_anchor": 1, "extrapolated": 1,
            "street_proportional": 2, "block_face": 0, "corner": 0}
    people = {}
    for y, gdf in pts.items():
        rows = []
        for r, g in zip(gdf.to_dict("records"), gdf.geometry):
            where = r.get("street_raw") or ""
            if r.get("cross_street"):
                where = f"{where} {r.get('bearing','')} of {r['cross_street']}".strip()
            rows.append([sx(g.x), sy(g.y), tier.get(r["confidence"], 2),
                         r["surname"], r["given"], (r["occupation"] or "")[:40],
                         where, r.get("house_no", "")])
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

    payload = {"w": W, "h": H, "streets": paths, "wards": ward_feats,
               "people": people, "occupations": occ, "parsed": parsed_counts,
               "metres_per_unit": round(1 / scale, 3)}
    out = WORK / "map_payload.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print("streets", len(paths), "wards", len(ward_feats))
    for y in YEARS:
        print(f"  {y}: {len(people.get(y, [])):5d} placed, "
              f"{parsed_counts.get(y,0):5d} parsed, "
              f"{len(occ.get(y,[])):3d} occupations")
    print(f"payload {out.stat().st_size/1_000_000:.2f} MB")


if __name__ == "__main__":
    main()
