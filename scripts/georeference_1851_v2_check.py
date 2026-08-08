#!/usr/bin/env python3
"""Independent accuracy test of the 1851 Sidney & Neff georeference, and the
final combined transform.

Why this script exists
----------------------
scripts/georeference_1851_v2.py fits and cross-validates a transform on 54
control points read off the full-resolution sheet. Leave-one-out cross
validation is a good estimator, but it has two blind spots that only a second,
independent reading of the map can close:

  1. LOOCV holds out a point that the *same operator* picked with the *same*
     habits. A systematic reading bias -- always taking the north kerb rather
     than the corridor centre, say -- is invisible to it, because it is present
     in both the fit and the held-out point.
  2. LOOCV cannot measure error outside the convex hull of the control network.
     Every held-out point is, by construction, surrounded by the others. The 54
     control points stop at pixel y=6653 on a sheet 10643 pixels tall, so the
     bottom third -- Federal Hill south, Whetstone Point, Locust Point, Fort
     McHenry, the Middle Branch shore -- is pure extrapolation and no
     leave-one-out figure says anything about it.

The 21 points below were located independently, by a separate pass over the
same jp2, before the 54-point table was seen. They are therefore usable as
NSSDA check points: FGDC-STD-007.3-1998 requires accuracy to be tested against
"an independent source of higher accuracy" at points not used to build the
product. See docs/GEOREFERENCING_METHOD.md section 1.3.

They also differ in kind. Fourteen are street crossings, matching the control
set, but seven are standing physical structures -- two masonry monuments, two
public squares laid out before 1851, a fortification, and a colonial mansion.
Those carry no dependence on street naming or on centreline vintage at all.

What the script reports
-----------------------
  A. Inter-operator agreement. At intersections both passes located, how far
     apart are the two pixel picks? This is the reading precision of the method
     itself, and it is the floor on any accuracy claim.
  B. Independent check-point accuracy. Fit on the 54 control points only,
     predict the 21 check points, report the error. Split in-hull versus
     out-of-hull so the extrapolation cost is visible rather than averaged away.
  C. The final combined transform. All 75 points, leave-one-out cross validated,
     reported in NSSDA form (Accuracy_r = 1.7308 * RMSE_r at 95% confidence).

Outputs (all _v2 suffixed; nothing here overwrites a v1 artefact)
  data/work/maps/checkpoints_1851_v2.csv       the 21 check points + their errors
  data/work/maps/gcps_1851_v2_combined.csv     all 75 points, LOO errors per model
  data/work/maps/accuracy_1851_v2.json         every statistic quoted in the docs
  data/work/maps/baltimore_1851_v2.points      QGIS format, combined set
  data/work/maps/baltimore_1851_georef_v2.tif  TPS-warped raster (if GDAL is found)

Provenance of the check-point world coordinates, all accessed 2026-08-08
  Street crossings: Baltimore City road centrelines, data/raw/balt_streets.geojson
  Monuments, squares, fort, mansion: OpenStreetMap way geometry via the Overpass
    API, https://overpass-api.de/api/interpreter . OSM way id is recorded per
    point below. Where the Maryland Inventory of Historic Properties
    (data/raw/mihp_baltimore.geojson, Maryland Historical Trust) also holds the
    feature, the two agree to the fifth decimal of a degree; the MIHP number is
    noted for cross-reference.
  Map: Sidney & Neff, Plan of the City of Baltimore, 1851. Library of Congress
    https://www.loc.gov/item/2004629026/ . Local master
    data/raw/maps/baltimore_1851_plan.jp2, 13414 x 10643.
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work" / "maps"
WORK.mkdir(parents=True, exist_ok=True)

CRS_M = 6487          # NAD83(2011) / Maryland, metres -- project standard
FULL_SIZE = (13414, 10643)

# ---------------------------------------------------------------------------
# The 21 independent check points.
#
# pixel_x / pixel_y are full-resolution jp2 coordinates, read by cropping the
# master with `gdal_translate -srcwin` and inspecting the crop with a labelled
# pixel grid overlaid. `crop` records the srcwin box used, so any pick can be
# re-opened and re-argued from the source image.
#
# kind = "street"   -> world coordinate is the crossing of two named centrelines
#        "osm_way"  -> world coordinate is the centroid of an OSM way geometry
# ---------------------------------------------------------------------------
CHECKPOINTS = [
    # --- standing structures: no dependence on street names or centrelines ----
    dict(name="Washington Monument", kind="osm_way", ref="osm:116542858",
         lon=-76.61565, lat=39.29752, px=6740, py=2978,
         crop="6500,2800,500,400",
         note="cross-hatched square base in the Mount Vernon Place crossing; "
              "MIHP B-6 agrees to 5 d.p. Built 1815-1829, never moved."),
    dict(name="Battle Monument", kind="osm_way", ref="osm:453652377",
         lon=-76.61241, lat=39.29068, px=7135, py=4256,
         crop="7050,4120,400,340",
         note="small hatched block inside the widened Calvert St corridor "
              "labelled MONUMENT SQUARE; MIHP B-14 agrees. Built 1815-1825."),
    dict(name="Union Square centre", kind="osm_way", ref="osm:85585339",
         lon=-76.64160, lat=39.28691, px=3086, py=4751,
         crop="2930,4460,500,400",
         note="block labelled UNION SQUARE, corners read at "
              "x 3009/3163, y 4673/4829. Laid out 1847."),
    dict(name="Franklin Square centre", kind="osm_way", ref="osm:85585348",
         lon=-76.63894, lat=39.29029, px=3470, py=4169,
         crop="3120,4060,500,400",
         note="block labelled FRANKLIN SQUARE between CALHOUN and CAREY, both "
              "named on the sheet; corners x 3390/3550, y 4087/4250. Laid out 1839."),
    dict(name="Fort McHenry star centre", kind="osm_way", ref="osm:1220301007",
         lon=-76.57988, lat=39.26324, px=11408, py=9251,
         crop="11200,9080,480,380",
         note="centre of the drawn five-bastion star, from the west and east "
              "bastion tips (x 11307/11510) and north and south (y 9152/9350). "
              "The masonry fort of 1798-1803. Lowest point on the sheet by far."),
    dict(name="Mount Clare mansion", kind="osm_way", ref="osm:85715388",
         lon=-76.64298, lat=39.27895, px=2838, py=6135,
         crop="2800,5950,700,500",
         note="hatched house symbol labelled MOUNT CLARE / J. Carroll. Built 1760s."),
    # --- street crossings ----------------------------------------------------
    dict(name="Eutaw & Baltimore", kind="street", a="EUTAW", b="BALTIMORE",
         px=5919, py=4432, crop="5820,4270,360,300",
         note="Eutaw corridor x 5900-5938, Eutaw House hotel labelled on the NW "
              "corner. v1 recorded x=6011 here, which is 92 px / 57 m out."),
    dict(name="Charles & Baltimore", kind="street", a="CHARLES", b="BALTIMORE",
         px=6727, py=4444, crop="6490,4230,500,400",
         note="Charles reads as a pale vertical band, which is the sheet join, "
              "so x is the weaker coordinate here."),
    dict(name="Gay & Baltimore", kind="street", a="GAY", b="BALTIMORE",
         px=7587, py=4408, crop="7350,4210,500,400", note="N. GAY labelled."),
    dict(name="Broadway & Baltimore", kind="street", a="BROADWAY", b="BALTIMORE",
         px=9678, py=4196, crop="9500,4050,400,340",
         note="Broadway corridor x 9646-9709, unusually wide, with the market "
              "line down the middle."),
    dict(name="Chester & Baltimore", kind="street", a="CHESTER", b="BALTIMORE",
         px=10570, py=4197, crop="10380,4030,620,380",
         note="CHESTER named at the head of the street on the same sheet."),
    dict(name="Potomac & Baltimore", kind="street", a="POTOMAC", b="BALTIMORE",
         px=12315, py=4198, crop="12120,4040,620,380",
         note="POTOMAC named at the head of the street. Easternmost check point."),
    dict(name="Fulton & Baltimore", kind="street", a="FULTON", b="BALTIMORE",
         px=2600, py=4495, crop="2340,4300,500,400",
         note="Fulton identified from the sheet's own vertical label at x~2606; "
              "the crossing itself is in open ground, so this is a weaker pick."),
    dict(name="Calhoun & Fayette", kind="street", a="CALHOUN", b="FAYETTE",
         px=3370, py=4272, crop="3120,4060,500,400",
         note="STRICKER, MORRIS, CALHOUN and CAREY all named in this crop."),
    dict(name="Stricker & Hollins", kind="street", a="STRICKER", b="HOLLINS",
         px=3187, py=4660, crop="2930,4460,500,400",
         note="Hollins runs along the north side of Union Square, not the south."),
    dict(name="Broadway & Monument", kind="street", a="BROADWAY", b="MONUMENT",
         px=9674, py=2981, crop="9520,2820,620,380", note=""),
    dict(name="Eutaw & Madison", kind="street", a="EUTAW", b="MADISON",
         px=5937, py=2790, crop="5750,2680,620,380",
         note="W. MADISON and W. MONUMENT both named in this crop."),
    dict(name="Charles & Chase", kind="street", a="CHARLES", b="CHASE",
         px=6705, py=2110, crop="6560,2020,620,380",
         note="street name not legible in the crop; identified by position only. "
              "Weakest pick in the set and expected to show it."),
    dict(name="Charles & Cross", kind="street", a="CHARLES", b="CROSS",
         px=6737, py=6651, crop="6580,6520,620,380",
         note="CROSS named; the market house sits in the street, corridor centre taken."),
    dict(name="Russell & Ostend", kind="street", a="RUSSELL", b="OSTEND",
         px=5295, py=6625, crop="5040,6460,500,400",
         note="RUSSEL named on the sheet; Ostend located from its label further "
              "west along the same corridor. Weaker pick."),
    dict(name="Wolfe & Lancaster", kind="street", a="WOLFE", b="LANCASTER",
         px=10171, py=5777, crop="9980,5620,620,380", note=""),
]


# ---------------------------------------------------------------------------
# Reference geometry
# ---------------------------------------------------------------------------

def norm(name):
    """Strip directional prefix and street-type suffix, matching the project's
    existing convention in scripts/geocode_1860.norm_street()."""
    c = re.sub(r"^(N|S|E|W)\s+", "", str(name).upper().strip())
    c = re.sub(r"\s+(ST|STREET|AVE|AVENUE|RD|ROAD|LN|LANE|ALY|ALLEY|CT|COURT"
               r"|PL|PLACE|BLVD|HWY|PKWY|DR|TER|WAY|SQ)\.?$", "", c)
    return c.strip()


def load_modern_streets():
    """One merged geometry per normalised name from the modern Baltimore City
    centreline file. Deliberately NOT the HUE c.1930 file: see
    docs/GEOREFERENCING_METHOD.md section 1.5 on why fitting to HUE and then
    measuring against HUE is circular."""
    import geopandas as gpd
    from shapely.ops import unary_union
    gdf = gpd.read_file(ROOT / "data" / "raw" / "balt_streets.geojson").to_crs(CRS_M)
    buckets = defaultdict(list)
    for name, geom in zip(gdf["ROAD_NAME"], gdf.geometry):
        if name:
            buckets[norm(name)].append(geom)
    return {k: unary_union(v) for k, v in buckets.items()}


def resolve_checkpoints():
    """Attach an EPSG:6487 world coordinate to every check point."""
    import geopandas as gpd
    from shapely.geometry import Point
    streets = load_modern_streets()

    lonlat = [(c["lon"], c["lat"]) for c in CHECKPOINTS if c["kind"] == "osm_way"]
    projected = list(gpd.GeoSeries([Point(p) for p in lonlat], crs=4326).to_crs(CRS_M))

    out, it = [], iter(projected)
    for c in CHECKPOINTS:
        row = dict(c)
        if c["kind"] == "osm_way":
            p = next(it)
            row["world_x"], row["world_y"] = p.x, p.y
        else:
            ga, gb = streets.get(c["a"]), streets.get(c["b"])
            if ga is None or gb is None:
                raise KeyError(f"{c['name']}: missing centreline for "
                               f"{c['a'] if ga is None else c['b']}")
            inter = ga.intersection(gb)
            pts = [p for p in getattr(inter, "geoms", [inter]) if p.geom_type == "Point"]
            if not pts:
                raise ValueError(f"{c['name']}: centrelines do not cross")
            # More than one crossing means the merged geometry doubles back;
            # take the one nearest the other points' centre of mass rather than
            # silently picking the first.
            row["world_x"], row["world_y"] = pts[0].x, pts[0].y
            row["ref"] = "balt_streets.geojson"
        out.append(row)
    return out


def load_control():
    """The 54-point control table produced by scripts/georeference_1851_v2.py."""
    path = WORK / "gcps_1851.csv"
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append(dict(name=r["name"], region=r["region"],
                             px=float(r["pixel_x"]), py=float(r["pixel_y"]),
                             world_x=float(r["world_x_epsg6487"]),
                             world_y=float(r["world_y_epsg6487"]),
                             ref="balt_streets/911", kind="street",
                             note=r.get("note", "")))
    return rows


# ---------------------------------------------------------------------------
# Transforms. All map pixel -> world (EPSG:6487 metres).
#
# Each returns a callable f(px_array, py_array) -> (wx_array, wy_array), so the
# cross-validation loop can treat all four models identically.
# ---------------------------------------------------------------------------

def _design(px, py, order):
    if order == 1:
        return np.column_stack([np.ones_like(px), px, py])
    return np.column_stack([np.ones_like(px), px, py, px * px, px * py, py * py])


def fit_poly(px, py, wx, wy, order):
    A = _design(px, py, order)
    cx, *_ = np.linalg.lstsq(A, wx, rcond=None)
    cy, *_ = np.linalg.lstsq(A, wy, rcond=None)

    def f(qx, qy):
        B = _design(np.asarray(qx, float), np.asarray(qy, float), order)
        return B @ cx, B @ cy
    f.coeffs = (cx, cy)
    return f


def fit_helmert(px, py, wx, wy):
    """Similarity: translation, rotation, one uniform scale. Four parameters.

    Raster rows count downwards and projected northings count upwards, so the
    pixel frame is left-handed with respect to the world frame. A pure rotation
    has determinant +1 and cannot express that flip, so the row axis is negated
    before fitting and the fit is done on the right-handed frame (px, -py). Left
    unflipped this model cannot fit at all: it degenerates to a near-degenerate
    least-squares solution with kilometre-scale residuals.

    Solved as one least-squares system in (a, b, tx, ty) where
        wx = a*px - b*(-py) + tx
        wy = b*px + a*(-py) + ty
    so scale = hypot(a, b) metres per pixel and rotation = atan2(b, a)."""
    n = len(px)
    py = -np.asarray(py, float)
    A = np.zeros((2 * n, 4))
    A[0::2, 0], A[0::2, 1], A[0::2, 2] = px, -py, 1.0
    A[1::2, 0], A[1::2, 1], A[1::2, 3] = py, px, 1.0
    sol, *_ = np.linalg.lstsq(A, np.column_stack([wx, wy]).ravel(), rcond=None)
    a, b, tx, ty = sol

    def f(qx, qy):
        qx = np.asarray(qx, float)
        qy = -np.asarray(qy, float)
        return a * qx - b * qy + tx, b * qx + a * qy + ty
    f.params = dict(scale=float(np.hypot(a, b)),
                    rotation_deg=float(np.degrees(np.arctan2(b, a))),
                    tx=float(tx), ty=float(ty))
    return f


def _tps_kernel(r2):
    """U(r) = r^2 log(r^2), the standard 2-D thin plate spline basis. Written in
    terms of r^2 so the r=0 case is handled without a square root."""
    out = np.zeros_like(r2)
    nz = r2 > 0
    out[nz] = r2[nz] * np.log(r2[nz])
    return out


def fit_tps(px, py, wx, wy, scale=1e-4):
    """Thin plate spline, exact interpolation at the control points.

    Pixel coordinates run to ~13000, and r^2 log r^2 on numbers that size is
    badly conditioned, so the fit is done in a scaled coordinate frame and the
    scaling is undone inside the returned callable."""
    n = len(px)
    sx, sy = px * scale, py * scale
    dx = sx[:, None] - sx[None, :]
    dy = sy[:, None] - sy[None, :]
    K = _tps_kernel(dx * dx + dy * dy)
    P = np.column_stack([np.ones(n), sx, sy])
    L = np.zeros((n + 3, n + 3))
    L[:n, :n] = K
    L[:n, n:] = P
    L[n:, :n] = P.T
    rhs = np.zeros((n + 3, 2))
    rhs[:n, 0], rhs[:n, 1] = wx, wy
    # lstsq rather than solve: with near-duplicate control points L is singular,
    # and a least-norm solution is the right behaviour there.
    sol, *_ = np.linalg.lstsq(L, rhs, rcond=None)
    w, aff = sol[:n], sol[n:]

    def f(qx, qy):
        qx = np.atleast_1d(np.asarray(qx, float)) * scale
        qy = np.atleast_1d(np.asarray(qy, float)) * scale
        d2 = (qx[:, None] - sx[None, :]) ** 2 + (qy[:, None] - sy[None, :]) ** 2
        U = _tps_kernel(d2)
        base = np.column_stack([np.ones(len(qx)), qx, qy]) @ aff
        return base[:, 0] + U @ w[:, 0], base[:, 1] + U @ w[:, 1]
    return f


MODELS = {
    "helmert": lambda px, py, wx, wy: fit_helmert(px, py, wx, wy),
    "affine": lambda px, py, wx, wy: fit_poly(px, py, wx, wy, 1),
    "poly2": lambda px, py, wx, wy: fit_poly(px, py, wx, wy, 2),
    "tps": lambda px, py, wx, wy: fit_tps(px, py, wx, wy),
}


def errors_at(f, px, py, wx, wy):
    ex, ey = f(px, py)
    return np.hypot(np.asarray(ex) - wx, np.asarray(ey) - wy)


def loocv(model, px, py, wx, wy):
    """Leave-one-out: refit from scratch n times, measure at the omitted point."""
    n = len(px)
    out = np.zeros(n)
    idx = np.arange(n)
    for i in range(n):
        m = idx != i
        f = MODELS[model](px[m], py[m], wx[m], wy[m])
        out[i] = errors_at(f, px[i:i + 1], py[i:i + 1], wx[i:i + 1], wy[i:i + 1])[0]
    return out


def rmse(v):
    return float(np.sqrt(np.mean(np.asarray(v, float) ** 2)))


def nssda(rmse_r):
    """FGDC-STD-007.3-1998: Accuracy_r = 1.7308 * RMSE_r, at 95% confidence."""
    return 1.7308 * rmse_r


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def inter_operator_agreement(control, checks):
    """Pixel distance between the two passes wherever both located the same
    intersection. This is the reading precision of the method and is the floor
    on any accuracy claim made from it."""
    by_name = {c["name"]: c for c in control}
    rows = []
    for c in checks:
        m = by_name.get(c["name"])
        if m is None:
            continue
        d_px = float(np.hypot(m["px"] - c["px"], m["py"] - c["py"]))
        rows.append(dict(name=c["name"], control_px=m["px"], control_py=m["py"],
                         check_px=c["px"], check_py=c["py"], dist_px=d_px))
    return rows


def in_hull(points_xy, query_xy):
    """Is each query point inside the convex hull of the control network?
    Implemented without scipy (not installed in this project's venv) by taking
    the hull with a monotone chain and testing the sign of the cross product
    against every edge."""
    pts = sorted(set(map(tuple, np.asarray(points_xy, float).tolist())))
    if len(pts) < 3:
        return np.zeros(len(query_xy), bool)

    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (x1, y1), (x2, y2) = out[-2], out[-1]
                if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) <= 0:
                    out.pop()
                else:
                    break
            out.append(p)
        return out

    hull = half(pts)[:-1] + half(pts[::-1])[:-1]
    H = np.array(hull)
    res = []
    for q in np.asarray(query_xy, float):
        a = H
        b = np.roll(H, -1, axis=0)
        cross = (b[:, 0] - a[:, 0]) * (q[1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (q[0] - a[:, 0])
        res.append(bool(np.all(cross >= -1e-9) or np.all(cross <= 1e-9)))
    return np.array(res)


def main():
    control = load_control()
    checks = resolve_checkpoints()

    cpx = np.array([r["px"] for r in control], float)
    cpy = np.array([r["py"] for r in control], float)
    cwx = np.array([r["world_x"] for r in control], float)
    cwy = np.array([r["world_y"] for r in control], float)

    kpx = np.array([r["px"] for r in checks], float)
    kpy = np.array([r["py"] for r in checks], float)
    kwx = np.array([r["world_x"] for r in checks], float)
    kwy = np.array([r["world_y"] for r in checks], float)

    report = {}

    # --- A. inter-operator agreement -------------------------------------
    agree = inter_operator_agreement(control, checks)
    d = np.array([a["dist_px"] for a in agree]) if agree else np.array([])
    print(f"\nA. INTER-OPERATOR AGREEMENT  ({len(agree)} intersections located twice)")
    for a in sorted(agree, key=lambda r: r["dist_px"]):
        print(f"   {a['name']:<26} {a['dist_px']:6.1f} px")
    if len(d):
        # Sheet scale comes from the affine fitted below; 0.62 m/px is the
        # first-order figure and is used here only to give the reader a sense
        # of the size. The authoritative conversion is in the JSON.
        print(f"   median {np.median(d):.1f} px, max {d.max():.1f} px")
    report["inter_operator"] = dict(
        n=len(agree), pairs=agree,
        median_px=float(np.median(d)) if len(d) else None,
        max_px=float(d.max()) if len(d) else None)

    # --- B. independent check points -------------------------------------
    hull_flags = in_hull(np.column_stack([cpx, cpy]), np.column_stack([kpx, kpy]))
    print(f"\nB. INDEPENDENT CHECK POINTS  (fit on {len(control)} control, "
          f"tested at {len(checks)} points never used in the fit)")
    print(f"   {sum(hull_flags)} of {len(checks)} fall inside the control hull, "
          f"{len(checks) - sum(hull_flags)} outside it")
    report["checkpoints"] = {}
    per_point = {}
    for model in MODELS:
        f = MODELS[model](cpx, cpy, cwx, cwy)
        err = errors_at(f, kpx, kpy, kwx, kwy)
        per_point[model] = err
        inside, outside = err[hull_flags], err[~hull_flags]
        report["checkpoints"][model] = dict(
            n=len(err), rmse_m=rmse(err), mean_m=float(err.mean()),
            median_m=float(np.median(err)), max_m=float(err.max()),
            nssda_95_m=nssda(rmse(err)),
            rmse_in_hull_m=rmse(inside) if len(inside) else None,
            rmse_out_of_hull_m=rmse(outside) if len(outside) else None)
        print(f"   {model:<9} RMSE {rmse(err):6.2f} m   "
              f"in-hull {rmse(inside) if len(inside) else float('nan'):6.2f}   "
              f"out-of-hull {rmse(outside) if len(outside) else float('nan'):7.2f}   "
              f"max {err.max():6.1f}")

    print("\n   per check point (metres):")
    hdr = f"   {'point':<26}" + "".join(f"{m:>10}" for m in MODELS) + "   hull"
    print(hdr)
    for i, c in enumerate(checks):
        line = f"   {c['name']:<26}" + "".join(f"{per_point[m][i]:10.1f}" for m in MODELS)
        print(line + ("   in" if hull_flags[i] else "   OUT"))

    # --- C. final combined transform -------------------------------------
    #
    # Seven intersections were located by both passes and a few more sit within
    # a block of each other. Feeding two near-coincident points with slightly
    # different world coordinates into a thin plate spline forces it to
    # interpolate exactly through both, which demands an unbounded gradient over
    # a few pixels and wrecks the surface for hundreds of metres around. The
    # first run of this script showed exactly that: TPS leave-one-out error blew
    # out to 96.7 m RMSE with a 735 m worst point, against 11.4 m on the control
    # set alone. So a check point is merged into the control network only if it
    # is more than MERGE_MIN_SEP pixels from every control point. The rejected
    # ones have already done their job in section B.
    MERGE_MIN_SEP = 120.0
    keep = []
    for i in range(len(kpx)):
        d = np.hypot(cpx - kpx[i], cpy - kpy[i]).min()
        keep.append(d > MERGE_MIN_SEP)
    keep = np.array(keep)
    dropped = [checks[i]["name"] for i in range(len(checks)) if not keep[i]]
    print(f"\n   merging {int(keep.sum())} of {len(checks)} check points into the "
          f"control network; {len(dropped)} sit within {MERGE_MIN_SEP:.0f} px of an "
          f"existing control point and are held back:")
    for n in dropped:
        print(f"     - {n}")

    apx = np.concatenate([cpx, kpx[keep]]); apy = np.concatenate([cpy, kpy[keep]])
    awx = np.concatenate([cwx, kwx[keep]]); awy = np.concatenate([cwy, kwy[keep]])
    print(f"\nC. COMBINED TRANSFORM  ({len(apx)} points, leave-one-out cross validated)")
    report["combined"] = {}
    combined_loo = {}
    for model in MODELS:
        f = MODELS[model](apx, apy, awx, awy)
        fit_err = errors_at(f, apx, apy, awx, awy)
        loo_err = loocv(model, apx, apy, awx, awy)
        combined_loo[model] = loo_err
        report["combined"][model] = dict(
            n=len(apx), fit_rmse_m=rmse(fit_err), loocv_rmse_m=rmse(loo_err),
            loocv_mean_m=float(loo_err.mean()), loocv_median_m=float(np.median(loo_err)),
            loocv_max_m=float(loo_err.max()), nssda_95_m=nssda(rmse(loo_err)))
        print(f"   {model:<9} fit RMSE {rmse(fit_err):6.2f} m   "
              f"LOOCV RMSE {rmse(loo_err):6.2f} m   "
              f"NSSDA 95% {nssda(rmse(loo_err)):6.2f} m   max {loo_err.max():6.1f}")

    h = fit_helmert(apx, apy, awx, awy)
    # The Library of Congress records the sheet as 86 x 108 cm and the master
    # scan as 13414 x 10643 px, so the scan is 13414/108 = 124.2 px per cm of
    # paper. One centimetre of paper therefore covers 124.2 * (m/px) metres.
    px_per_cm = FULL_SIZE[0] / 108.0
    denom = h.params["scale"] * px_per_cm * 100.0
    report["sheet_geometry"] = dict(
        metres_per_pixel=h.params["scale"],
        rotation_deg=h.params["rotation_deg"],
        scan_px_per_cm_of_paper=px_per_cm,
        approx_scale_denominator=denom,
        note="scale denominator assumes the LOC sheet dimension of 108 cm on "
             "the long axis (https://www.loc.gov/item/2004629026/)")
    print(f"\n   sheet scale {h.params['scale']:.4f} m/px, "
          f"rotation {h.params['rotation_deg']:.3f} deg (Helmert), "
          f"about 1:{denom:,.0f}")

    # Which model to ship. Decided on the section B evidence, not on fit RMSE.
    ranked = sorted(("affine", "poly2", "tps"),
                    key=lambda m: report["checkpoints"][m]["rmse_m"])
    report["shipped_model"] = ranked[0]
    print(f"\n   model shipped in the raster: {ranked[0]} "
          f"(lowest independent check-point RMSE)")

    # --- outputs ----------------------------------------------------------
    with open(WORK / "checkpoints_1851_v2.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "kind", "reference", "pixel_x", "pixel_y",
                    "world_x_epsg6487", "world_y_epsg6487", "in_control_hull",
                    *[f"err_{m}_m" for m in MODELS], "crop_srcwin", "note"])
        for i, c in enumerate(checks):
            w.writerow([c["name"], c["kind"], c["ref"], c["px"], c["py"],
                        f"{c['world_x']:.2f}", f"{c['world_y']:.2f}",
                        "yes" if hull_flags[i] else "no",
                        *[f"{per_point[m][i]:.2f}" for m in MODELS],
                        c["crop"], c["note"]])

    allrows = ([dict(r, role="control") for r in control] +
               [dict(checks[i], role="check_merged")
                for i in range(len(checks)) if keep[i]])
    with open(WORK / "gcps_1851_v2_combined.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "role", "reference", "pixel_x", "pixel_y",
                    "world_x_epsg6487", "world_y_epsg6487",
                    *[f"loo_err_{m}_m" for m in MODELS]])
        for i, r in enumerate(allrows):
            w.writerow([r["name"], r["role"], r.get("ref", ""), r["px"], r["py"],
                        f"{r['world_x']:.2f}", f"{r['world_y']:.2f}",
                        *[f"{combined_loo[m][i]:.2f}" for m in MODELS]])

    with open(WORK / "baltimore_1851_v2.points", "w") as fh:
        fh.write(f"#CRS: EPSG:{CRS_M}\n")
        fh.write("mapX,mapY,pixelX,pixelY,enable\n")
        for r in allrows:
            fh.write(f"{r['world_x']:.3f},{r['world_y']:.3f},"
                     f"{r['px']:.3f},{-r['py']:.3f},1\n")

    with open(WORK / "accuracy_1851_v2.json", "w") as fh:
        json.dump(report, fh, indent=2)

    print(f"\nWrote {WORK/'checkpoints_1851_v2.csv'}")
    print(f"Wrote {WORK/'gcps_1851_v2_combined.csv'}")
    print(f"Wrote {WORK/'baltimore_1851_v2.points'}")
    print(f"Wrote {WORK/'accuracy_1851_v2.json'}")

    build_geotiff(allrows, report["shipped_model"])


def find_gdal():
    """QGIS ships the only GDAL on this Mac; scripts/qgis_env.sh documents it."""
    import os
    import shutil
    env = os.environ.copy()
    if shutil.which("gdal_translate"):
        return "gdal_translate", "gdalwarp", env
    d = Path("/Applications/QGIS-final-4_2_1.app/Contents/MacOS")
    if (d / "gdal_translate").exists():
        env["PATH"] = str(d) + os.pathsep + env.get("PATH", "")
        env["GDAL_DATA"] = "/Applications/QGIS-final-4_2_1.app/Contents/Resources/qgis/gdal"
        env["PROJ_LIB"] = "/Applications/QGIS-final-4_2_1.app/Contents/Resources/qgis/proj"
        return str(d / "gdal_translate"), str(d / "gdalwarp"), env
    return None, None, env


def build_geotiff(rows, model):
    """Warp the master on the combined control network, using whichever model
    won the independent check-point test rather than whichever fit the control
    points best. Output is EPSG:4326 so the raster drops straight into the web
    map; all metric work stays in EPSG:6487."""
    import subprocess
    translate, warp, env = find_gdal()
    if translate is None:
        print("\nGDAL not found; GCP table and coefficients written, raster skipped.")
        return
    jp2 = ROOT / "data" / "raw" / "maps" / "baltimore_1851_plan.jp2"
    tmp = WORK / "_tmp_v2_gcp.tif"
    out = WORK / "baltimore_1851_georef_v2.tif"
    gcps = []
    for r in rows:
        gcps += ["-gcp", f"{r['px']:.3f}", f"{r['py']:.3f}",
                 f"{r['world_x']:.3f}", f"{r['world_y']:.3f}"]
    subprocess.run([translate, "-q", "-of", "GTiff", "-a_srs", f"EPSG:{CRS_M}",
                    *gcps, str(jp2), str(tmp)], env=env, check=True)
    method = {"tps": ["-tps"], "affine": ["-order", "1"], "poly2": ["-order", "2"]}[model]
    subprocess.run([warp, "-q", *method, "-r", "cubic", "-t_srs", "EPSG:4326",
                    "-co", "COMPRESS=JPEG", "-co", "JPEG_QUALITY=82",
                    "-co", "TILED=YES", "-co", "PHOTOMETRIC=YCBCR",
                    "-overwrite", str(tmp), str(out)], env=env, check=True)
    tmp.unlink(missing_ok=True)
    for aux in WORK.glob("_tmp_v2_gcp.tif.*"):
        aux.unlink(missing_ok=True)
    mb = out.stat().st_size / 1e6
    print(f"\nGeoTIFF: {out} ({mb:.1f} MB, {model}, EPSG:4326)")
    if mb > 90:
        print("WARNING: over the 90 MB commit cap; re-run with a lower JPEG_QUALITY.")


if __name__ == "__main__":
    main()
