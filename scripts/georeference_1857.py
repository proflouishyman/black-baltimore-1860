#!/usr/bin/env python3
"""Georeference Robert Taylor's 1857 "Map of the City and County of Baltimore".

Source scan
-----------
Library of Congress, https://www.loc.gov/item/2002624019/ (accessed 2026-08-08).
Full-resolution JP2, 15804 x 19291 px, 43.2 MB:
  https://tile.loc.gov/storage-services/service/gmd/gmd384/g3843/g3843b/la000284.jp2

The sheet is a COUNTY land-ownership map. Baltimore City appears only as an
inset in the upper right, occupying roughly x 10000-14420, y 4600-8500 of the
full-resolution scan, at about 1.65 m per pixel. Only that inset is
georeferenced here; the surrounding county map is at a different (much smaller)
scale and warping the whole sheet with one transform would be meaningless.

Why the reference geometry is NOT the HUE street file
-----------------------------------------------------
The point of georeferencing a period map for this project is to measure how far
the c.1930 HUE street file (ICPSR 35617) -- the layer every resident is
currently placed against -- disagrees with mid-century geometry. Fitting the
1857 sheet to HUE and then comparing the result to HUE is circular: the fit
absorbs exactly the disagreement it is supposed to expose, and the residual
reports only the map's internal noise.

So the control points here are resolved against MODERN street centrelines from
OpenStreetMap, which are GPS-derived and independent of both the 1857 map and
the 1930 survey. That makes two separate, non-circular measurements possible:

  1. how well the 1857 sheet can be brought onto true modern geometry
     (the leave-one-out cross-validated error, reported below), and
  2. how far HUE's own intersections sit from the modern ones at those same
     named crossings (`hue_vs_osm_m` in the GCP table) -- the error the project
     currently inherits, measured without reference to the 1857 map at all.

data/raw/balt_streets.geojson was tried first and rejected: it is a partial,
generalised extract (4878 features, several named streets reduced to
disconnected fragments or zero-length geometries), so most control pairs simply
do not cross in it. OSM is fetched fresh from Overpass and cached.

Ground control points
---------------------
Every pixel coordinate below was read off the full-resolution scan by cropping
the neighbourhood with GDAL, overlaying a labelled pixel grid, and locating the
street corridors visually. None is inferred, predicted or interpolated from the
fit. Street-name normalisation reuses scripts/geocode_1860.norm_street() so
that "North Charles Street" and "N CHARLES ST" collapse to the same key, as
elsewhere in this project.

Points that were considered and deliberately EXCLUDED are listed in EXCLUDED,
with the reason. The two structural exclusions are worth stating up front:

  * The quarter north-west of downtown (Bolton / Mount Royal, roughly
    x 11150-11750, y 5150-5600) is drawn as a DIAGONAL grid -- Lanvale,
    Dolphin, Preston and Biddle all run at about 40 degrees. Those streets run
    east-west in the built city. That quarter is a projected plat that was
    never executed, so no intersection in it can be matched to real geometry.
  * The far north-east (x > 12600, y < 5250) and the far south (y > 7400) are
    drawn as uniform empty rectangles with no buildings: platted, unbuilt land.
    A handful of points are taken from the edges of those zones but the
    interiors are left alone.

Fits
----
Affine (6 parameters), 2nd-order polynomial (12), and thin plate spline. The
TPS interpolates its control points exactly, so its FIT residual is ~0 by
construction and is not an accuracy measure; only its leave-one-out error is.
Leave-one-out cross validation is the headline number for all three.

Outputs
-------
  data/work/maps/gcps_1857.csv             GCPs, per-point residuals, LOO errors
  data/work/maps/baltimore_1857.points     QGIS georeferencer format
  data/work/maps/baltimore_1857_georef.tif GeoTIFF of the city inset
  docs/georef/1857.md                      written by hand, not by this script
"""

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import geocode_1860 as g60  # noqa: E402  (path must be set up first)

