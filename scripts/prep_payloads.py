#!/usr/bin/env python3
"""Build one shared SVG-ready payload carrying every layer the site draws.

All three pages (1860 dots, 1842 block faces, ward density) share a single
projection and extent so the maps are directly comparable page to page: a dot
in the same screen position means the same ground position on every page.

Output: data/work/map_payload.json
"""

import json
from pathlib import Path

import csv
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


def main():
    p60 = gpd.read_file(WORK / "people_1860_geocoded.geojson").to_crs(epsg=CRS_M)
    p42 = gpd.read_file(WORK / "people_1842_geocoded.geojson").to_crs(epsg=CRS_M)
    wards = gpd.read_file(
        RAW / "hue" / "HUE_Baltimore_Wards" / "baltimore_wards_1846_1860.shp"
    ).to_crs(epsg=CRS_M)

    # shared square extent, driven by the wards (the city) plus both cohorts
    allg = list(p60.geometry) + list(p42.geometry) + list(wards.geometry)
    minx, miny, maxx, maxy = gpd.GeoSeries(allg, crs=f"EPSG:{CRS_M}").total_bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    half = max(maxx - minx, maxy - miny) / 2 + MARGIN
    x0, y0, x1, y1 = cx - half, cy - half, cx + half, cy + half
    scale = (W - 2 * PAD) / (x1 - x0)
    clip = box(x0, y0, x1, y1)

    def sx(x):
        return round(PAD + (x - x0) * scale, 1)

    def sy(y):
        return round(H - PAD - (y - y0) * scale, 1)

    def flat_line(geom):
        out = []
        parts = [geom] if geom.geom_type == "LineString" else list(getattr(geom, "geoms", []))
        for p in parts:
            if p.geom_type == "LineString" and len(p.coords) >= 2:
                f = []
                for x, y in p.coords:
                    f += [sx(x), sy(y)]
                out.append(f)
        return out

    streets = gpd.read_file(
        RAW / "hue" / "HUE_Baltimore_Streets" / "CPE_Baltimore_Streets_HUE_v1.shp"
    ).to_crs(epsg=CRS_M)
    city = unary_union(wards.geometry.values).buffer(0)
    streets = streets[streets.intersects(city)].copy()
    streets["geometry"] = streets.geometry.intersection(city).simplify(SIMPLIFY)
    paths = []
    for g in streets.geometry:
        if not g.is_empty:
            paths += flat_line(g)

    # ward polygons carrying the census attributes, for the choropleth
    cen = {int(r["ward"]): r for r in csv.DictReader(open(WORK / "ward_census_1860.csv"))}
    ward_feats = []
    for num, geom in zip(wards["Ward_Num"], wards.geometry):
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
            "ward": int(num), "rings": rings,
            "black_pct": float(c["black_pct"]),
            "black": int(c["black_total"]), "white": int(c["white"]),
            "slave": int(c["slave"]), "free_colored": int(c["free_colored"]),
            "aggregate": int(c["aggregate"]),
        })

    tier60 = {"bracketed": 0, "single_anchor": 1, "extrapolated": 1,
              "street_proportional": 2}
    people60 = []
    for r, g in zip(p60.to_dict("records"), p60.geometry):
        people60.append([sx(g.x), sy(g.y), tier60.get(r["confidence"], 2),
                         r["surname"], r["given"], (r["occupation"] or "")[:40],
                         r["street_raw"], r["house_no"]])

    people42 = []
    for r, g in zip(p42.to_dict("records"), p42.geometry):
        where = f"{r['street_raw']} {r['bearing']} of {r['cross_street']}".strip()
        people42.append([sx(g.x), sy(g.y), 0,
                         r["surname"], r["given"], (r["occupation"] or "")[:40],
                         where, ""])

    payload = {"w": W, "h": H, "streets": paths, "wards": ward_feats,
               "people1860": people60, "people1842": people42,
               "metres_per_unit": round(1 / scale, 3)}
    out = WORK / "map_payload.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"streets {len(paths)}  wards {len(ward_feats)}  "
          f"1860 {len(people60)}  1842 {len(people42)}")
    print(f"payload {out.stat().st_size/1_000_000:.2f} MB")


if __name__ == "__main__":
    main()
