#!/usr/bin/env python3
"""Georeference Sidney & Neff, *Plan of the City of Baltimore*, 1851.

This is the redo of scripts/georeference_1851.py, which is left in place for
comparison. The first attempt had three faults that this one is built to avoid:

  1. Twelve control points, seven of them on Baltimore Street. The network was
     nearly collinear, so it pinned the east-west axis and barely constrained
     the north-south one.
  2. RMSE was reported on the same points the transform was fitted to. That is
     training error and is optimistically biased by construction.
  3. Control coordinates were taken from the HUE circa-1930 street file, which
     is the very layer the 1851 result was supposed to be compared against.
     Fitting to HUE and then measuring disagreement with HUE is circular: the
     fit absorbs HUE's own error into the transform and then reports what is
     left as if it were the map's error.

What this script does instead
-----------------------------
CONTROL TARGET. World coordinates come from the modern authoritative Baltimore
City street centreline file (911 / AddressDB StreetCity, ArcGIS REST), not from
HUE. Modern centrelines are survey grade and completely independent of both the
1851 sheet and the c.1930 HUE digitisation, so the 1851-vs-HUE comparison at the
end is a genuine three-way check rather than a tautology.

The assumption this buys, and it is a real assumption, is that a named street
intersection in the built-up core has not physically moved between 1851 and
today. That holds well for the old grid and badly for filled land, so every
control point sits on a street crossing in the built city and none sits on a
shoreline, a wharf, a watercourse, or on Locust Point (see EXCLUDED below).

CONTROL POINTS. 54 of them, each read visually off the full-resolution jp2
(13414 x 10643) by cropping the neighbourhood and reading the street corridor
crossing against a labelled pixel grid. Nothing here is inferred from the
transform: a point was recorded only where the two named streets could be seen
crossing. Coverage was chosen over count, so the set reaches Gilmor Street in
the west, Canton in the east, Greenmount at Lanvale in the north and Cross
Street in the south.

FITS. First-order (affine), second-order polynomial, and thin plate spline.
TPS interpolates exactly at the control points, so its fit residual is ~0 by
construction and is NOT an accuracy measure; only its cross-validated error
means anything.

HEADLINE NUMBER. Leave-one-out cross validation. Fit on n-1 points, predict the
held-out one, repeat n times, report the RMS of those held-out errors. Fit RMSE
is reported too, and the gap between them is the honest measure of how much each
model is fitting noise.

Outputs
  data/work/maps/gcps_1851.csv              GCP table, per-point fit residuals
                                            and per-point leave-one-out errors
  data/work/maps/baltimore_1851_georef.tif  GeoTIFF (if GDAL is reachable)
  docs/georef/1851.md                       written by hand, not by this script

  --points additionally emits a QGIS Georeferencer .points file. It is off by
  default so that this script does not overwrite the one belonging to the
  original scripts/georeference_1851.py.

Provenance
  Map:      Sidney & Neff / Lloyd Van Derveer, Plan of the City of Baltimore,
            June 1851. Library of Congress, https://www.loc.gov/item/2004629026/
            Local copy data/raw/maps/baltimore_1851_plan.jp2, 13414 x 10643.
  Control:  Baltimore City street centrelines (911 StreetCity), ArcGIS REST at
            https://egisdata.baltimorecity.gov/egis/rest/services/911/Street_City/MapServer/0
            accessed 2026-08-08. Cached in the system temp directory on first
            run, so no extra file lands in the repo; the resolved world
            coordinates are recorded in gcps_1851.csv either way.
  Compared: HUE Baltimore streets, ICPSR 35617, circa 1930.
"""

import csv
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

MAPS = ROOT / "data" / "raw" / "maps"
WORK = ROOT / "data" / "work" / "maps"
WORK.mkdir(parents=True, exist_ok=True)

JP2 = MAPS / "baltimore_1851_plan.jp2"
FULL_SIZE = (13414, 10643)
CRS_EPSG = 6487                    # NAD83(2011) / Maryland, metres

CENTERLINE_URL = ("https://egisdata.baltimorecity.gov/egis/rest/services/"
                  "911/Street_City/MapServer/0/query")
CENTERLINE_CACHE = Path(tempfile.gettempdir()) / "balt_centerlines_2026.geojson"
CENTERLINE_BBOX = "-76.67,39.24,-76.54,39.34"
CENTERLINE_ACCESSED = "2026-08-08"