WORK = ROOT / "data" / "work" / "maps"
WORK.mkdir(parents=True, exist_ok=True)

CRS_EPSG = 6487  # NAD83(2011) / Maryland, metres -- project standard

SOURCE_URL = ("https://tile.loc.gov/storage-services/service/gmd/gmd384/"
              "g3843/g3843b/la000284.jp2")
SOURCE_ITEM = "https://www.loc.gov/item/2002624019/"
ACCESSED = "2026-08-08"
FULL_SIZE = (15804, 19291)

# The city inset inside the full sheet: x, y, width, height in scan pixels.
INSET = (10000, 4600, 4420, 3900)

QGIS_MACOS = "/Applications/QGIS-final-4_2_1.app/Contents/MacOS"
QGIS_RES = "/Applications/QGIS-final-4_2_1.app/Contents/Resources/qgis"

# Overpass bounding box covering the whole 1857 city and a margin.
OVERPASS_BOXES = [
    (39.235, -76.69, 39.285, -76.62),
    (39.235, -76.62, 39.285, -76.545),
    (39.285, -76.69, 39.335, -76.655),
    (39.285, -76.655, 39.335, -76.62),
    (39.285, -76.62, 39.335, -76.545),
]
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# ---------------------------------------------------------------------------
# Ground control points.
#
# (label, street_a, street_b, pixel_x, pixel_y)
# A street is ("CORE", "") for the whole street or ("CORE", "N") when only the
# directional half is wanted (HUE and OSM both split N/S and E/W halves, and
# merging them can put an intersection on the wrong side of Baltimore Street).
# Pixel coordinates are in FULL-RESOLUTION scan pixels.
# ---------------------------------------------------------------------------
GCPS = [
    # --- downtown core -----------------------------------------------------
    ("Charles & Baltimore",   ("CHARLES", "N"),    ("BALTIMORE", ""),   12020, 6074),
    ("Eutaw & Baltimore",     ("EUTAW", ""),       ("BALTIMORE", ""),   11723, 6075),
    ("Howard & Baltimore",    ("HOWARD", ""),      ("BALTIMORE", ""),   11798, 6075),
    ("Paca & Lombard",        ("PACA", ""),        ("LOMBARD", "W"),    11652, 6179),
    ("Eutaw & Lombard",       ("EUTAW", ""),       ("LOMBARD", "W"),    11723, 6179),
    ("Calvert & Pratt",       ("CALVERT", "S"),    ("PRATT", "E"),      12158, 6249),
    # --- north-central (Mount Vernon / Seton Hill) -------------------------
    ("St Paul & Chase",       ("SAINT PAUL", ""),  ("CHASE", "E"),      12092, 5224),
    ("Calvert & Biddle",      ("CALVERT", "N"),    ("BIDDLE", "E"),     12156, 5164),
    ("St Paul & Madison",     ("SAINT PAUL", ""),  ("MADISON", "E"),    12092, 5468),
    ("Howard & Centre",       ("HOWARD", "N"),     ("CENTRE", "W"),     11792, 5615),
    ("Howard & Madison",      ("HOWARD", "N"),     ("MADISON", "W"),    11795, 5468),
    ("Eutaw & Madison",       ("EUTAW", "N"),      ("MADISON", "W"),    11719, 5468),
    # --- east / north-east -------------------------------------------------
    ("Broadway & Monument",   ("BROADWAY", ""),    ("MONUMENT", "E"),   13125, 5540),
    ("Wolfe & Monument",      ("WOLFE", ""),       ("MONUMENT", "E"),   13296, 5533),
    ("Broadway & Baltimore",  ("BROADWAY", ""),    ("BALTIMORE", "E"),  13124, 5996),
    ("Wolfe & Baltimore",     ("WOLFE", ""),       ("BALTIMORE", "E"),  13296, 5990),
    ("Caroline & Baltimore",  ("CAROLINE", ""),    ("BALTIMORE", "E"),  12950, 5998),
    ("Broadway & Pratt",      ("BROADWAY", ""),    ("PRATT", "E"),      13124, 6146),
    # --- Fells Point -------------------------------------------------------
    ("Broadway & Eastern",    ("BROADWAY", ""),    ("EASTERN", ""),     13124, 6392),
    ("Broadway & Lancaster",  ("BROADWAY", ""),    ("LANCASTER", ""),   13124, 6578),
    ("Wolfe & Eastern",       ("WOLFE", ""),       ("EASTERN", ""),     13296, 6383),
    ("Bond & Aliceanna",      ("BOND", "S"),       ("ALICEANNA", ""),   13020, 6516),
    # --- west --------------------------------------------------------------
    ("Monroe & Baltimore",    ("MONROE", ""),      ("BALTIMORE", "W"),  10291, 6070),
    ("Monroe & Lombard",      ("MONROE", ""),      ("LOMBARD", "W"),    10291, 6192),
    ("Monroe & Pratt",        ("MONROE", ""),      ("PRATT", "W"),      10291, 6247),
    ("Fulton & Franklin",     ("FULTON", ""),      ("FRANKLIN", "W"),   10379, 5695),
    ("Calhoun & Lanvale",     ("CALHOUN", ""),     ("LANVALE", "W"),    10760, 5485),
    ("Carey & Mulberry",      ("CAREY", ""),       ("MULBERRY", "W"),   10840, 5760),
    ("Stricker & Mosher",     ("STRICKER", ""),    ("MOSHER", ""),      10688, 5330),
    ("Poppleton & Baltimore", ("POPPLETON", ""),   ("BALTIMORE", "W"),  11146, 6070),
    ("Poppleton & Lombard",   ("POPPLETON", ""),   ("LOMBARD", "W"),    11146, 6179),
    ("Poppleton & Pratt",     ("POPPLETON", ""),   ("PRATT", "W"),      11146, 6249),
    # --- south (Federal Hill and South Baltimore) --------------------------
    ("Charles & Cross",       ("CHARLES", "S"),    ("CROSS", ""),       12007, 6861),
    ("Charles & Hamburg",     ("CHARLES", "S"),    ("HAMBURG", ""),     12007, 6793),
    ("William & Cross",       ("WILLIAM", ""),     ("CROSS", "E"),      12193, 6855),
    ("Leadenhall & Hamburg",  ("LEADENHALL", ""),  ("HAMBURG", "W"),    11841, 6798),
    ("Charles & Ostend",      ("CHARLES", "S"),    ("OSTEND", "E"),     12007, 7016),
    ("Charles & Fort",        ("CHARLES", "S"),    ("FORT", ""),        12007, 7155),
    ("Charles & Randall",     ("CHARLES", "S"),    ("RANDALL", ""),     12007, 7241),
]

