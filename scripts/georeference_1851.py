#!/usr/bin/env python3
"""Georeference the 1851 Sidney & Neff Plan of Baltimore against period-consistent
street geometry, and quantify how far 1851 disagrees with the c.1930 HUE survey
that the rest of this project currently places residents against.

Method
------
1. A set of ground control points (GCPs) is defined below as pairs of named
   streets, plus the *pixel location on the map preview* where that
   intersection was visually located (see docs/GEOREFERENCE.md for how each
   one was found and the crop coordinates used).
2. Each pair's real-world coordinate is resolved the same way the rest of the
   project resolves intersections: by loading the HUE 1930 street centrelines
   (plus modern streets as a fallback) via scripts/geocode_1860.load_streets(),
   and intersecting the two named lines. This reuses the project's existing
   street-name normalisation (norm_street) and alias table
   (data/work/street_aliases.csv) rather than duplicating it.
3. Pixel coordinates are given in the *preview* image (3354x2661) because that
   is what is practical to visually inspect; they are scaled up to the
   full-resolution jp2 (13414x10643) before fitting.
4. A first-order (affine, 6 param) and second-order (12 param) polynomial are
   fit by least squares from pixel -> world (EPSG:6487, metres). RMSE is
   reported overall and per point, in metres.
5. If GDAL (via the QGIS bundle, see scripts/qgis_env.sh) is reachable, an
   actual georeferenced GeoTIFF is produced with gdal_translate + gdalwarp.
   Otherwise the GCP table and fit coefficients are written out so the
   transform can be applied later without repeating any of this.

Discipline: every GCP here was visually confirmed on the map image (see
docs/GEOREFERENCE.md for the crop this was read from). Two originally planned
points (Charles & Monument; Orleans & Front, at the Jones Falls) were DROPPED
rather than forced, because the reference street geometry has a genuine gap
at Mount Vernon Place and Front Street does not reach far enough east in the
HUE data to meet Orleans -- see docs/GEOREFERENCE.md for the honest accounting.

Output:
  data/work/maps/gcps_1851.csv          -- GCP table with per-point residuals
  data/work/maps/baltimore_1851.points  -- QGIS georeferencer format
  data/work/maps/baltimore_1851_georef.tif  -- GeoTIFF (if GDAL available and
                                                under the repo's 90MB commit cap)
  docs/GEOREFERENCE.md                  -- written separately, not by this script
"""

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import geocode_1860 as g  # noqa: E402  (path must be set up first)

MAPS = ROOT / "data" / "raw" / "maps"
WORK = ROOT / "data" / "work" / "maps"
WORK.mkdir(parents=True, exist_ok=True)

JP2 = MAPS / "baltimore_1851_plan.jp2"
PREVIEW = MAPS / "baltimore_1851_plan_preview.jpg"
FULL_SIZE = (13414, 10643)     # gdalinfo on the jp2
PREVIEW_SIZE = (3354, 2661)    # gdalinfo confirms this is an exact overview level
CRS_EPSG = 6487                # NAD83(2011) / Maryland, metres -- project standard

SCALE_X = FULL_SIZE[0] / PREVIEW_SIZE[0]
SCALE_Y = FULL_SIZE[1] / PREVIEW_SIZE[1]

# ---------------------------------------------------------------------------
# Ground control points.
#
# Each entry: (name, street_a_key, street_b_key, preview_px_x, preview_px_y)
# A "key" is either a plain normalised street name (matching a key in
# load_streets()'s output) or an (name, direction) tuple when the plain,
# undirected merge of that street has a gap and the directional half must be
# used instead (this happens where HUE recorded the street as separate N/S or
# E/W segments that a whole-street union does not bridge cleanly, e.g. across
# Baltimore St or Mount Vernon Place).
#
# Pixel coordinates are read off data/raw/maps/baltimore_1851_plan_preview.jpg
# by cropping the neighbourhood with scripts-local grid overlays (see
# docs/GEOREFERENCE.md for the exact crop box used for each one, so this is
# re-checkable against the source image).
# ---------------------------------------------------------------------------
GCPS = [
    ("Charles & Baltimore",   "CHARLES",              "BALTIMORE",            1678, 1100),
    ("Calvert & Baltimore",   "CALVERT",               "BALTIMORE",            1830, 1099),
    ("Eutaw & Baltimore",     "EUTAW",                 "BALTIMORE",            1503, 1100),
    ("Gay & Baltimore",       ("GAY", "S"),             "BALTIMORE",           1893, 1100),
    ("Broadway & Baltimore",  "BROADWAY",               "BALTIMORE",           2413, 1050),
    ("Charles & Biddle",      ("CHARLES", "N"),         ("BIDDLE", "W"),       1678, 498),
    ("Eutaw & Monument",      "EUTAW",                  ("MONUMENT", "W"),     1520, 740),
    ("Fremont & Baltimore",   "FREMONT",                "BALTIMORE",           1276, 1113),
    ("Poppleton & Baltimore", "POPPLETON",              "BALTIMORE",           1100, 1118),
    ("Charles & Cross",       "CHARLES",                "CROSS",              1680, 1660),
    ("Light & York",          "LIGHT",                  "YORK",                1758, 1456),
    ("Bond & Aliceanna",      "BOND",                   "ALICEANNA",           2370, 1400),
]