HUE_SHP = ROOT / "data" / "raw" / "hue" / "HUE_Baltimore_Streets" / "CPE_Baltimore_Streets_HUE_v1.shp"


# ---------------------------------------------------------------------------
# Ground control points.
#
# (label, modern_street_a, modern_street_b, pixel_x, pixel_y, region, note)
#
# pixel_x/pixel_y are FULL-RESOLUTION pixel coordinates on
# data/raw/maps/baltimore_1851_plan.jp2, read visually. `note` records the 1851
# name where it differs from the modern one, and any caveat about the reading.
#
# Old-to-modern name equivalences below were checked against the project's own
# alias table (data/work/street_aliases.csv, from the Gunby index) and, for
# Canton and east Baltimore, confirmed by the fact that whole runs of adjacent
# streets line up one for one with the modern spacing, including two that never
# changed name at all (Curley, Potomac in Canton; Rose, Luzerne in east
# Baltimore). That is the check that makes the renamed neighbours safe to use.
# ---------------------------------------------------------------------------
GCPS = [
    # --- central core -----------------------------------------------------
    ("Charles & Baltimore",    "CHARLES",   "BALTIMORE",  6748, 4415, "core",
     "sheet join runs down Charles St here, so x is the weaker coordinate"),
    ("Calvert & Baltimore",    "CALVERT",   "BALTIMORE",  7135, 4410, "core", ""),
    ("Gay & Baltimore",        "GAY",       "BALTIMORE",  7587, 4407, "core", ""),
    ("Eutaw & Baltimore",      "EUTAW",     "BALTIMORE",  5915, 4435, "core", ""),
    ("Greene & Baltimore",     "GREENE",    "BALTIMORE",  5545, 4448, "core", ""),
    ("Paca & Pratt",           "PACA",      "PRATT",      5748, 4956, "core", ""),
    ("Paca & Lexington",       "PACA",      "LEXINGTON",  5734, 4008, "core",
     "market house sits in the street; corridor centre taken"),
    ("Eutaw & Lexington",      "EUTAW",     "LEXINGTON",  5906, 4008, "core",
     "1851 sheet labels this stretch Louisiana St (Gunby: became part of Lexington)"),
    ("Charles & Franklin",     "CHARLES",   "FRANKLIN",   6740, 3413, "core",
     "Unitarian Church on the NW corner confirms the crossing; sheet join in x"),
    ("Eutaw & Monument",       "EUTAW",     "MONUMENT",   5915, 2975, "core", ""),

    # --- west -------------------------------------------------------------
    ("Poppleton & Baltimore",  "POPPLETON", "BALTIMORE",  4389, 4468, "west", ""),
    ("Carey & Baltimore",      "CAREY",     "BALTIMORE",  3560, 4490, "west", ""),
    ("Gilmor & Baltimore",     "GILMOR",    "BALTIMORE",  2989, 4485, "west", ""),
    ("Stricker & Baltimore",   "STRICKER",  "BALTIMORE",  3181, 4483, "west", ""),
    ("Carey & Lexington",      "CAREY",     "LEXINGTON",  3558, 4043, "west", ""),
    ("Carey & Pratt",          "CAREY",     "PRATT",      3561, 5027, "west", ""),
    ("Scott & Pratt",          "SCOTT",     "PRATT",      4803, 4991, "west", ""),

    # --- east, along Baltimore Street --------------------------------------
    ("Caroline & Baltimore",   "CAROLINE",  "BALTIMORE",  9216, 4196, "east", ""),
    ("Bond & Baltimore",       "BOND",      "BALTIMORE",  9412, 4196, "east", ""),
    ("Broadway & Baltimore",   "BROADWAY",  "BALTIMORE",  9680, 4199, "east", ""),
    ("Castle & Baltimore",     "CASTLE",    "BALTIMORE", 10456, 4199, "east", ""),
    ("Chester & Baltimore",    "CHESTER",   "BALTIMORE", 10576, 4198, "east", ""),
    ("Patterson Park & Baltimore", "PATTERSON PARK", "BALTIMORE", 10934, 4197, "east",
     "1851 name Gist St (Gunby: Patterson Park Ave was Gist St)"),
    ("Rose & Baltimore",       "ROSE",      "BALTIMORE", 11422, 4196, "east",
     "same name on the 1851 sheet"),
    ("Luzerne & Baltimore",    "LUZERNE",   "BALTIMORE", 11526, 4196, "east",
     "same name on the 1851 sheet"),

    # --- Fells Point --------------------------------------------------------
    ("Bond & Aliceanna",       "BOND",      "ALICEANNA",  9422, 5608, "fells", ""),
    ("Wolfe & Fleet",          "WOLFE",     "FLEET",     10160, 5422, "fells", ""),
    ("Broadway & Eastern",     "BROADWAY",  "EASTERN",    9687, 5251, "fells",
     "Eastern Ave was widened in the C20; treat as the weaker Fells Point point"),

    # --- south Baltimore / Federal Hill --------------------------------------
    ("Light & Hughes",         "LIGHT",     "HUGHES",     7035, 6006, "south", ""),
    ("Light & Montgomery",     "LIGHT",     "MONTGOMERY", 7035, 6113, "south", ""),
    ("Light & Warren",         "LIGHT",     "WARREN",     7036, 6300, "south", ""),
    ("Light & Cross",          "LIGHT",     "CROSS",      7037, 6653, "south",
     "Cross Street Market sits in the street; corridor centre taken"),
    ("William & Cross",        "WILLIAM",   "CROSS",      7233, 6653, "south", ""),
    ("William & Montgomery",   "WILLIAM",   "MONTGOMERY", 7233, 6113, "south", ""),
    ("Charles & Cross",        "CHARLES",   "CROSS",      6728, 6653, "south",
     "sheet join runs down Charles St here"),

    # --- Canton --------------------------------------------------------------
    ("Kenwood & O'Donnell",    "KENWOOD",   "O'DONNELL", 11931, 6328, "canton",
     "1851 name Chesapeake St"),
    ("Linwood & O'Donnell",    "LINWOOD",   "O'DONNELL", 12131, 6328, "canton",
     "1851 name Patuxent St"),
    ("Curley & O'Donnell",     "CURLEY",    "O'DONNELL", 12228, 6328, "canton",
     "same name on the 1851 sheet"),
    ("Curley & Elliott",       "CURLEY",    "ELLIOTT",   12230, 6507, "canton",
     "same name on the 1851 sheet"),
    ("Ellwood & O'Donnell",    "ELLWOOD",   "O'DONNELL", 12528, 6328, "canton",
     "1851 name Canton St"),

    # --- north east ----------------------------------------------------------
    ("Broadway & Monument",    "BROADWAY",  "MONUMENT",   9673, 2981, "northeast", ""),
    ("Wolfe & Monument",       "WOLFE",     "MONUMENT",  10143, 2984, "northeast", ""),
    ("Aisquith & Monument",    "AISQUITH",  "MONUMENT",   8637, 2990, "northeast",
     "Aisquith is a diagonal; crossing read where the corridor centres meet"),
    ("Harford & Chase",        "HARFORD",   "CHASE",      8525, 2126, "northeast",
     "Harford Ave is a diagonal; weaker reading"),
    ("Gay & Preston",          "GAY",       "PRESTON",    9950, 1722, "northeast",
     "Gay St is wide here and a run passes close by; weaker reading"),

    # --- north ---------------------------------------------------------------
    ("Guilford & Biddle",      "GUILFORD",  "BIDDLE",     7282, 1925, "north",
     "1851 name North St"),
    ("Barclay & Chase",        "BARCLAY",   "CHASE",      7495, 2118, "north", ""),
    ("St Paul & Preston",      "SAINT PAUL", "PRESTON",   6964, 1737, "north", ""),
    ("Calvert & Preston",      "CALVERT",   "PRESTON",    7111, 1735, "north", ""),
    ("Greenmount & Preston",   "GREENMOUNT", "PRESTON",   7806, 1728, "north", ""),
    ("Greenmount & Federal",   "GREENMOUNT", "FEDERAL",   7733, 1158, "north", ""),
    ("Greenmount & Lanvale",   "GREENMOUNT", "LANVALE",   7700,  988, "north",
     "northernmost verified point on the sheet"),

    # --- north west ----------------------------------------------------------
    ("Etting & Lanvale",       "ETTING",    "LANVALE",    4922, 2194, "northwest",
     "Etting keeps its name on the 1851 sheet; the label lies along the line "
     "through this crossing and the Dolphin one"),
    ("Etting & Dolphin",       "ETTING",    "DOLPHIN",    5037, 2346, "northwest",
     "Etting keeps its name on the 1851 sheet"),
]

