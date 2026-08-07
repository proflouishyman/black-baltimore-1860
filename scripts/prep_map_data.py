#!/usr/bin/env python3
"""Flatten the geocoded 1860 data into a compact, SVG-ready JSON payload.

The exhibit preview is a self-contained page with no external tile server, so
the street network, ward outlines and resident points all have to travel inside
the document. This script projects everything to Maryland State Plane, clips to
the area residents actually occupy, simplifies the geometry hard, and emits
integer SVG coordinates so the payload stays small enough to inline.
"""

import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"
RAW = ROOT / "data" / "raw"
CRS_M = 6487
W, H = 1600, 1600          # SVG viewBox
PAD = 24
MARGIN = 260               # metres of context beyond the residents' extent
SIMPLIFY = 6               # metres; drops vertices we cannot see at this scale


def main():
    pts = gpd.read_file(WORK / "people_1860_geocoded.geojson").to_crs(epsg=CRS_M)
    minx, miny, maxx, maxy = pts.total_bounds
    clip = box(minx - MARGIN, miny - MARGIN, maxx + MARGIN, maxy + MARGIN)

    # square the extent so the map is not distorted by the viewBox aspect
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    half = max(maxx - minx, maxy - miny) / 2 + MARGIN
    x0, y0, x1, y1 = cx - half, cy - half, cx + half, cy + half
    scale = (W - 2 * PAD) / (x1 - x0)

    def sx(x):
        return round(PAD + (x - x0) * scale, 1)

    def sy(y):
        return round(H - PAD - (y - y0) * scale, 1)   # flip: SVG y grows down

    streets = gpd.read_file(
        RAW / "hue" / "HUE_Baltimore_Streets" / "CPE_Baltimore_Streets_HUE_v1.shp"
    ).to_crs(epsg=CRS_M)
    streets = streets[streets.intersects(clip)].copy()
    streets["geometry"] = streets.geometry.intersection(clip).simplify(SIMPLIFY)

    paths = []
    for geom in streets.geometry:
        if geom.is_empty:
            continue
        parts = [geom] if geom.geom_type == "LineString" else list(getattr(geom, "geoms", []))
        for p in parts:
            if p.geom_type != "LineString" or len(p.coords) < 2:
                continue
            flat = []
            for x, y in p.coords:
                flat.append(sx(x))
                flat.append(sy(y))
            paths.append(flat)

    wards = []
    wshp = RAW / "hue" / "HUE_Baltimore_Wards" / "baltimore_wards_1846_1860.shp"
    if wshp.exists():
        wg = gpd.read_file(wshp).to_crs(epsg=CRS_M)
        wg = wg[wg.intersects(clip)].copy()
        wg["geometry"] = wg.geometry.intersection(clip).simplify(SIMPLIFY)
        for geom in wg.geometry:
            if geom.is_empty:
                continue
            polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
            for poly in polys:
                flat = []
                for x, y in poly.exterior.coords:
                    flat.append(sx(x))
                    flat.append(sy(y))
                wards.append(flat)

    # residents: [x, y, tier, surname, given, occupation, street, house_no]
    tier_of = {"bracketed": 0, "single_anchor": 1, "extrapolated": 1,
               "street_proportional": 2}
    people = []
    for r, geom in zip(pts.to_dict("records"), pts.geometry):
        people.append([
            sx(geom.x), sy(geom.y), tier_of.get(r["confidence"], 2),
            r["surname"], r["given"], (r["occupation"] or "")[:40],
            r["street_raw"], r["house_no"],
        ])

    payload = {"w": W, "h": H, "streets": paths, "wards": wards, "people": people,
               "metres_per_unit": round(1 / scale, 3)}
    out = WORK / "map_payload.json"
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"streets paths : {len(paths)}")
    print(f"ward outlines : {len(wards)}")
    print(f"people        : {len(people)}")
    print(f"payload       : {out.stat().st_size/1_000_000:.2f} MB")


if __name__ == "__main__":
    main()
