#!/usr/bin/env python3
"""Georeference Fielding Lucas Jr.'s 1836 'Plan of the City of Baltimore', and
quantify how far it disagrees with the c.1930 HUE street survey that the rest
of this project currently places residents against.

Source and provenance
---------------------
Library of Congress, Geography and Map Division.
  Item page : https://www.loc.gov/item/2002624026/
  Title     : "Plan of the city of Baltimore"
  Imprint   : Baltimore : published by F. Lucas Jr., [1836]
  Sheet     : 1 map : hand colored ; 50 x 67 cm
  Master JP2: https://tile.loc.gov/storage-services/service/gmd/gmd384/g3844/g3844b/wd000016.jp2
              6923 x 5374 px, 7.35 MB
  Accessed  : 2026-08-08

The 680 KB file already in the repo
(data/raw/maps/baltimore_1836_plan_preview.jpg, 1731 x 1344) is a preview only.
Every pixel coordinate below was read on the FULL-RESOLUTION 6923 x 5374 JP2,
which this script will download if it is not already on disk.

Method
------
1.  42 ground control points, each a street/street intersection, were located
    by eye on the full-resolution scan.  The procedure for every one of them:
    crop a 230-900 px neighbourhood with Pillow, upscale it to ~1500 px wide
    (2.3x to 6x), overlay a labelled 25 or 50 px coordinate grid, and read the
    crossing off that image.  Reading precision is about +/-5 source px, which
    at this map's scale (1.31 m/px) is about +/-7 m.  Nothing here was inferred
    from a street's expected position: every point was seen.  Where a street's
    NAME could not be read next to the crossing itself, that is recorded in the
    `note` field of the GCP table below and repeated in the output CSV.
2.  Each pair's real-world coordinate is resolved the way the rest of this
    project resolves intersections: scripts/geocode_1860.load_streets() loads
    the HUE c.1930 centrelines (ICPSR 35617) clipped to the 1846-1860 ward
    boundary, with modern centrelines filling in only names HUE lacks, and the
    two named lines are intersected.  This reuses norm_street() and the alias
    table rather than duplicating them.
3.  Three transforms are fitted pixel -> EPSG:6487 (NAD83 Maryland, metres):
    first-order polynomial (affine), second-order polynomial, and thin plate
    spline.
4.  The headline accuracy number is LEAVE-ONE-OUT CROSS VALIDATED error: fit on
    41 points, predict the 42nd, repeat 42 times.  Fit RMSE is also reported.
    TPS interpolates exactly at its control points, so its fit residual is 0 by
    construction and is not an accuracy measure at all; only its LOO number
    means anything.

On circularity
--------------
The control coordinates come from the same c.1930 HUE layer this map is being
compared against.  That is deliberate and it bounds what the result can claim.

  - What it CAN say: after removing the best global affine (a single scale,
    rotation, and shift), where and by how much does the 1836 draughtsman's
    geometry disagree LOCALLY with the 1930 survey?  That is exactly the
    question that matters for re-placing residents, and the residuals answer
    it directly.
  - What it CANNOT say: anything about the absolute geodetic accuracy of
    either source.  A uniform citywide error in HUE would be absorbed into the
    fitted affine and would leave no trace in the residuals.  This map cannot
    detect that, and no georeference of it against HUE ever could.

To get a genuinely independent check on HUE one would need control coordinates
from a source that is not HUE (a modern survey-grade layer, or GPS on surviving
1836 structures).  That is a separate job and is not attempted here.

Outputs
-------
  data/work/maps/gcps_1836.csv              GCP table, per-point residuals AND
                                            per-point leave-one-out errors
  data/work/maps/baltimore_1836.points      QGIS Georeferencer format
  data/work/maps/baltimore_1836_georef.tif  GeoTIFF, EPSG:6487 (if GDAL found)
  docs/georef/1836.md                       written by hand, not by this script
"""