EXCLUDED = [
    ("Pulaski & Baltimore / Smallwood & Baltimore",
     "Read at x=10215 and x=10144. Modern spacing Smallwood->Pulaski->Monroe is "
     "121 m then 270 m; the map draws 71 px (117 m) then 75 px (123 m). The map "
     "is missing roughly a block's worth of ground between Pulaski and Monroe, so "
     "these two points are internally inconsistent with everything east of them. "
     "Dropped rather than allowed to drag the western fit."),
    ("Lanvale / Dolphin / Preston / Biddle west of Bolton",
     "Drawn as a diagonal grid at about 40 degrees from east-west. Those streets "
     "run east-west in the built city. This quarter of the sheet is a projected "
     "plat that was never executed and cannot be matched to real geometry."),
    ("Gay & Baltimore",
     "Gay Street is drawn diagonally through the block here and its centreline "
     "cannot be pinned to better than about 25 px (40 m) on the scan. Excluded "
     "rather than guessed."),
    ("Thames Street / City Dock / any harbour-edge point",
     "The Fells Point and Inner Harbour shorelines were extensively filled after "
     "1857 and the Jones Falls was culverted. Waterfront points measure land "
     "reclamation, not map error."),
    ("Anything inside the far north-east paper grid (x > 12600, y < 5250) "
     "and the far south below Fort Avenue (y > 7400)",
     "Drawn as uniform empty rectangles with no buildings: platted but unbuilt "
     "in 1857, and several of those streets were never cut as drawn."),
]


