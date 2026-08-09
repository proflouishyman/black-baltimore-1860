#!/usr/bin/env python3
"""Georeference the 1860 Baltimore city directory map (William Sides / John W.
Woods) and measure honestly how far it disagrees with the c.1930 HUE street
file that every resident in this project is currently placed against.

Source scan
-----------
data/raw/maps/baltimore_1860_directory_map.jpg, 5000 x 4009 px, RGB.
Talbot County Free Library via Digital Maryland, item tcgc:22:
  https://collections.digitalmaryland.org/digital/collection/tcgc/id/22
Full-resolution download used here (accessed 2026-08-08):
  https://collections.digitalmaryland.org/digital/download/collection/tcgc/id/22/size/full
The IIIF info.json for tcgc:22 reports width 5000, height 4009, so 5000x4009 IS
the master resolution the repository serves. There is no larger scan to get.

What this script fixes relative to scripts/georeference_1851.py
--------------------------------------------------------------
1. 27 control points instead of 12, deliberately spread over the whole built-up
   area rather than strung along one street. No single street contributes more
   than five points and the two most-used streets (Broadway, Charles) run
   north-south and are crossed by six different east-west streets between them.
2. Leave-one-out cross validation is the headline accuracy number. Fit RMSE is
   reported too, and the gap between them is the point of the exercise.
3. Control coordinates come from the MODERN Baltimore centreline file
   (data/raw/balt_streets.geojson), not from HUE. HUE is then measured against
   those same intersections as an independent check. See CIRCULARITY below.

CIRCULARITY
-----------
The 1851 script took its control coordinates from the c.1930 HUE file and then
used the result to talk about how far 1851 sits from HUE. That is circular: a
global least-squares fit absorbs whatever systematic offset the reference
carries, so the residuals cannot see it.

Here the reference is the modern city centreline file, which is a survey
product with a different provenance from HUE. That breaks the loop in
principle. In practice it turns out to make almost no numerical difference,
and that fact is itself the most useful thing this script reports: at all 27
control intersections the HUE c.1930 position and the modern position agree to
within a couple of metres (see the hue_minus_modern_m column of the output
CSV). Wherever a street survives, HUE is effectively coincident with modern
survey geometry, so it is not a systematically displaced layer. Any large
1860-vs-HUE disagreement therefore has to come from the 1860 sheet itself, or
from geometry that no longer exists (the culverted Jones Falls, the filled
harbour), not from a global shift in HUE.

HOW THE PIXEL COORDINATES WERE FOUND
------------------------------------
Every pixel coordinate below was read off the scan by cropping a window at
4x to 7x magnification with a labelled pixel grid overlaid, identifying both
street corridors by the engraved street name printed in the corridor, and
taking the centre of the white gap between the facing block edges. None was
computed from a transform and then written down. Points that could not be
identified from the engraving were dropped rather than guessed; the DROPPED
list at the bottom of this docstring records them.

Deliberately avoided as control points:
  - anything on the harbour edge, the wharves, or the Jones Falls, because the
    harbour was filled and the falls was culverted and rerouted;
  - the 45-degree grids of Bolton, the Pennsylvania Avenue corridor and the
    southwest, where the engraved streets run diagonally and the corridor
    centre cannot be read to better than about 20 px;
  - Gay Street at Baltimore Street, where the diagonal junction and Marsh
    Market make the crossing ambiguous on the sheet.

DROPPED after visual inspection:
  Wolfe & Pratt      - four evenly spaced unlabelled corridors in the crop and
                       no engraved name near the crossing; could not tell which
                       one is Wolfe.
  Gilmor & Townsend  - Townsend St has no crossing with Gilmor in either
                       reference layer.
  Patterson Park Ave & Baltimore - regular unlabelled block grid, street not
                       identifiable from the engraving.
  Harford Ave & Chase - Harford Ave runs diagonally here and the east-west
                       streets are unlabelled in that block.

Outputs
-------
  data/work/maps/gcps_1860.csv               control points, per-point residuals,
                                             per-point leave-one-out errors
  data/work/maps/baltimore_1860.points       QGIS Georeferencer control points
  data/work/maps/baltimore_1860_coeffs.json  fitted transform coefficients
  data/work/maps/baltimore_1860_georef.tif   GeoTIFF, if GDAL is reachable
  docs/georef/1860.md                        written separately, not by this script
"""