# Intersections that were located on the sheet but deliberately NOT used, with
# the reason. Recording these matters as much as recording the ones that were
# used: it is the difference between a gap that was noticed and a gap that was
# hidden.
EXCLUDED = [
    ("Fort Ave & Lawrence St, Locust Point",
     "Locust Point was still largely a paper subdivision in 1851 and the whole "
     "peninsula was later filled and re-platted for the railway terminal. The "
     "1851 lot lines there cannot be assumed to be today's streets."),
    ("Thames St & Bond St, Fells Point waterfront",
     "The Fells Point wharf line was filled and rebuilt. Waterfront points are "
     "measuring made ground, not surveyed streets."),
    ("Pennsylvania Ave and the Bolton Hill / Madison Park grid",
     "The far north west of the sheet is a speculative lot layout over ground "
     "that was mostly unbuilt in 1851, and most of its street names were later "
     "changed. Identities could not be confirmed street by street without "
     "assuming the answer, so no control point was taken west of Etting St "
     "north of Franklin St. This is the sheet's real coverage gap."),
    ("Any intersection on the Jones Falls or Harford Run",
     "Both were culverted and rerouted. Watercourse crossings are traps."),
]


# ---------------------------------------------------------------------------
# Control geometry: modern Baltimore City centrelines
# ---------------------------------------------------------------------------