# ---------------------------------------------------------------------------
# Reference geometry
# ---------------------------------------------------------------------------

def fetch_osm(cache: Path):
    """Named road centrelines for Baltimore from Overpass, cached as GeoPackage.

    Modern geometry is used deliberately: it is independent of both the 1857
    sheet and the c.1930 HUE file, which is what makes the accuracy number and
    the HUE-displacement number non-circular. See the module docstring."""
    import geopandas as gpd
    from shapely.geometry import LineString

    if cache.exists():
        return gpd.read_file(cache)

    q_tmpl = ('[out:json][timeout:280];way["highway"~"^(motorway|trunk|primary|'
              'secondary|tertiary|unclassified|residential|living_street|'
              'pedestrian)$"]["name"](%s);out geom;')
    rows = {}
    for box in OVERPASS_BOXES:
        bb = ",".join(str(v) for v in box)
        data = urllib.parse.urlencode({"data": q_tmpl % bb}).encode()
        req = urllib.request.Request(OVERPASS_URL, data=data,
                                     headers={"User-Agent": "baltimore_map/1857 georef"})
        with urllib.request.urlopen(req, timeout=300) as r:
            payload = json.loads(r.read())
        for el in payload.get("elements", []):
            if el.get("type") != "way" or "geometry" not in el:
                continue
            name = el.get("tags", {}).get("name")
            pts = [(p["lon"], p["lat"]) for p in el.get("geometry", [])]
            if not name or len(pts) < 2:
                continue
            rows[el["id"]] = (name, LineString(pts))
    gdf = gpd.GeoDataFrame({"name": [v[0] for v in rows.values()]},
                           geometry=[v[1] for v in rows.values()], crs="EPSG:4326")
    cache.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(cache, driver="GPKG")
    return gdf


def index_streets(gdf, name_field="name"):
    """{core: geom, (core, dir): geom} using the project's own normalisation."""
    from shapely.ops import unary_union
    gdf = gdf.to_crs(epsg=CRS_EPSG)
    buckets = {}
    for name, geom in zip(gdf[name_field], gdf.geometry):
        core, d = g60.norm_street(name)
        if not core:
            continue
        buckets.setdefault(core, []).append(geom)
        if d:
            buckets.setdefault((core, d), []).append(geom)
    return {k: unary_union(v) for k, v in buckets.items()}


def key_of(street):
    core, d = street
    return core if not d else (core, d)


def crossings(streets, a, b):
    ga, gb = streets.get(key_of(a)), streets.get(key_of(b))
    if ga is None or gb is None:
        return []
    inter = ga.intersection(gb)
    return [p for p in getattr(inter, "geoms", [inter]) if p.geom_type == "Point"]


# ---------------------------------------------------------------------------
# Transforms.  All take pixel coords and return world coords.
# ---------------------------------------------------------------------------

def _design_affine(px, py):
    return np.c_[np.ones_like(px), px, py]


def _design_poly2(px, py):
    return np.c_[np.ones_like(px), px, py, px * px, px * py, py * py]


def _fit_linear(design, px, py, wx, wy):
    A = design(px, py)
    cx, *_ = np.linalg.lstsq(A, wx, rcond=None)
    cy, *_ = np.linalg.lstsq(A, wy, rcond=None)
    return cx, cy


def _apply_linear(design, coef, px, py):
    cx, cy = coef
    A = design(px, py)
    return A @ cx, A @ cy