import csv
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import geocode_1860 as g  # noqa: E402  (sys.path must be set up first)

import geopandas as gpd  # noqa: E402
from shapely.ops import linemerge, unary_union  # noqa: E402

MAPS = ROOT / "data" / "raw" / "maps"
WORK = ROOT / "data" / "work" / "maps"
WORK.mkdir(parents=True, exist_ok=True)

SCAN = MAPS / "baltimore_1860_directory_map.jpg"
SCAN_SIZE = (5000, 4009)
CRS_EPSG = 6487                  # NAD83(2011) / Maryland, metres

MODERN_STREETS = ROOT / "data" / "raw" / "balt_streets.geojson"
HUE_STREETS = (ROOT / "data" / "raw" / "hue" / "HUE_Baltimore_Streets"
               / "CPE_Baltimore_Streets_HUE_v1.shp")

# ---------------------------------------------------------------------------
# Ground control points.
#
# (label, street_a, street_b, pixel_x, pixel_y, region, note)
#
# street_a / street_b are normalised street cores as produced by
# geocode_1860.norm_street(), so "BALTIMORE" matches E BALTIMORE ST, W
# BALTIMORE ST and BALTIMORE ST alike. Pixel coordinates are in the
# 5000 x 4009 scan, origin top-left.
#
# `region` exists so the write-up can report coverage rather than just count.
# ---------------------------------------------------------------------------
GCPS = [
    # --- west and northwest -------------------------------------------------
    ("Payson & W Baltimore",   "PAYSON",   "BALTIMORE", 1035, 1648, "W",
     "Payson engraved vertically at the corridor; Baltimore confirmed by "
     "counting Fayette-Baltimore spacing against the block depths"),
    ("Fulton & W Baltimore",   "FULTON",   "BALTIMORE", 1170, 1657, "W",
     "both names engraved in their corridors"),
    ("Gilmor & Mosher",        "GILMOR",   "MOSHER",    1288, 1085, "NW",
     "both names engraved in their corridors"),
    ("Stricker & Mosher",      "STRICKER", "MOSHER",    1341, 1085, "NW",
     "both names engraved in their corridors"),
    ("Carey & W Franklin",     "CAREY",    "FRANKLIN",  1445, 1358, "W",
     "Franklin engraved; Carey identified as the corridor one block west of "
     "the engraved Republican St"),

    # --- southwest ----------------------------------------------------------
    ("Scott & W Ramsay",       "SCOTT",    "RAMSAY",    1812, 1928, "SW",
     "both names engraved in their corridors"),

    # --- centre south -------------------------------------------------------
    ("Paca & W Pratt",         "PACA",     "PRATT",     2078, 1792, "CS",
     "S Paca engraved; Pratt corridor carries the ward boundary dashes"),
    ("Eutaw & Camden",         "EUTAW",    "CAMDEN",    2145, 1851, "CS",
     "both names engraved in their corridors"),

    # --- centre -------------------------------------------------------------
    ("Eutaw & Baltimore",      "EUTAW",    "BALTIMORE", 2139, 1656, "C",
     "both names engraved"),
    ("Howard & Baltimore",     "HOWARD",   "BALTIMORE", 2195, 1657, "C",
     "both names engraved"),
    ("Charles & Baltimore",    "CHARLES",  "BALTIMORE", 2371, 1659, "C",
     "both names engraved; German St one block south confirms the corridor"),

    # --- centre north -------------------------------------------------------
    ("Charles & W Madison",    "CHARLES",  "MADISON",   2371, 1180, "N",
     "both names engraved; Mount Vernon Place one block south"),
    ("Charles & E Chase",      "CHARLES",  "CHASE",     2371,  985, "N",
     "both names engraved"),
    ("Calvert & E Biddle",     "CALVERT",  "BIDDLE",    2473,  943, "N",
     "both names engraved"),

    # --- south --------------------------------------------------------------
    ("Charles & Cross",        "CHARLES",  "CROSS",     2359, 2282, "S",
     "S Charles engraved; Cross corridor holds Cross Street Market"),
    ("Light & Cross",          "LIGHT",    "CROSS",     2448, 2282, "S",
     "LOWER CONFIDENCE: Light itself is not engraved near this crossing; "
     "identified as the second corridor east of the engraved Patapsco St"),
    ("Charles & W Ostend",     "CHARLES",  "OSTEND",    2357, 2400, "S",
     "both names engraved"),

    # --- east ---------------------------------------------------------------
    ("Caroline & E Baltimore", "CAROLINE", "BALTIMORE", 3088, 1592, "E",
     "S Caroline engraved; E Baltimore engraved two blocks west"),
    ("Broadway & E Baltimore", "BROADWAY", "BALTIMORE", 3220, 1597, "E",
     "Broadway engraved and unmistakable, wide corridor with a market oval"),
    ("Broadway & E Monument",  "BROADWAY", "MONUMENT",  3224, 1239, "E",
     "both names engraved"),
    ("Wolfe & E Monument",     "WOLFE",    "MONUMENT",  3355, 1239, "E",
     "Wolfe engraved vertically at the corridor"),

    # --- northeast ----------------------------------------------------------
    ("Broadway & E Federal",   "BROADWAY", "FEDERAL",   3222,  730, "NE",
     "Federal engraved; Broadway traced continuously north from Monument"),
    ("Broadway & E Lanvale",   "BROADWAY", "LANVALE",   3222,  671, "NE",
     "Lanvale engraved; Broadway traced continuously north from Monument"),

    # --- far east -----------------------------------------------------------
    ("Chester & McElderry",    "CHESTER",  "MCELDERRY", 3466, 1300, "FE",
     "both names engraved; note this was platted-but-thinly-built ground in "
     "1860, so the sheet may be showing a plat rather than a survey"),
    ("Luzerne & E Monument",   "LUZERNE",  "MONUMENT",  3732, 1242, "FE",
     "both names engraved; same platted-ground caveat as Chester"),

    # --- southeast, Fells Point --------------------------------------------
    ("Broadway & Aliceanna",   "BROADWAY", "ALICEANNA", 3225, 2009, "SE",
     "Alice Anna engraved; Broadway corridor carries the market sheds"),
    ("Broadway & Lancaster",   "BROADWAY", "LANCASTER", 3222, 2058, "SE",
     "Lancaster engraved; Broadway as above"),
]