DROPPED = [
    ("Charles & Monument",
     "HUE's undirected CHARLES merge ends at y=180970 (m, EPSG:6487); MONUMENT's "
     "west half starts at y=181076. There is a real gap in the reference geometry "
     "at Mount Vernon Place (the plaza appears to interrupt the digitised centreline). "
     "Rather than guess the crossing, this GCP was dropped."),
    ("Orleans & Front (Jones Falls crossing)",
     "Visually located at approx preview px (1975,1048), but FRONT's digitised "
     "segments (bounds x=433658-433802 and x=434053-434119) do not reach ORLEANS' "
     "x-range (434241-436598) in the HUE data -- the crossing this map shows no "
     "longer has a matching reference geometry post-channelisation. Dropped rather "
     "than fabricated."),
]


def resolve_world_xy(key, streets):
    """Look up a street key (plain name or (name, direction)) to its geometry."""
    if isinstance(key, tuple):
        geom = streets.get(key)
        if geom is None:
            raise KeyError(f"no geometry for {key}")
        return geom
    geom = streets.get(key)
    if geom is None:
        raise KeyError(f"no geometry for {key!r}")
    return geom


def build_gcp_table():
    g.ALIASES = g.load_aliases()
    streets = g.load_streets()

    rows = []
    for name, a_key, b_key, px, py in GCPS:
        ga = resolve_world_xy(a_key, streets)
        gb = resolve_world_xy(b_key, streets)
        inter = ga.intersection(gb)
        if inter.geom_type != "Point":
            # Some pairs cross more than once (or the merge is a multi-line);
            # pick the nearest point candidate to the previous behaviour --
            # but every pair used here was pre-checked to yield a single Point,
            # so this branch existing is itself a signal something moved.
            pts = [p for p in getattr(inter, "geoms", []) if p.geom_type == "Point"]
            if not pts:
                raise ValueError(f"{name}: streets do not cross ({inter.geom_type})")
            inter = pts[0]
        full_px = px * SCALE_X
        full_py = py * SCALE_Y
        rows.append({
            "name": name,
            "street_a": a_key if isinstance(a_key, str) else f"{a_key[0]} ({a_key[1]})",
            "street_b": b_key if isinstance(b_key, str) else f"{b_key[0]} ({b_key[1]})",
            "preview_px": px, "preview_py": py,
            "pixel_x": full_px, "pixel_y": full_py,
            "world_x": inter.x, "world_y": inter.y,
        })
    return rows


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------

def fit_affine(rows):
    """First-order polynomial: [wx,wy] = A @ [px,py,1]. Returns coeffs + residuals."""
    P = np.array([[r["pixel_x"], r["pixel_y"], 1.0] for r in rows])
    Wx = np.array([r["world_x"] for r in rows])
    Wy = np.array([r["world_y"] for r in rows])
    cx, *_ = np.linalg.lstsq(P, Wx, rcond=None)
    cy, *_ = np.linalg.lstsq(P, Wy, rcond=None)
    pred_x = P @ cx
    pred_y = P @ cy
    res = np.sqrt((pred_x - Wx) ** 2 + (pred_y - Wy) ** 2)
    return {"order": 1, "cx": cx, "cy": cy, "residuals": res,
            "rmse": float(np.sqrt(np.mean(res ** 2)))}


def fit_poly2(rows):
    """Second-order polynomial: 6 terms per axis (1,x,y,x^2,xy,y^2)."""
    def terms(px, py):
        return [1.0, px, py, px * px, px * py, py * py]
    P = np.array([terms(r["pixel_x"], r["pixel_y"]) for r in rows])
    Wx = np.array([r["world_x"] for r in rows])
    Wy = np.array([r["world_y"] for r in rows])
    cx, *_ = np.linalg.lstsq(P, Wx, rcond=None)
    cy, *_ = np.linalg.lstsq(P, Wy, rcond=None)
    pred_x = P @ cx
    pred_y = P @ cy
    res = np.sqrt((pred_x - Wx) ** 2 + (pred_y - Wy) ** 2)
    return {"order": 2, "cx": cx, "cy": cy, "residuals": res,
            "rmse": float(np.sqrt(np.mean(res ** 2)))}


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

def write_csv(rows, fit1, fit2, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "street_a", "street_b", "preview_px", "preview_py",
                    "pixel_x_full", "pixel_y_full", "world_x_epsg6487",
                    "world_y_epsg6487", "residual_m_order1", "residual_m_order2"])
        for r, e1, e2 in zip(rows, fit1["residuals"], fit2["residuals"]):
            w.writerow([r["name"], r["street_a"], r["street_b"],
                        r["preview_px"], r["preview_py"],
                        f"{r['pixel_x']:.2f}", f"{r['pixel_y']:.2f}",
                        f"{r['world_x']:.2f}", f"{r['world_y']:.2f}",
                        f"{e1:.2f}", f"{e2:.2f}"])