def _tps_kernel(r2):
    # U(r) = r^2 log r, written on r^2 to avoid a sqrt; 0 at r == 0.
    out = np.zeros_like(r2)
    nz = r2 > 0
    out[nz] = 0.5 * r2[nz] * np.log(r2[nz])
    return out


def _tps_fit(px, py, wx, wy):
    n = len(px)
    dx = px[:, None] - px[None, :]
    dy = py[:, None] - py[None, :]
    K = _tps_kernel(dx * dx + dy * dy)
    P = np.c_[np.ones(n), px, py]
    L = np.zeros((n + 3, n + 3))
    L[:n, :n] = K
    L[:n, n:] = P
    L[n:, :n] = P.T
    sol_x = np.linalg.lstsq(L, np.r_[wx, np.zeros(3)], rcond=None)[0]
    sol_y = np.linalg.lstsq(L, np.r_[wy, np.zeros(3)], rcond=None)[0]
    return (px, py, sol_x, sol_y)


def _tps_apply(model, qx, qy):
    px, py, sx, sy = model
    n = len(px)
    dx = qx[:, None] - px[None, :]
    dy = qy[:, None] - py[None, :]
    K = _tps_kernel(dx * dx + dy * dy)
    P = np.c_[np.ones(len(qx)), qx, qy]
    # numpy raises spurious divide/overflow warnings out of matmul on the
    # exactly-zero diagonal that appears when predicting at the control points
    # themselves; the products are checked for finiteness instead.
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        ox = K @ sx[:n] + P @ sx[n:]
        oy = K @ sy[:n] + P @ sy[n:]
    if not (np.isfinite(ox).all() and np.isfinite(oy).all()):
        raise FloatingPointError("TPS produced a non-finite prediction")
    return ox, oy


class Model:
    """Uniform wrapper so affine / poly2 / TPS can be scored identically.

    Pixel coordinates are centred and scaled before fitting: the raw values are
    ~1e4 and the poly2 and TPS design matrices are badly conditioned without it.
    """

    def __init__(self, kind):
        self.kind = kind

    def fit(self, px, py, wx, wy):
        self.mx, self.my = px.mean(), py.mean()
        self.s = max(px.std(), py.std()) or 1.0
        u, v = (px - self.mx) / self.s, (py - self.my) / self.s
        if self.kind == "affine":
            self.coef = _fit_linear(_design_affine, u, v, wx, wy)
        elif self.kind == "poly2":
            self.coef = _fit_linear(_design_poly2, u, v, wx, wy)
        elif self.kind == "tps":
            self.coef = _tps_fit(u, v, wx, wy)
        else:
            raise ValueError(self.kind)
        return self

    def predict(self, px, py):
        u, v = (px - self.mx) / self.s, (py - self.my) / self.s
        if self.kind == "affine":
            return _apply_linear(_design_affine, self.coef, u, v)
        if self.kind == "poly2":
            return _apply_linear(_design_poly2, self.coef, u, v)
        return _tps_apply(self.coef, u, v)


def fit_residuals(kind, px, py, wx, wy):
    m = Model(kind).fit(px, py, wx, wy)
    ex, ey = m.predict(px, py)
    return np.hypot(ex - wx, ey - wy), m


def loo_errors(kind, px, py, wx, wy):
    """Leave-one-out cross validation: fit on n-1, predict the held-out point.

    This is the only honest accuracy figure here. The fit residual of a TPS is
    ~0 by construction because it interpolates its control points exactly, and
    even the polynomial residual is optimistic because the same points set the
    coefficients."""
    n = len(px)
    out = np.zeros(n)
    idx = np.arange(n)
    for i in range(n):
        keep = idx != i
        m = Model(kind).fit(px[keep], py[keep], wx[keep], wy[keep])
        ex, ey = m.predict(px[i:i + 1], py[i:i + 1])
        out[i] = float(np.hypot(ex[0] - wx[i], ey[0] - wy[i]))
    return out