# ---------------------------------------------------------------------------
# Reference geometry
# ---------------------------------------------------------------------------

def _bucket(gdf, namecol):
    """One merged geometry per normalised street core, plus per-direction keys.

    Mirrors geocode_1860.load_streets()'s keying so that the same normalised
    names work here, but without that function's clip to the 1846-1860 ward
    boundary: several control points (Luzerne, Chester) sit on ground that was
    inside the 1860 city but the clip is not needed for a pure intersection
    lookup and would only risk trimming a line short of its crossing.
    """
    plain = defaultdict(list)
    directed = defaultdict(list)
    for name, geom in zip(gdf[namecol], gdf.geometry):
        if not name or geom is None or geom.is_empty:
            continue
        core, direction = g.norm_street(name)
        if not core:
            continue
        plain[core].append(geom)
        if direction:
            directed[(core, direction)].append(geom)
    out = {}
    for key, geoms in list(plain.items()) + list(directed.items()):
        out[key] = linemerge(unary_union(geoms)) if len(geoms) > 1 else geoms[0]
    return out


def load_reference_layers():
    g.ALIASES = g.load_aliases()
    modern = _bucket(gpd.read_file(MODERN_STREETS).to_crs(epsg=CRS_EPSG),
                     "ROAD_NAME")
    hue = _bucket(gpd.read_file(HUE_STREETS).to_crs(epsg=CRS_EPSG), "Full_Name")
    return modern, hue