import csv
import math
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import geocode_1860 as g  # noqa: E402  (sys.path must be set up first)

MAPS = ROOT / "data" / "raw" / "maps"
WORK = ROOT / "data" / "work" / "maps"
WORK.mkdir(parents=True, exist_ok=True)

LOC_ITEM = "https://www.loc.gov/item/2002624026/"
LOC_JP2 = ("https://tile.loc.gov/storage-services/service/gmd/gmd384/"
           "g3844/g3844b/wd000016.jp2")
ACCESSED = "2026-08-08"

# The full-resolution scan.  BALT_1836_JP2 lets a caller point at a copy that
# lives outside the repo (this script's own first run did exactly that).
SRC = Path(os.environ.get("BALT_1836_JP2", MAPS / "baltimore_1836_plan.jp2"))
FULL_SIZE = (6923, 5374)
CRS_EPSG = 6487


def ensure_source():
    """Download the LOC master JP2 if it is not already on disk."""
    if SRC.exists():
        return SRC
    SRC.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {LOC_JP2} -> {SRC}")
    req = urllib.request.Request(LOC_JP2, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(SRC, "wb") as f:
        shutil.copyfileobj(r, f)
    return SRC


# ---------------------------------------------------------------------------
# Ground control points.
#
# (name, street_a_key, street_b_key, pixel_x, pixel_y, region, note)
#
# A key is a plain normalised street name, or (name, direction) where HUE
# records the halves of a split street separately and the undirected merge has
# a gap.  Pixel coordinates are on the FULL-RESOLUTION 6923 x 5374 JP2.
#
# `region` is used only for the residual-by-region report.  `note` records how
# the point was identified when the street name was not printed at the crossing
# itself; an empty note means both street names were legible right there.
# ---------------------------------------------------------------------------
GCPS = [
    # --- far north / north-east, the platted-but-not-yet-built grid ---------
    ("Broadway & Lanvale",   ("BROADWAY", "N"),   ("LANVALE", "E"),   4474,  537, "NE",
     "Broadway is the sheet's 'North MARKET STREET'; both names printed"),
    ("Wolfe & Lanvale",      ("WOLFE", "N"),      ("LANVALE", "E"),   4713,  537, "NE", ""),
    ("Chester & Federal",    ("CHESTER", "N"),    ("FEDERAL", "E"),   4901,  624, "NE", ""),

    # --- north-central, Charles Street corridor ----------------------------
    ("Charles & Biddle",     ("CHARLES", "N"),    ("BIDDLE", "W"),    3069,  979, "N", ""),
    ("St Paul & Biddle",     "SAINT PAUL",        ("BIDDLE", "E"),    3157,  979, "N",
     "St Paul name read one block south, on the same straight run"),
    ("Charles & Chase",      ("CHARLES", "N"),    ("CHASE", "W"),     3069, 1069, "N", ""),
    ("Charles & Eager",      ("CHARLES", "N"),    ("EAGER", "W"),     3069, 1176, "N", ""),
    ("Charles & Madison",    ("CHARLES", "N"),    ("MADISON", "W"),   3067, 1385, "N", ""),
    ("Broadway & Madison",   ("BROADWAY", "N"),   ("MADISON", "E"),   4472, 1380, "NE", ""),
    ("Broadway & Monument",  ("BROADWAY", "N"),   ("MONUMENT", "E"),  4472, 1472, "NE", ""),

    # --- north-west, the platted grid above Franklin Square ----------------
    ("Fulton & Mosher",      ("FULTON", "N"),     "MOSHER",           1088, 1204, "NW", ""),
    ("Gilmor & Mosher",      ("GILMOR", "N"),     "MOSHER",           1278, 1204, "NW", ""),
    ("Carey & Mosher",       ("CAREY", "N"),      "MOSHER",           1530, 1204, "NW", ""),
    ("Fulton & Lanvale",     ("FULTON", "N"),     ("LANVALE", "W"),   1088, 1394, "NW", ""),
    ("Gilmor & Lanvale",     ("GILMOR", "N"),     ("LANVALE", "W"),   1278, 1394, "NW", ""),
    ("Carey & Lanvale",      ("CAREY", "N"),      ("LANVALE", "W"),   1530, 1394, "NW", ""),

    # --- west, along Baltimore Street --------------------------------------
    ("Fulton & Baltimore",   "FULTON",            "BALTIMORE",        1083, 2175, "W",
     "cross street identified by tracing the labelled, dead-straight Fulton St "
     "down from the NW grid; the block gap is visible at this x"),
    ("Mount & Baltimore",    "MOUNT",             "BALTIMORE",        1186, 2175, "W",
     "same tracing method as Fulton & Baltimore"),
    ("Gilmor & Baltimore",   "GILMOR",            "BALTIMORE",        1276, 2175, "W",
     "same tracing method as Fulton & Baltimore"),
    ("Carey & Baltimore",    "CAREY",             "BALTIMORE",        1527, 2175, "W",
     "same tracing method as Fulton & Baltimore"),

    # --- downtown core ------------------------------------------------------
    ("Eutaw & Baltimore",    "EUTAW",             "BALTIMORE",        2669, 2169, "C", ""),
    ("Charles & Baltimore",  "CHARLES",           "BALTIMORE",        3060, 2164, "C", ""),
    ("Gay & Baltimore",      ("GAY", "S"),        "BALTIMORE",        3446, 2166, "C", ""),
    ("Light & Pratt",        "LIGHT",             ("PRATT", "E"),     3133, 2424, "C", ""),
    ("Gay & Pratt",          ("GAY", "S"),        ("PRATT", "E"),     3446, 2422, "C", ""),

    # --- east, Old Town and Fells Point ------------------------------------
    ("Broadway & Baltimore", ("BROADWAY", "S"),   ("BALTIMORE", "E"), 4465, 2059, "E", ""),
    ("Chester & Baltimore",  ("CHESTER", "S"),    ("BALTIMORE", "E"), 4879, 2058, "E", ""),
    ("Broadway & Pratt",     ("BROADWAY", "S"),   ("PRATT", "E"),     4468, 2232, "E", ""),
    ("Wolfe & Pratt",        ("WOLFE", "S"),      ("PRATT", "E"),     4698, 2232, "E", ""),
    ("Washington & Pratt",   ("WASHINGTON", "S"), ("PRATT", "E"),     4779, 2232, "E", ""),
    ("Wolfe & Bank",         ("WOLFE", "S"),      "BANK",             4692, 2467, "E", ""),
    ("Ann & Aliceanna",      ("ANN", "S"),        "ALICEANNA",        4616, 2716, "E", ""),
    ("Bond & Aliceanna",     ("BOND", "S"),       "ALICEANNA",        4336, 2716, "E", ""),

    # --- south, Federal Hill and South Baltimore ---------------------------
    ("Charles & York",       "CHARLES",           ("YORK", "E"),      3040, 2853, "S", ""),
    ("Light & Hughes",       "LIGHT",             ("HUGHES", "E"),    3158, 2939, "S",
     "sheet prints this as 'Great Hughes'"),
    ("Light & Montgomery",   "LIGHT",             ("MONTGOMERY", "E"), 3159, 2994, "S",
     "sheet prints this as 'Great Montgomery'"),
    ("William & Montgomery", "WILLIAM",           ("MONTGOMERY", "E"), 3261, 2994, "S", ""),
    ("Hanover & Hamburg",    "HANOVER",           ("HAMBURG", "W"),   2962, 3163, "S", ""),
    ("Hanover & Cross",      "HANOVER",           ("CROSS", "W"),     2962, 3257, "S", ""),
    ("Charles & Cross",      "CHARLES",           ("CROSS", "E"),     3043, 3257, "S", ""),
    ("Light & Cross",        "LIGHT",             ("CROSS", "E"),     3172, 3257, "S", ""),
    ("Light & West",         "LIGHT",             ("WEST", "E"),      3172, 3347, "S", ""),
]

# Points that were located on the map and then NOT used, with the reason.
DROPPED = [
    ("Charles & Monument (Mount Vernon Place)",
     "Located on the sheet at approx. px (3067, 1477). Dropped because HUE has "
     "a real gap in CHARLES through the Washington Monument plaza and the two "
     "lines do not intersect. The same gap defeated the 1851 pass; see "
     "docs/GEOREFERENCE.md."),
    ("Calvert & Baltimore",
     "Calvert's name is printed at px x=3234 near y=1600, not at Baltimore St. "
     "Carrying it 570 px south to the Baltimore St crossing would be an "
     "inference, not a reading, and downtown is already the best-covered part "
     "of the sheet, so it was left out rather than guessed."),
    ("Ann & Oliver",
     "Both streets are printed on the sheet, but HUE's ANN (N) and OLIVER (E) "
     "do not intersect inside the 1846-1860 city boundary, so there is no "
     "reference coordinate to fit against."),
    ("Charles & Read, Charles & Centre",
     "Same failure mode as Charles & Monument: the reference geometry does not "
     "cross where the map does."),
]

# Points read along the drawn centre of the Jones Falls channel, for the
# displacement analysis.  These are NOT control points and take no part in any
# fit.  Read at 6x zoom on crop (3330, 1350)-(3560, 1550).
FALLS_PX = [(3378, 1375), (3387, 1425), (3406, 1475), (3421, 1525)]


# ---------------------------------------------------------------------------
# Reference geometry
# ---------------------------------------------------------------------------

def build_gcp_table():
    """Resolve every GCP's street pair to an EPSG:6487 coordinate."""
    g.ALIASES = g.load_aliases()
    streets = g.load_streets()

    rows = []
    for name, a_key, b_key, px, py, region, note in GCPS:
        ga, gb = streets.get(a_key), streets.get(b_key)
        if ga is None or gb is None:
            raise KeyError(f"{name}: no geometry for "
                           f"{a_key if ga is None else b_key!r}")
        inter = ga.intersection(gb)
        pts = ([inter] if inter.geom_type == "Point" else
               [p for p in getattr(inter, "geoms", []) if p.geom_type == "Point"])
        if len(pts) != 1:
            # Every pair here was pre-checked to give exactly one crossing, so
            # this branch firing means the reference geometry moved under us.
            raise ValueError(f"{name}: expected 1 crossing, got {len(pts)}")
        rows.append({
            "name": name, "region": region, "note": note,
            "street_a": a_key if isinstance(a_key, str) else f"{a_key[0]} ({a_key[1]})",
            "street_b": b_key if isinstance(b_key, str) else f"{b_key[0]} ({b_key[1]})",
            "pixel_x": float(px), "pixel_y": float(py),
            "world_x": pts[0].x, "world_y": pts[0].y,
        })
    return rows, streets


# ---------------------------------------------------------------------------
# Transforms.  All map pixel (x, y) -> world (easting, northing) in metres.
# ---------------------------------------------------------------------------

def design(P, order):
    """Polynomial design matrix. order 1 = affine (3 terms), 2 = quadratic (6)."""
    x, y = P[:, 0], P[:, 1]
    if order == 1:
        return np.column_stack([np.ones_like(x), x, y])
    return np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])