def fetch_centerlines():
    """Download (once) the modern city centrelines inside the map's bbox.

    The ArcGIS MapServer ignores resultOffset paging on this layer, so ids are
    pulled first and then fetched in POST batches (a GET with 500 ids exceeds
    the URL length limit and 404s)."""
    if CENTERLINE_CACHE.exists():
        return CENTERLINE_CACHE

    def post(params):
        req = urllib.request.Request(CENTERLINE_URL,
                                     data=urllib.parse.urlencode(params).encode())
        return json.loads(urllib.request.urlopen(req, timeout=180).read())

    ids = post(dict(where="1=1", geometry=CENTERLINE_BBOX,
                    geometryType="esriGeometryEnvelope", inSR="4326",
                    spatialRel="esriSpatialRelIntersects", f="json",
                    returnIdsOnly="true"))["objectIds"]
    feats = []
    for i in range(0, len(ids), 500):
        r = post(dict(objectIds=",".join(map(str, ids[i:i + 500])),
                      outFields="FULLNAME,FEANME,DIRPRE,FEATYPE,DIRSUF",
                      outSR="4326", f="geojson", returnGeometry="true"))
        feats += r.get("features", [])
    CENTERLINE_CACHE.write_text(json.dumps({"type": "FeatureCollection",
                                            "features": feats}))
    print(f"fetched {len(feats)} modern centreline segments -> {CENTERLINE_CACHE}")
    return CENTERLINE_CACHE


_modern = None


def modern_streets():
    global _modern
    if _modern is None:
        import geopandas as gpd
        _modern = gpd.read_file(fetch_centerlines()).to_crs(epsg=CRS_EPSG)
    return _modern


def modern_intersection(a, b):
    """(x, y) in EPSG:6487 where modern street a crosses modern street b."""
    from shapely.geometry import Point
    from shapely.ops import nearest_points, unary_union
    g = modern_streets()
    parts = []
    for name in (a, b):
        sel = g[g["FEANME"] == name]
        if sel.empty:
            raise KeyError(f"no modern street named {name!r}")
        parts.append(unary_union(sel.geometry.values))
    ga, gb = parts
    inter = ga.intersection(gb)
    if inter.is_empty:
        # Centrelines that stop a few metres short of each other at a node.
        d = ga.distance(gb)
        if d > 30.0:
            raise ValueError(f"{a} and {b} are {d:.1f} m apart")
        p, q = nearest_points(ga, gb)
        return (p.x + q.x) / 2, (p.y + q.y) / 2
    pts = [inter] if inter.geom_type == "Point" else [
        p if p.geom_type == "Point" else p.centroid
        for p in getattr(inter, "geoms", [inter])]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    spread = max(max(xs) - min(xs), max(ys) - min(ys))
    if spread > 60:
        raise ValueError(f"{a} x {b}: {len(pts)} crossings spread {spread:.0f} m")
    return sum(xs) / len(xs), sum(ys) / len(ys)