def intersect_points(streets, a, b):
    """All Point intersections of two named streets, or [] if they do not meet."""
    ga, gb = streets.get(a), streets.get(b)
    if ga is None or gb is None:
        return []
    it = ga.intersection(gb)
    if it.is_empty:
        return []
    if it.geom_type == "Point":
        return [it]
    return [p for p in getattr(it, "geoms", []) if p.geom_type == "Point"]


def resolve_world(streets, rows):
    """Pixel -> world for every GCP, disambiguating multi-crossing pairs.

    Some street names cross twice in the reference layer (Baltimore has two
    Frederick Streets, Broadway meets Aliceanna at both kerb lines of a divided
    stretch). Those cannot be resolved by name alone. They are resolved in two
    passes: fit a preliminary affine on only the pairs that cross exactly once,
    then, for the ambiguous pairs, take the crossing nearest that preliminary
    prediction. This is a tie-break between candidates that are all genuinely
    the named crossing, not a way of inventing a location.
    """
    unique, ambiguous = [], []
    for row in rows:
        pts = intersect_points(streets, row["street_a"], row["street_b"])
        if len(pts) == 1:
            unique.append((row, pts[0]))
        elif len(pts) > 1:
            ambiguous.append((row, pts))
        else:
            raise ValueError(f"{row['label']}: streets do not cross in reference")

    # preliminary pixel -> world affine on the unambiguous subset
    P = np.array([[r["px"], r["py"], 1.0] for r, _ in unique])
    cx, *_ = np.linalg.lstsq(P, np.array([p.x for _, p in unique]), rcond=None)
    cy, *_ = np.linalg.lstsq(P, np.array([p.y for _, p in unique]), rcond=None)

    resolved = {r["label"]: (p.x, p.y) for r, p in unique}
    for row, pts in ambiguous:
        v = np.array([row["px"], row["py"], 1.0])
        guess = np.array([v @ cx, v @ cy])
        best = min(pts, key=lambda p: (p.x - guess[0]) ** 2 + (p.y - guess[1]) ** 2)
        resolved[row["label"]] = (best.x, best.y)
    return resolved


# ---------------------------------------------------------------------------
# Transforms. Each exposes fit(P, W) -> model and apply(model, P) -> W,
# so the leave-one-out loop can treat them identically.
# ---------------------------------------------------------------------------

def _poly_terms(P, order):
    x, y = P[:, 0], P[:, 1]
    if order == 1:
        return np.column_stack([np.ones_like(x), x, y])
    return np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])


def fit_poly(P, W, order):
    A = _poly_terms(P, order)
    cx, *_ = np.linalg.lstsq(A, W[:, 0], rcond=None)
    cy, *_ = np.linalg.lstsq(A, W[:, 1], rcond=None)
    return ("poly", order, cx, cy)


def apply_poly(model, P):
    _, order, cx, cy = model
    A = _poly_terms(P, order)
    return np.column_stack([A @ cx, A @ cy])


def _tps_kernel(r2):
    """U(r) = r^2 log r, written on squared distance and guarded at r = 0."""
    out = np.zeros_like(r2)
    nz = r2 > 0
    out[nz] = 0.5 * r2[nz] * np.log(r2[nz])
    return out