def fit_poly(P, W, order):
    c, *_ = np.linalg.lstsq(design(P, order), W, rcond=None)
    return c


def pred_poly(c, P, order):
    return design(P, order) @ c


def _tps_kernel(D):
    """U(r) = r^2 log r, with U(0) = 0."""
    return np.where(D > 0, D * D * np.log(np.where(D > 0, D, 1.0)), 0.0)


def fit_tps(P, W):
    """Exact-interpolating thin plate spline. Returns (coefficients, centres)."""
    n = len(P)
    K = _tps_kernel(np.linalg.norm(P[:, None, :] - P[None, :, :], axis=2))
    Pm = np.column_stack([np.ones(n), P])
    L = np.zeros((n + 3, n + 3))
    L[:n, :n], L[:n, n:], L[n:, :n] = K, Pm, Pm.T
    Y = np.vstack([W, np.zeros((3, 2))])
    return np.linalg.solve(L, Y), P


def pred_tps(model, Q):
    sol, C = model
    n = len(C)
    K = _tps_kernel(np.linalg.norm(Q[:, None, :] - C[None, :, :], axis=2))
    return K @ sol[:n] + np.column_stack([np.ones(len(Q)), Q]) @ sol[n:]


def dist(a, b):
    return np.linalg.norm(a - b, axis=1)