def write_points_file(rows, path):
    """QGIS Georeferencer .points format (pixelY stored negative: GDAL raster
    convention is row-down, QGIS's on-disk format flips sign)."""
    with open(path, "w") as f:
        f.write(f"#CRS: EPSG:{CRS_EPSG}\n")
        f.write("mapX,mapY,pixelX,pixelY,enable\n")
        for r in rows:
            f.write(f"{r['world_x']:.3f},{r['world_y']:.3f},"
                    f"{r['pixel_x']:.3f},{-r['pixel_y']:.3f},1\n")


def find_gdal():
    """Locate gdal_translate/gdalwarp, preferring the QGIS bundle (scripts/qgis_env.sh)
    since this Mac has no system GDAL."""
    candidates_dir = "/Applications/QGIS-final-4_2_1.app/Contents/MacOS"
    env = os.environ.copy()
    if shutil.which("gdal_translate"):
        return "gdal_translate", "gdalwarp", env
    translate = Path(candidates_dir) / "gdal_translate"
    warp = Path(candidates_dir) / "gdalwarp"
    if translate.exists() and warp.exists():
        env["PATH"] = candidates_dir + os.pathsep + env.get("PATH", "")
        env["GDAL_DATA"] = "/Applications/QGIS-final-4_2_1.app/Contents/Resources/qgis/gdal"
        env["PROJ_LIB"] = "/Applications/QGIS-final-4_2_1.app/Contents/Resources/qgis/proj"
        return str(translate), str(warp), env
    return None, None, env


def build_geotiff(rows, order, out_path):
    """gdal_translate to attach GCPs, then gdalwarp to a real EPSG:6487 raster."""
    translate, warp, env = find_gdal()
    if translate is None:
        print("GDAL not found -- skipping GeoTIFF; GCP table + coefficients still written.")
        return None

    gcp_args = []
    for r in rows:
        gcp_args += ["-gcp", f"{r['pixel_x']:.3f}", f"{r['pixel_y']:.3f}",
                      f"{r['world_x']:.3f}", f"{r['world_y']:.3f}"]

    tmp_tif = WORK / "_tmp_gcp.tif"
    cmd1 = [translate, "-of", "GTiff", "-a_srs", f"EPSG:{CRS_EPSG}",
            *gcp_args, str(JP2), str(tmp_tif)]
    print("Running:", " ".join(cmd1[:6]), "... (%d GCPs)" % len(rows))
    subprocess.run(cmd1, env=env, check=True)

    cmd2 = [warp, "-r", "cubic", "-order", str(order),
            "-t_srs", f"EPSG:{CRS_EPSG}",
            "-co", "COMPRESS=JPEG", "-co", "TILED=YES", "-co", "PHOTOMETRIC=YCBCR",
            "-overwrite", str(tmp_tif), str(out_path)]
    print("Running:", " ".join(cmd2))
    subprocess.run(cmd2, env=env, check=True)
    tmp_tif.unlink(missing_ok=True)
    for aux in WORK.glob("_tmp_gcp.tif.*"):
        aux.unlink(missing_ok=True)
    return out_path


def main():
    rows = build_gcp_table()
    fit1 = fit_affine(rows)
    fit2 = fit_poly2(rows)

    print(f"{len(rows)} ground control points")
    print(f"order-1 (affine) RMSE: {fit1['rmse']:.2f} m")
    print(f"order-2 (poly)   RMSE: {fit2['rmse']:.2f} m")
    print()
    print(f"{'name':<26}{'res1(m)':>10}{'res2(m)':>10}")
    for r, e1, e2 in zip(rows, fit1["residuals"], fit2["residuals"]):
        print(f"{r['name']:<26}{e1:>10.1f}{e2:>10.1f}")

    write_csv(rows, fit1, fit2, WORK / "gcps_1851.csv")
    write_points_file(rows, WORK / "baltimore_1851.points")
    print(f"\nWrote {WORK / 'gcps_1851.csv'}")
    print(f"Wrote {WORK / 'baltimore_1851.points'}")

    # Ship the first-order (affine) fit. Order-2 has a marginally lower RMSE
    # at the control points themselves (49m vs 56m) but with only 12 points
    # feeding 6 parameters per axis, it extrapolates unpredictably outside the
    # control-point hull -- visibly so at the map's corners in testing. The
    # affine degrades gracefully there instead. See docs/GEOREFERENCE.md.
    order = 1
    out_tif = WORK / "baltimore_1851_georef.tif"
    result = build_geotiff(rows, order, out_tif)
    if result and result.exists():
        size_mb = result.stat().st_size / 1e6
        print(f"\nGeoTIFF: {result} ({size_mb:.1f} MB, order={order})")
        if size_mb > 90:
            print("WARNING: exceeds 90MB commit cap -- do not commit this file; "
                  "add data/work/maps/*.tif to .gitignore.")


if __name__ == "__main__":
    main()