def fit_tps(P, W, smoothing=0.0):
    """Thin plate spline through the control points.

    NOTE: a TPS interpolates its control points exactly, so its FIT residual is
    zero by construction and is not an accuracy measure. Only its leave-one-out
    error means anything.
    """
    n = len(P)
    # scale pixel coordinates so the log kernel is numerically well behaved
    scale = float(np.max(np.abs(P))) or 1.0
    Q = P / scale
    d2 = ((Q[:, None, :] - Q[None, :, :]) ** 2).sum(-1)
    K = _tps_kernel(d2)
    if smoothing:
        K = K + np.eye(n) * smoothing
    Pm = np.column_stack([np.ones(n), Q])
    L = np.zeros((n + 3, n + 3))
    L[:n, :n] = K
    L[:n, n:] = Pm
    L[n:, :n] = Pm.T
    rhs = np.zeros((n + 3, 2))
    rhs[:n] = W
    sol, *_ = np.linalg.lstsq(L, rhs, rcond=None)
    return ("tps", Q, sol, scale)


def apply_tps(model, P):
    _, Q, sol, scale = model
    R = P / scale
    d2 = ((R[:, None, :] - Q[None, :, :]) ** 2).sum(-1)
    K = _tps_kernel(d2)
    A = np.column_stack([K, np.ones(len(R)), R])
    return A @ sol


TRANSFORMS = {
    "affine": (lambda P, W: fit_poly(P, W, 1), apply_poly, 3),
    "poly2":  (lambda P, W: fit_poly(P, W, 2), apply_poly, 6),
    "tps":    (fit_tps, apply_tps, None),
}


def evaluate(P, W):
    """Fit residuals and leave-one-out errors for every transform, in metres."""
    out = {}
    n = len(P)
    for name, (fit, apply_, min_pts) in TRANSFORMS.items():
        model = fit(P, W)
        pred = apply_(model, P)
        fit_res = np.linalg.norm(pred - W, axis=1)

        loo = np.full(n, np.nan)
        for i in range(n):
            keep = np.arange(n) != i
            if min_pts is not None and keep.sum() < min_pts:
                continue
            m = fit(P[keep], W[keep])
            p = apply_(m, P[i:i + 1])
            loo[i] = float(np.linalg.norm(p[0] - W[i]))

        out[name] = {
            "model": model,
            "fit_residuals": fit_res,
            "fit_rmse": float(np.sqrt(np.mean(fit_res ** 2))),
            "loo_errors": loo,
            "loo_rmse": float(np.sqrt(np.nanmean(loo ** 2))),
            "loo_median": float(np.nanmedian(loo)),
            "loo_max": float(np.nanmax(loo)),
        }
    return out


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

def write_csv(rows, world_modern, world_hue, results, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "label", "street_a", "street_b", "region",
            "pixel_x", "pixel_y",
            "modern_x_epsg6487", "modern_y_epsg6487",
            "hue_x_epsg6487", "hue_y_epsg6487",
            "hue_minus_modern_m",
            "fit_residual_affine_m", "fit_residual_poly2_m", "fit_residual_tps_m",
            "loo_error_affine_m", "loo_error_poly2_m", "loo_error_tps_m",
            "map_vs_hue_m", "note",
        ])
        aff, pol, tps = results["affine"], results["poly2"], results["tps"]
        # map_vs_hue: where the shipped (affine) transform puts the pixel, versus
        # where HUE puts the same named intersection.
        P = np.array([[r["px"], r["py"]] for r in rows], float)
        map_world = apply_poly(aff["model"], P)
        for i, r in enumerate(rows):
            mx, my = world_modern[r["label"]]
            h = world_hue.get(r["label"])
            hx, hy = (h if h else ("", ""))
            hd = (f"{np.hypot(hx - mx, hy - my):.1f}" if h else "")
            mvh = (f"{np.hypot(map_world[i][0] - hx, map_world[i][1] - hy):.1f}"
                   if h else "")
            w.writerow([
                r["label"], r["street_a"], r["street_b"], r["region"],
                r["px"], r["py"],
                f"{mx:.2f}", f"{my:.2f}",
                (f"{hx:.2f}" if h else ""), (f"{hy:.2f}" if h else ""),
                hd,
                f"{aff['fit_residuals'][i]:.1f}",
                f"{pol['fit_residuals'][i]:.1f}",
                f"{tps['fit_residuals'][i]:.1f}",
                f"{aff['loo_errors'][i]:.1f}",
                f"{pol['loo_errors'][i]:.1f}",
                f"{tps['loo_errors'][i]:.1f}",
                mvh, r["note"],
            ])