def loocv(P, W):
    """Leave-one-out cross validated error, in metres, for all three fits.

    This is the honest accuracy estimate. Fit RMSE is optimistically biased
    because the same points set the coefficients and then grade them; for the
    TPS it is exactly zero and means nothing at all."""
    n = len(P)
    out = {1: np.zeros(n), 2: np.zeros(n), "tps": np.zeros(n)}
    for i in range(n):
        keep = np.array([j for j in range(n) if j != i])
        for order in (1, 2):
            c = fit_poly(P[keep], W[keep], order)
            out[order][i] = np.linalg.norm(pred_poly(c, P[i:i + 1], order)[0] - W[i])
        m = fit_tps(P[keep], W[keep])
        out["tps"][i] = np.linalg.norm(pred_tps(m, P[i:i + 1])[0] - W[i])
    return out


def rmse(v):
    return float(np.sqrt(np.mean(np.asarray(v, float) ** 2)))


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

def write_csv(rows, fit, loo, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "name", "region", "street_a", "street_b",
            "pixel_x", "pixel_y", "world_x_epsg6487", "world_y_epsg6487",
            "residual_m_affine", "residual_m_poly2", "residual_m_tps",
            "loo_error_m_affine", "loo_error_m_poly2", "loo_error_m_tps",
            "note",
        ])
        for i, r in enumerate(rows):
            w.writerow([
                r["name"], r["region"], r["street_a"], r["street_b"],
                f"{r['pixel_x']:.0f}", f"{r['pixel_y']:.0f}",
                f"{r['world_x']:.2f}", f"{r['world_y']:.2f}",
                f"{fit[1][i]:.1f}", f"{fit[2][i]:.1f}", f"{fit['tps'][i]:.1f}",
                f"{loo[1][i]:.1f}", f"{loo[2][i]:.1f}", f"{loo['tps'][i]:.1f}",
                r["note"],
            ])