# ---------------------------------------------------------------------------
# Comparison geometry: HUE circa 1930
# ---------------------------------------------------------------------------

_hue = None


def hue_streets():
    """One merged geometry per normalised HUE street name.

    Reuses norm_street() from scripts/geocode_1860.py rather than
    reimplementing the project's street-name normalisation. Unlike
    geocode_1860.load_streets() this does NOT layer modern centrelines
    underneath, because the whole point here is to isolate what HUE alone says.
    """
    global _hue
    if _hue is None:
        import geopandas as gpd
        from shapely.ops import unary_union
        import geocode_1860 as g
        hue = gpd.read_file(HUE_SHP).to_crs(epsg=CRS_EPSG)
        buckets = defaultdict(list)
        for name, geom in zip(hue["Full_Name"], hue.geometry):
            core, _ = g.norm_street(name)
            if core:
                buckets[core].append(geom)
        _hue = {k: unary_union(v) for k, v in buckets.items()}
    return _hue


def hue_intersection(a, b, near):
    """Where HUE puts the crossing of a and b, or None. `near` disambiguates."""
    from shapely.geometry import Point
    s = hue_streets()
    ga, gb = s.get(a), s.get(b)
    if ga is None or gb is None:
        return None
    inter = ga.intersection(gb)
    if inter.is_empty:
        return None
    pts = [inter] if inter.geom_type == "Point" else [
        p if p.geom_type == "Point" else p.centroid
        for p in getattr(inter, "geoms", [inter])]
    hp = Point(near)
    best = min(pts, key=lambda p: p.distance(hp))
    if best.distance(hp) > 400:
        return None            # a different crossing of the same two names
    return best.x, best.y


# ---------------------------------------------------------------------------
# Transforms.  Each is fit(P, W) -> predictor(P) -> W
#   P is (n, 2) pixel coordinates, W is (n, 2) world coordinates in metres.
# ---------------------------------------------------------------------------

def _poly_terms(P, order):
    x, y = P[:, 0], P[:, 1]
    if order == 1:
        return np.column_stack([np.ones_like(x), x, y])
    return np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])


def fit_poly(P, W, order):
    A = _poly_terms(P, order)
    coef, *_ = np.linalg.lstsq(A, W, rcond=None)
    return lambda Q: _poly_terms(Q, order) @ coef


def fit_tps(P, W, smooth=0.0):
    """Thin plate spline. Exact interpolant at the control points when
    smooth == 0, which is why its fit residual is meaningless as accuracy."""
    n = len(P)
    # Scale pixels to a sane magnitude so the U = r^2 log r kernel is stable.
    s = 1000.0
    Q = P / s
    d = np.sqrt(((Q[:, None, :] - Q[None, :, :]) ** 2).sum(-1))
    U = np.where(d > 0, d ** 2 * np.log(np.where(d > 0, d, 1.0)), 0.0)
    K = U + smooth * np.eye(n)
    Pm = np.column_stack([np.ones(n), Q])
    L = np.zeros((n + 3, n + 3))
    L[:n, :n] = K
    L[:n, n:] = Pm
    L[n:, :n] = Pm.T
    rhs = np.zeros((n + 3, 2))
    rhs[:n] = W
    sol = np.linalg.lstsq(L, rhs, rcond=None)[0]
    wts, aff = sol[:n], sol[n:]

    def predict(R):
        Rq = R / s
        dd = np.sqrt(((Rq[:, None, :] - Q[None, :, :]) ** 2).sum(-1))
        UU = np.where(dd > 0, dd ** 2 * np.log(np.where(dd > 0, dd, 1.0)), 0.0)
        return np.column_stack([np.ones(len(R)), Rq]) @ aff + UU @ wts

    return predict


MODELS = {
    "affine":  lambda P, W: fit_poly(P, W, 1),
    "poly2":   lambda P, W: fit_poly(P, W, 2),
    "tps":     lambda P, W: fit_tps(P, W),
}


def errors(pred, P, W):
    D = pred(P) - W
    return np.hypot(D[:, 0], D[:, 1])


def loocv(model, P, W):
    """Leave-one-out: fit on n-1, predict the held-out one. The honest number."""
    out = np.zeros(len(P))
    for i in range(len(P)):
        keep = np.ones(len(P), bool)
        keep[i] = False
        pred = MODELS[model](P[keep], W[keep])
        d = pred(P[i:i + 1]) - W[i:i + 1]
        out[i] = math.hypot(d[0, 0], d[0, 1])
    return out


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