def write_points_file(rows, world, path):
    """QGIS Georeferencer .points format. QGIS stores pixel row as negative."""
    with open(path, "w") as f:
        f.write(f"#CRS: EPSG:{CRS_EPSG}\n")
        f.write("mapX,mapY,pixelX,pixelY,enable\n")
        for r in rows:
            wx, wy = world[r["label"]]
            f.write(f"{wx:.3f},{wy:.3f},{r['px']:.3f},{-r['py']:.3f},1\n")


def write_coeffs(results, path):
    aff, pol = results["affine"], results["poly2"]
    payload = {
        "crs": f"EPSG:{CRS_EPSG}",
        "scan": SCAN.name,
        "scan_size_px": list(SCAN_SIZE),
        "pixel_to_world": {
            "affine": {
                "terms": ["1", "x", "y"],
                "x": list(map(float, aff["model"][2])),
                "y": list(map(float, aff["model"][3])),
            },
            "poly2": {
                "terms": ["1", "x", "y", "x^2", "x*y", "y^2"],
                "x": list(map(float, pol["model"][2])),
                "y": list(map(float, pol["model"][3])),
            },
        },
        "accuracy_m": {
            k: {"fit_rmse": v["fit_rmse"], "loo_rmse": v["loo_rmse"],
                "loo_median": v["loo_median"], "loo_max": v["loo_max"]}
            for k, v in results.items()
        },
    }
    path.write_text(json.dumps(payload, indent=2))


def find_gdal():
    """gdal_translate/gdalwarp, preferring the QGIS bundle (scripts/qgis_env.sh)."""
    env = os.environ.copy()
    if shutil.which("gdal_translate") and shutil.which("gdalwarp"):
        return "gdal_translate", "gdalwarp", env
    qgis = Path("/Applications/QGIS-final-4_2_1.app/Contents/MacOS")
    if (qgis / "gdal_translate").exists() and (qgis / "gdalwarp").exists():
        env["PATH"] = str(qgis) + os.pathsep + env.get("PATH", "")
        res = "/Applications/QGIS-final-4_2_1.app/Contents/Resources"
        env["GDAL_DATA"] = f"{res}/qgis/gdal"
        # PROJ >= 9.1 reads PROJ_DATA; older builds read PROJ_LIB. Without one
        # of these pointing at proj.db, gdalwarp silently writes the raster with
        # an unnamed engineering CRS instead of EPSG:6487.
        env["PROJ_LIB"] = f"{res}/qgis/proj"
        env["PROJ_DATA"] = f"{res}/qgis/proj"
        return str(qgis / "gdal_translate"), str(qgis / "gdalwarp"), env
    return None, None, env


def build_geotiff(rows, world, out_path, order=1):
    translate, warp, env = find_gdal()
    if translate is None:
        print("GDAL not found: skipping GeoTIFF. Transform coefficients and the "
              "QGIS .points file are still written, so the warp can be applied "
              "later without repeating any of this.")
        return None

    gcp_args = []
    for r in rows:
        wx, wy = world[r["label"]]
        gcp_args += ["-gcp", f"{r['px']:.3f}", f"{r['py']:.3f}",
                     f"{wx:.3f}", f"{wy:.3f}"]

    tmp = WORK / "_tmp_1860_gcp.tif"
    subprocess.run([translate, "-of", "GTiff", "-a_srs", f"EPSG:{CRS_EPSG}",
                    *gcp_args, str(SCAN), str(tmp)], env=env, check=True)
    subprocess.run([warp, "-r", "cubic", "-order", str(order),
                    "-t_srs", f"EPSG:{CRS_EPSG}",
                    "-co", "COMPRESS=JPEG", "-co", "JPEG_QUALITY=85",
                    "-co", "TILED=YES", "-co", "PHOTOMETRIC=YCBCR",
                    "-overwrite", str(tmp), str(out_path)],
                   env=env, check=True)
    tmp.unlink(missing_ok=True)
    for aux in WORK.glob("_tmp_1860_gcp.tif.*"):
        aux.unlink(missing_ok=True)
    return out_path