def write_points_file(rows, path):
    """QGIS Georeferencer .points format (pixelY negative, per QGIS convention)."""
    with open(path, "w") as f:
        f.write(f"#CRS: EPSG:{CRS_EPSG}\n")
        f.write("mapX,mapY,pixelX,pixelY,enable\n")
        for r in rows:
            f.write(f"{r['world_x']:.3f},{r['world_y']:.3f},"
                    f"{r['pixel_x']:.3f},{-r['pixel_y']:.3f},1\n")


def find_gdal():
    """gdal_translate / gdalwarp, preferring the QGIS bundle (scripts/qgis_env.sh)."""
    env = os.environ.copy()
    if shutil.which("gdal_translate") and shutil.which("gdalwarp"):
        return "gdal_translate", "gdalwarp", env
    qgis = Path("/Applications/QGIS-final-4_2_1.app/Contents")
    translate, warp = qgis / "MacOS" / "gdal_translate", qgis / "MacOS" / "gdalwarp"
    if translate.exists() and warp.exists():
        env["PATH"] = str(qgis / "MacOS") + os.pathsep + env.get("PATH", "")
        env["GDAL_DATA"] = str(qgis / "Resources" / "qgis" / "gdal")
        env["PROJ_LIB"] = str(qgis / "Resources" / "qgis" / "proj")
        return str(translate), str(warp), env
    return None, None, env