def write_csv(rows, path):
    cols = ["name", "region", "modern_street_a", "modern_street_b",
            "pixel_x", "pixel_y", "world_x_epsg6487", "world_y_epsg6487",
            "lon_wgs84", "lat_wgs84",
            "fit_resid_affine_m", "fit_resid_poly2_m", "fit_resid_tps_m",
            "loo_err_affine_m", "loo_err_poly2_m", "loo_err_tps_m",
            "hue_offset_m", "note"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def write_points_file(rows, path):
    """QGIS Georeferencer .points format. QGIS stores pixel row as negative."""
    with open(path, "w") as f:
        f.write(f"#CRS: EPSG:{CRS_EPSG}\n")
        f.write("mapX,mapY,pixelX,pixelY,enable\n")
        for r in rows:
            f.write(f"{r['world_x_epsg6487']:.3f},{r['world_y_epsg6487']:.3f},"
                    f"{r['pixel_x']:.1f},{-r['pixel_y']:.1f},1\n")


def find_gdal():
    """gdal_translate / gdalwarp, preferring the QGIS bundle (scripts/qgis_env.sh)."""
    env = os.environ.copy()
    if shutil.which("gdal_translate") and shutil.which("gdalwarp"):
        return "gdal_translate", "gdalwarp", env
    base = Path("/Applications/QGIS-final-4_2_1.app/Contents")
    t, w = base / "MacOS" / "gdal_translate", base / "MacOS" / "gdalwarp"
    if t.exists() and w.exists():
        env["PATH"] = str(base / "MacOS") + os.pathsep + env.get("PATH", "")
        env["GDAL_DATA"] = str(base / "Resources" / "qgis" / "gdal")
        env["PROJ_LIB"] = str(base / "Resources" / "qgis" / "proj")
        return str(t), str(w), env
    return None, None, env


def build_geotiff(rows, out_path, order=1, max_mb=90):
    translate, warp, env = find_gdal()
    if translate is None:
        print("GDAL not found; skipping GeoTIFF. The .points file and the "
              "coefficients printed above are enough to apply the transform.")
        return None
    gcp_args = []
    for r in rows:
        gcp_args += ["-gcp", f"{r['pixel_x']:.1f}", f"{r['pixel_y']:.1f}",
                     f"{r['world_x_epsg6487']:.3f}", f"{r['world_y_epsg6487']:.3f}"]
    tmp = WORK / "_tmp_1851_redo_gcp.tif"
    subprocess.run([translate, "-of", "GTiff", "-a_srs", f"EPSG:{CRS_EPSG}",
                    *gcp_args, str(JP2), str(tmp)], env=env, check=True)

    def warp_at(scale, dest):
        cmd = [warp, "-r", "cubic", "-order", str(order),
               "-t_srs", f"EPSG:{CRS_EPSG}",
               "-co", "COMPRESS=JPEG", "-co", "JPEG_QUALITY=80",
               "-co", "TILED=YES", "-co", "PHOTOMETRIC=YCBCR",
               "-overwrite"]
        if scale != 1.0:
            cmd += ["-ts", str(int(FULL_SIZE[0] * scale)), "0"]
        cmd += [str(tmp), str(dest)]
        subprocess.run(cmd, env=env, check=True)
        return dest.stat().st_size / 1e6

    scale = 1.0
    size = warp_at(scale, out_path)
    while size > max_mb and scale > 0.2:
        scale *= 0.7
        print(f"  {size:.0f} MB is over the {max_mb} MB cap; retrying at "
              f"{scale:.2f} of full resolution")
        size = warp_at(scale, out_path)
    tmp.unlink(missing_ok=True)
    for aux in WORK.glob("_tmp_1851_redo_gcp.tif.*"):
        aux.unlink(missing_ok=True)
    print(f"GeoTIFF: {out_path} ({size:.1f} MB, order={order}, "
          f"{scale:.2f} of full resolution)")
    return out_path


# ---------------------------------------------------------------------------

def main():
    import pyproj

    rows = []
    for label, a, b, px, py, region, note in GCPS:
        try:
            wx, wy = modern_intersection(a, b)
        except Exception as e:
            print(f"DROPPED {label}: {e}")
            continue
        rows.append({"name": label, "region": region, "modern_street_a": a,
                     "modern_street_b": b, "pixel_x": float(px),
                     "pixel_y": float(py), "world_x_epsg6487": wx,
                     "world_y_epsg6487": wy, "note": note})

    P = np.array([[r["pixel_x"], r["pixel_y"]] for r in rows])
    W = np.array([[r["world_x_epsg6487"], r["world_y_epsg6487"]] for r in rows])
    n = len(rows)

    print(f"\n{n} ground control points, all read visually off the "
          f"full-resolution sheet\n")
    print(f"{'model':10s}{'fit RMSE':>12s}{'fit max':>10s}"
          f"{'LOO RMSE':>12s}{'LOO median':>12s}{'LOO max':>10s}")
    summary = {}
    for m in ("affine", "poly2", "tps"):
        fit_err = errors(MODELS[m](P, W), P, W)
        loo_err = loocv(m, P, W)
        summary[m] = (fit_err, loo_err)
        print(f"{m:10s}{np.sqrt((fit_err**2).mean()):11.1f}m{fit_err.max():9.1f}m"
              f"{np.sqrt((loo_err**2).mean()):11.1f}m"
              f"{np.median(loo_err):11.1f}m{loo_err.max():9.1f}m")
    print("\nTPS interpolates exactly at the control points, so its fit RMSE is "
          "~0 by construction\nand is not an accuracy measure. Only its "
          "leave-one-out column means anything.")

    # Displacement of HUE c.1930 from the modern survey, at the same crossings.
    hue_offsets = []
    for r in rows:
        h = hue_intersection(r["modern_street_a"], r["modern_street_b"],
                             (r["world_x_epsg6487"], r["world_y_epsg6487"]))
        if h is None:
            r["hue_offset_m"] = ""
        else:
            d = math.hypot(h[0] - r["world_x_epsg6487"],
                           h[1] - r["world_y_epsg6487"])
            r["hue_offset_m"] = f"{d:.1f}"
            hue_offsets.append((r["name"], r["region"], d))

    to4326 = pyproj.Transformer.from_crs(CRS_EPSG, 4326, always_xy=True)
    for r, fa, f2, ft, la, l2, lt in zip(
            rows, summary["affine"][0], summary["poly2"][0], summary["tps"][0],
            summary["affine"][1], summary["poly2"][1], summary["tps"][1]):
        lon, lat = to4326.transform(r["world_x_epsg6487"], r["world_y_epsg6487"])
        r.update({"lon_wgs84": f"{lon:.6f}", "lat_wgs84": f"{lat:.6f}",
                  "world_x_epsg6487": round(r["world_x_epsg6487"], 2),
                  "world_y_epsg6487": round(r["world_y_epsg6487"], 2),
                  "fit_resid_affine_m": f"{fa:.1f}", "fit_resid_poly2_m": f"{f2:.1f}",
                  "fit_resid_tps_m": f"{ft:.2f}", "loo_err_affine_m": f"{la:.1f}",
                  "loo_err_poly2_m": f"{l2:.1f}", "loo_err_tps_m": f"{lt:.1f}"})

    print(f"\nPer point, worst leave-one-out first "
          f"(affine fit residual / affine LOO error / HUE offset):")
    order = np.argsort(-summary["affine"][1])
    for i in order:
        r = rows[i]
        print(f"  {r['name']:28s}{r['region']:11s}"
              f"{summary['affine'][0][i]:7.1f}m{summary['affine'][1][i]:8.1f}m"
              f"   HUE {r['hue_offset_m'] or '--':>6}")

    if hue_offsets:
        d = np.array([h[2] for h in hue_offsets])
        print(f"\nHUE c.1930 vs the modern survey at {len(d)} of these crossings: "
              f"median {np.median(d):.0f} m, mean {d.mean():.0f} m, "
              f"max {d.max():.0f} m ({max(hue_offsets, key=lambda t: t[2])[0]})")

    write_csv(rows, WORK / "gcps_1851.csv")
    print(f"\nWrote {WORK / 'gcps_1851.csv'}")
    if "--points" in sys.argv:
        write_points_file(rows, WORK / "gcps_1851_qgis.points")
        print(f"Wrote {WORK / 'baltimore_1851_v2.points'}")

    if "--no-tif" not in sys.argv:
        build_geotiff(rows, WORK / "baltimore_1851_georef.tif", order=1)


if __name__ == "__main__":
    main()