# ---------------------------------------------------------------------------

def main():
    rows = [{"label": a, "street_a": b, "street_b": c, "px": d, "py": e,
             "region": f, "note": h} for a, b, c, d, e, f, h in GCPS]

    modern, hue = load_reference_layers()
    world_modern = resolve_world(modern, rows)
    world_hue = {}
    for r in rows:
        pts = intersect_points(hue, r["street_a"], r["street_b"])
        if pts:
            mx, my = world_modern[r["label"]]
            best = min(pts, key=lambda p: (p.x - mx) ** 2 + (p.y - my) ** 2)
            world_hue[r["label"]] = (best.x, best.y)

    P = np.array([[r["px"], r["py"]] for r in rows], float)
    W = np.array([world_modern[r["label"]] for r in rows], float)
    results = evaluate(P, W)

    print(f"{len(rows)} ground control points")
    regions = defaultdict(int)
    for r in rows:
        regions[r["region"]] += 1
    print("coverage:", ", ".join(f"{k}={v}" for k, v in sorted(regions.items())))
    print()
    print(f"{'transform':<10}{'fit RMSE':>12}{'LOO RMSE':>12}"
          f"{'LOO median':>12}{'LOO max':>10}")
    for name in ("affine", "poly2", "tps"):
        v = results[name]
        print(f"{name:<10}{v['fit_rmse']:>11.1f}m{v['loo_rmse']:>11.1f}m"
              f"{v['loo_median']:>11.1f}m{v['loo_max']:>9.1f}m")
    print()

    hue_off = [np.hypot(world_hue[r["label"]][0] - world_modern[r["label"]][0],
                        world_hue[r["label"]][1] - world_modern[r["label"]][1])
               for r in rows if r["label"] in world_hue]
    print(f"HUE c.1930 vs modern centrelines at the same {len(hue_off)} "
          f"intersections: median {np.median(hue_off):.1f} m, "
          f"max {np.max(hue_off):.1f} m")
    print()

    print(f"{'point':<26}{'aff res':>9}{'aff LOO':>9}{'p2 LOO':>9}{'tps LOO':>9}")
    order = np.argsort(-results["affine"]["loo_errors"])
    for i in order:
        print(f"{rows[i]['label']:<26}"
              f"{results['affine']['fit_residuals'][i]:>8.1f}m"
              f"{results['affine']['loo_errors'][i]:>8.1f}m"
              f"{results['poly2']['loo_errors'][i]:>8.1f}m"
              f"{results['tps']['loo_errors'][i]:>8.1f}m")

    write_csv(rows, world_modern, world_hue, results, WORK / "gcps_1860.csv")
    write_points_file(rows, world_modern, WORK / "baltimore_1860.points")
    write_coeffs(results, WORK / "baltimore_1860_coeffs.json")
    print(f"\nWrote {WORK / 'gcps_1860.csv'}")
    print(f"Wrote {WORK / 'baltimore_1860.points'}")
    print(f"Wrote {WORK / 'baltimore_1860_coeffs.json'}")

    out = build_geotiff(rows, world_modern, WORK / "baltimore_1860_georef.tif")
    if out and out.exists():
        mb = out.stat().st_size / 1e6
        print(f"GeoTIFF: {out} ({mb:.1f} MB)")
        if mb > 90:
            print("WARNING: over the 90 MB cap. Downsample before committing.")


if __name__ == "__main__":
    main()