def build_geotiff(rows, order, out_path, src):
    translate, warp, env = find_gdal()
    if translate is None:
        print("GDAL not found. GCP table, .points file and coefficients are "
              "still written; run gdalwarp later with the .points file.")
        return None
    gcp_args = []
    for r in rows:
        gcp_args += ["-gcp", f"{r['pixel_x']:.3f}", f"{r['pixel_y']:.3f}",
                     f"{r['world_x']:.3f}", f"{r['world_y']:.3f}"]
    tmp = WORK / "_tmp_1836_gcp.tif"
    subprocess.run([translate, "-of", "GTiff", "-a_srs", f"EPSG:{CRS_EPSG}",
                    *gcp_args, str(src), str(tmp)], env=env, check=True)
    subprocess.run([warp, "-r", "cubic", "-order", str(order),
                    "-t_srs", f"EPSG:{CRS_EPSG}",
                    "-co", "COMPRESS=JPEG", "-co", "TILED=YES",
                    "-co", "PHOTOMETRIC=YCBCR", "-co", "JPEG_QUALITY=85",
                    "-overwrite", str(tmp), str(out_path)], env=env, check=True)
    tmp.unlink(missing_ok=True)
    for aux in WORK.glob("_tmp_1836_gcp.tif.*"):
        aux.unlink(missing_ok=True)
    return out_path


# ---------------------------------------------------------------------------
# Displacement analysis: where does 1836 disagree with c.1930, and by how much
# ---------------------------------------------------------------------------

def displacement_report(rows, coeff_affine, streets):
    """Residual vectors by region, plus the Jones Falls corridor check."""
    P = np.array([[r["pixel_x"], r["pixel_y"]] for r in rows])
    W = np.array([[r["world_x"], r["world_y"]] for r in rows])
    pred = pred_poly(coeff_affine, P, 1)
    vec = pred - W                     # 1836-implied position minus HUE position

    print("\nResidual vectors by region, after the global affine")
    print("(positive dE = the 1836 sheet puts the corner EAST of where HUE does)")
    print(f"{'region':<8}{'n':>3}{'mean dE':>10}{'mean dN':>10}{'mean |r|':>10}{'max |r|':>10}")
    order = ["NW", "N", "NE", "W", "C", "E", "S"]
    for reg in order:
        idx = [i for i, r in enumerate(rows) if r["region"] == reg]
        if not idx:
            continue
        v = vec[idx]
        mags = np.linalg.norm(v, axis=1)
        print(f"{reg:<8}{len(idx):>3}{v[:, 0].mean():>10.1f}{v[:, 1].mean():>10.1f}"
              f"{mags.mean():>10.1f}{mags.max():>10.1f}")

    # Jones Falls: the channel the map draws, versus what sits in that corridor
    # now. The Falls was culverted in the 1910s and the Fallsway was built on
    # top of it, so the Fallsway centreline is the right modern proxy for the
    # old channel. HUE's FRONT is reported for continuity with the 1851 pass,
    # but note its digitised segments are short and truncated, so the figure
    # below is a distance to the nearest END of Front St as often as it is a
    # perpendicular offset. Read it as an order of magnitude, not a measurement.
    from shapely.geometry import Point
    fp = np.array(FALLS_PX, float)
    fw = pred_poly(coeff_affine, fp, 1)
    print("\nJones Falls corridor (map-drawn channel centre -> EPSG:6487, affine)")
    for (px, py), (wx, wy) in zip(FALLS_PX, fw):
        line = f"  px ({px}, {py}) -> ({wx:.0f}, {wy:.0f})"
        for key, label in (("FALLSWAY", "Fallsway"),
                           ("HOLLIDAY", "Holliday St"),
                           (("FRONT", "N"), "Front St (N)")):
            geom = streets.get(key)
            if geom is not None:
                line += f" | {label} {geom.distance(Point(wx, wy)):.0f} m"
        print(line)
    front = streets.get(("FRONT", "N"))
    if front is not None:
        b = [round(v) for v in front.bounds]
        print(f"  HUE Front St (N) bounds: x {b[0]}-{b[2]}, y {b[1]}-{b[3]}")