# ---------------------------------------------------------------------------
# GGCP resolution
# ---------------------------------------------------------------------------

def build_table(osm, hue):
    """Resolve every GCP to a world coordinate.

    Where a pair crosses more than once (split carriageways, a street that
    doubles back), the candidate nearest the prediction of a bootstrap affine
    -- fitted only on the pairs that cross exactly once -- is taken. That is a
    disambiguation, not a fit: the pixel coordinate is never moved."""
    rows = []
    for label, a, b, px, py in GCPS:
        cands = crossings(osm, a, b)
        if not cands:
            print(f"  UNRESOLVED {label}: no crossing in modern geometry")
            continue
        rows.append(dict(label=label, a=a, b=b, px=float(px), py=float(py),
                         cands=cands))

    single = [r for r in rows if len(r["cands"]) == 1]
    px = np.array([r["px"] for r in single])
    py = np.array([r["py"] for r in single])
    wx = np.array([r["cands"][0].x for r in single])
    wy = np.array([r["cands"][0].y for r in single])
    boot = Model("affine").fit(px, py, wx, wy)

    for r in rows:
        ex, ey = boot.predict(np.array([r["px"]]), np.array([r["py"]]))
        best = min(r["cands"], key=lambda p: (p.x - ex[0]) ** 2 + (p.y - ey[0]) ** 2)
        r["wx"], r["wy"] = best.x, best.y
        r["n_cands"] = len(r["cands"])
        # The same named crossing located in the c.1930 HUE file. The distance
        # between the two is HUE's own error at that point, measured without
        # any reference to the 1857 map -- see the module docstring.
        hc = crossings(hue, r["a"], r["b"])
        if hc:
            h = min(hc, key=lambda p: (p.x - best.x) ** 2 + (p.y - best.y) ** 2)
            r["hue_dx"], r["hue_dy"] = h.x - best.x, h.y - best.y
            r["hue_d"] = float(np.hypot(r["hue_dx"], r["hue_dy"]))
        else:
            r["hue_dx"] = r["hue_dy"] = r["hue_d"] = None
        del r["cands"]
    return rows


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

def write_csv(rows, fits, loos, path):
    kinds = list(fits)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label", "street_a", "street_b", "pixel_x", "pixel_y",
                    "world_x_epsg6487", "world_y_epsg6487", "n_candidates"]
                   + [f"fit_resid_m_{k}" for k in kinds]
                   + [f"loo_err_m_{k}" for k in kinds]
                   + ["hue_minus_osm_east_m", "hue_minus_osm_north_m",
                      "hue_vs_osm_m"])
        for i, r in enumerate(rows):
            def s(x, n=2):
                return "" if x is None else f"{x:.{n}f}"
            w.writerow([r["label"],
                        r["a"][0] + (f" ({r['a'][1]})" if r["a"][1] else ""),
                        r["b"][0] + (f" ({r['b'][1]})" if r["b"][1] else ""),
                        f"{r['px']:.0f}", f"{r['py']:.0f}",
                        f"{r['wx']:.2f}", f"{r['wy']:.2f}", r["n_cands"]]
                       + [f"{fits[k][i]:.2f}" for k in kinds]
                       + [f"{loos[k][i]:.2f}" for k in kinds]
                       + [s(r["hue_dx"]), s(r["hue_dy"]), s(r["hue_d"])])


def write_points(rows, path):
    """QGIS Georeferencer .points format (pixel row stored negative)."""
    with open(path, "w") as f:
        f.write(f"#CRS: EPSG:{CRS_EPSG}\n")
        f.write("mapX,mapY,pixelX,pixelY,enable\n")
        for r in rows:
            f.write(f"{r['wx']:.3f},{r['wy']:.3f},"
                    f"{r['px']:.3f},{-r['py']:.3f},1\n")