def main():
    src = ensure_source()
    rows, streets = build_gcp_table()
    P = np.array([[r["pixel_x"], r["pixel_y"]] for r in rows])
    W = np.array([[r["world_x"], r["world_y"]] for r in rows])

    c1, c2 = fit_poly(P, W, 1), fit_poly(P, W, 2)
    tps = fit_tps(P, W)
    fit = {1: dist(pred_poly(c1, P, 1), W),
           2: dist(pred_poly(c2, P, 2), W),
           "tps": dist(pred_tps(tps, P), W)}
    loo = loocv(P, W)

    print(f"Source: {src}  ({FULL_SIZE[0]}x{FULL_SIZE[1]} px)")
    print(f"{len(rows)} ground control points\n")
    print(f"{'transform':<22}{'fit RMSE':>10}{'LOO RMSE':>10}"
          f"{'LOO median':>12}{'LOO max':>10}")
    for key, label in ((1, "affine (order 1)"), (2, "polynomial (order 2)"),
                       ("tps", "thin plate spline")):
        print(f"{label:<22}{rmse(fit[key]):>10.1f}{rmse(loo[key]):>10.1f}"
              f"{np.median(loo[key]):>12.1f}{loo[key].max():>10.1f}")
    print("  TPS fit RMSE is 0 by construction (it interpolates its own control "
          "points).\n  Only the LOO column is an accuracy estimate.")

    scale = math.hypot(c1[1, 0], c1[1, 1])
    rot = math.degrees(math.atan2(c1[1, 1], c1[1, 0]))
    print(f"\naffine: {scale:.4f} m/px, rotation {rot:.3f} deg, "
          f"sheet {FULL_SIZE[0] * scale / 1000:.1f} x "
          f"{FULL_SIZE[1] * scale / 1000:.1f} km")

    print(f"\n{'point':<24}{'reg':>4}{'fit1':>8}{'fit2':>8}"
          f"{'LOO1':>8}{'LOO2':>8}{'LOOtps':>8}")
    for i, r in enumerate(rows):
        print(f"{r['name']:<24}{r['region']:>4}{fit[1][i]:>8.1f}{fit[2][i]:>8.1f}"
              f"{loo[1][i]:>8.1f}{loo[2][i]:>8.1f}{loo['tps'][i]:>8.1f}")

    displacement_report(rows, c1, streets)

    write_csv(rows, fit, loo, WORK / "gcps_1836.csv")
    write_points_file(rows, WORK / "baltimore_1836.points")
    print(f"\nWrote {WORK / 'gcps_1836.csv'}")
    print(f"Wrote {WORK / 'baltimore_1836.points'}")

    # Ship the first-order (affine) warp. Order 2 is a few metres better inside
    # the control hull but it bends the sheet's edges outside it, and the
    # Middle Branch, Whetstone Point and the far NW corner all lie outside the
    # hull. The affine degrades gracefully there. gcps_1836.csv carries all
    # three sets of numbers so this tradeoff stays checkable.
    out = build_geotiff(rows, 1, WORK / "baltimore_1836_georef.tif", src)
    if out and out.exists():
        mb = out.stat().st_size / 1e6
        print(f"GeoTIFF: {out} ({mb:.1f} MB, affine)")
        if mb > 90:
            print("WARNING: over the repo's 90 MB cap; downsample before committing.")


if __name__ == "__main__":
    main()