def gdal_env():
    env = os.environ.copy()
    if shutil.which("gdal_translate") and shutil.which("gdalwarp"):
        return "gdal_translate", "gdalwarp", env
    t, w = Path(QGIS_MACOS) / "gdal_translate", Path(QGIS_MACOS) / "gdalwarp"
    if t.exists() and w.exists():
        env["PATH"] = QGIS_MACOS + os.pathsep + env.get("PATH", "")
        env["GDAL_DATA"] = f"{QGIS_RES}/gdal"
        env["PROJ_LIB"] = f"{QGIS_RES}/proj"
        return str(t), str(w), env
    return None, None, env


def ensure_scan(path: Path):
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {SOURCE_URL}")
    req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as fh:
        shutil.copyfileobj(r, fh)
    return path


def build_geotiff(rows, method, scan, out_path):
    """Crop the city inset, attach the GCPs, warp to EPSG:6487.

    `method` is "tps" or an integer polynomial order. Only the inset is warped:
    the county map that surrounds it on the sheet is at a completely different
    scale and one transform cannot serve both."""
    translate, warp, env = gdal_env()
    if translate is None:
        print("GDAL not found -- GeoTIFF skipped; .points and coefficients written.")
        return None
    x0, y0, w, h = INSET
    tmp_crop = WORK / "_1857_inset.tif"
    subprocess.run([translate, "-q", "-of", "GTiff", "-srcwin",
                    str(x0), str(y0), str(w), str(h), str(scan), str(tmp_crop)],
                   env=env, check=True)

    gcp_args = []
    for r in rows:
        gcp_args += ["-gcp", f"{r['px'] - x0:.3f}", f"{r['py'] - y0:.3f}",
                     f"{r['wx']:.3f}", f"{r['wy']:.3f}"]
    tmp_gcp = WORK / "_1857_gcp.tif"
    subprocess.run([translate, "-q", "-of", "GTiff", "-a_srs", f"EPSG:{CRS_EPSG}",
                    *gcp_args, str(tmp_crop), str(tmp_gcp)], env=env, check=True)

    meth = ["-tps"] if method == "tps" else ["-order", str(method)]
    subprocess.run([warp, "-q", "-r", "cubic", *meth,
                    "-t_srs", f"EPSG:{CRS_EPSG}",
                    "-co", "COMPRESS=JPEG", "-co", "TILED=YES",
                    "-co", "PHOTOMETRIC=YCBCR", "-co", "JPEG_QUALITY=85",
                    "-overwrite", str(tmp_gcp), str(out_path)], env=env, check=True)
    for p in (tmp_crop, tmp_gcp):
        p.unlink(missing_ok=True)
        for aux in WORK.glob(p.name + ".*"):
            aux.unlink(missing_ok=True)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", type=Path,
                    default=Path(os.environ.get("BALT_1857_SCAN",
                                 "/private/tmp/claude-502/g1857/la000284.jp2")),
                    help="full-resolution JP2; downloaded from LOC if absent")
    ap.add_argument("--osm-cache", type=Path,
                    default=Path("/private/tmp/claude-502/g1857/osm_streets.gpkg"),
                    help="cached Overpass extract (fetched if absent)")
    ap.add_argument("--no-tif", action="store_true")
    args = ap.parse_args()

    import geopandas as gpd

    print(f"reference: OSM modern centrelines (cache {args.osm_cache})")
    osm = index_streets(fetch_osm(args.osm_cache))
    hue = index_streets(gpd.read_file(g60.HUE_SHP), name_field="Full_Name")

    rows = build_table(osm, hue)
    px = np.array([r["px"] for r in rows])
    py = np.array([r["py"] for r in rows])
    wx = np.array([r["wx"] for r in rows])
    wy = np.array([r["wy"] for r in rows])

    kinds = ["affine", "poly2", "tps"]
    fits, loos, models = {}, {}, {}
    for k in kinds:
        fits[k], models[k] = fit_residuals(k, px, py, wx, wy)
        loos[k] = loo_errors(k, px, py, wx, wy)

    def rms(a):
        return float(np.sqrt(np.mean(np.asarray(a) ** 2)))

    print(f"\n{len(rows)} ground control points, "
          f"pixel extent x {px.min():.0f}-{px.max():.0f}, y {py.min():.0f}-{py.max():.0f}")
    print(f"{'transform':10s}{'fit RMSE':>12}{'LOO RMSE':>12}{'LOO median':>12}{'LOO max':>10}")
    for k in kinds:
        print(f"{k:10s}{rms(fits[k]):12.1f}{rms(loos[k]):12.1f}"
              f"{np.median(loos[k]):12.1f}{loos[k].max():10.1f}")

    aff = Model("affine").fit(px, py, wx, wy)
    # Report the affine in raw scan-pixel terms so it can be applied directly.
    s, mx, my = aff.s, aff.mx, aff.my
    (a0, a1, a2), (b0, b1, b2) = aff.coef
    print("\naffine in raw scan pixels  (E,N metres, EPSG:6487):")
    print(f"  E = {a0 - a1 * mx / s - a2 * my / s:.3f} "
          f"+ {a1 / s:.6f}*px + {a2 / s:.6f}*py")
    print(f"  N = {b0 - b1 * mx / s - b2 * my / s:.3f} "
          f"+ {b1 / s:.6f}*px + {b2 / s:.6f}*py")
    print(f"  ground sample distance about {abs(a1 / s):.3f} m/px east-west, "
          f"{abs(b2 / s):.3f} m/px north-south")

    west = px < 11500
    for tag, sel in (("west of Poppleton (px<11500)", west),
                     ("core and east (px>=11500)", ~west)):
        print(f"  {tag}: n={sel.sum()}, affine LOO RMSE {rms(loos['affine'][sel]):.1f} m, "
              f"TPS LOO RMSE {rms(loos['tps'][sel]):.1f} m")

    hd = [r["hue_d"] for r in rows if r["hue_d"] is not None]
    if hd:
        print(f"\nHUE c.1930 vs modern at the same {len(hd)} crossings: "
              f"median {np.median(hd):.1f} m, mean {np.mean(hd):.1f} m, "
              f"max {max(hd):.1f} m")

    print(f"\n{'point':24s}{'fit(aff)':>10}{'LOO(aff)':>10}{'LOO(p2)':>10}"
          f"{'LOO(tps)':>10}{'HUE-OSM':>10}")
    for i in np.argsort(-loos["affine"]):
        r = rows[i]
        h = "" if r["hue_d"] is None else f"{r['hue_d']:10.1f}"
        print(f"{r['label']:24s}{fits['affine'][i]:10.1f}{loos['affine'][i]:10.1f}"
              f"{loos['poly2'][i]:10.1f}{loos['tps'][i]:10.1f}{h:>10}")

    write_csv(rows, fits, loos, WORK / "gcps_1857.csv")
    write_points(rows, WORK / "baltimore_1857.points")
    print(f"\nwrote {WORK / 'gcps_1857.csv'}")
    print(f"wrote {WORK / 'baltimore_1857.points'}")

    if not args.no_tif:
        scan = ensure_scan(args.scan)
        # Ship the thin plate spline. Its leave-one-out error is materially
        # lower than the affine's because the sheet has a real, spatially
        # coherent stretch in its western third that no global transform can
        # remove, and the TPS absorbs it. The price is that a TPS is only
        # meaningful inside the control hull; outside it the surface runs away,
        # which is why the unbuilt fringes of this sheet must not be trusted.
        out = build_geotiff(rows, "tps", scan, WORK / "baltimore_1857_georef.tif")
        if out and out.exists():
            mb = out.stat().st_size / 1e6
            print(f"wrote {out} ({mb:.1f} MB)")
            if mb > 90:
                print("WARNING: over the 90 MB cap -- downsample before committing.")


if __name__ == "__main__":
    main()
