#!/usr/bin/env python3
"""Render the georeferenced 1851 map into the map pages' own canvas space.

The map pages do not use Leaflet. They draw into a plain canvas whose
coordinates are a fixed square projection of EPSG:6487, computed in
`prep_payloads.py`. Dropping a slippy-tile basemap in would mean rewriting the
renderer, so instead this pre-warps the georeferenced 1851 raster ONCE into
exactly that square. The page then draws it as a single image with no
projection maths at runtime and no network dependency.

Source: `data/work/maps/baltimore_1851_georef_v2.tif`, the 68-control-point
polynomial-2 warp described in docs/GEOREFERENCE.md, cross-validated at 12.9 m
(NSSDA 22.3 m at 95% confidence). It is stored in WGS84, so the pipeline here is

    canvas pixel -> EPSG:6487 metres -> WGS84 degrees -> source pixel

No GDAL or rasterio is available in this environment, so the warp is done
directly with pyproj and numpy. Nearest-neighbour sampling is adequate: the
output is a 2000 px preview of a raster whose own positional error is 12.9 m,
about 4 output pixels, so interpolation would be false precision.

Output: docs/img/base_1851.jpg
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
from PIL import Image
from pyproj import Transformer
from shapely.geometry import box

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"
RAW = ROOT / "data" / "raw"
OUT = ROOT / "docs" / "img" / "base_1851.jpg"

SRC = WORK / "maps" / "baltimore_1851_georef_v2.tif"

# These MUST match prep_payloads.py or the overlay will not register.
W = H = 1600
PAD = 24
MARGIN = 200
CRS_M = 6487

# Output resolution. Higher than the 1600-unit canvas so the layer stays sharp
# when the user zooms in, but small enough to ship over the wire.
RES = 2000

# The source is 14883 x 9377. Downsampling before sampling keeps peak memory
# near 150 MB instead of 420 MB, and costs nothing at a 2000 px output.
MAX_SRC_W = 6000


def canvas_extent():
    """Recompute the exact square prep_payloads.py projects into.

    Derived from the same geometry (all placed people plus the 1846-1860 and
    1861-1882 ward polygons) so the two cannot drift apart.
    """
    ward_dir = RAW / "hue" / "HUE_Baltimore_Wards"
    w60 = gpd.read_file(ward_dir / "baltimore_wards_1846_1860.shp").to_crs(epsg=CRS_M)
    w68 = gpd.read_file(ward_dir / "baltimore_wards_1861_1882.shp").to_crs(epsg=CRS_M)

    geoms = list(w60.geometry) + list(w68.geometry)
    for f in sorted(WORK.glob("people_*_geocoded.geojson")):
        g = gpd.read_file(f).to_crs(epsg=CRS_M)
        geoms.extend(x for x in g.geometry if x is not None and not x.is_empty)

    minx, miny, maxx, maxy = gpd.GeoSeries(geoms, crs=f"EPSG:{CRS_M}").total_bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    half = max(maxx - minx, maxy - miny) / 2 + MARGIN
    return cx - half, cy - half, half


def geotiff_grid(path):
    """Top-left corner and pixel size from the GeoTIFF tags, in degrees."""
    im = Image.open(path)
    t = im.tag_v2
    sx, sy = t[33550][0], t[33550][1]
    tie = t[33922]
    return im, tie[3], tie[4], sx, sy


def main():
    if not SRC.exists():
        sys.exit(f"missing {SRC.relative_to(ROOT)} - run the georeferencing first")

    x0, y0, half = canvas_extent()
    scale = (W - 2 * PAD) / (2 * half)          # canvas units per metre
    print(f"canvas extent  x0={x0:.1f} y0={y0:.1f} half={half:.1f} m")
    print(f"metres per canvas unit: {1/scale:.3f}")

    im, lon0, lat0, dlon, dlat = geotiff_grid(SRC)
    sw, sh = im.size
    print(f"source {sw}x{sh}, origin ({lon0:.6f}, {lat0:.6f}), "
          f"pixel {dlon:.3e} deg")

    shrink = 1
    if sw > MAX_SRC_W:
        shrink = sw / MAX_SRC_W
        im = im.resize((int(sw / shrink), int(sh / shrink)), Image.BILINEAR)
        print(f"downsampled source by {shrink:.2f}x to {im.size}")
    arr = np.asarray(im.convert("RGB"))
    ah, aw = arr.shape[:2]

    # Output grid, in canvas units, then to metres. sy is flipped because the
    # canvas y axis points down while EPSG:6487 northings point up.
    px = np.arange(RES, dtype=np.float64) * (W / RES)
    py = np.arange(RES, dtype=np.float64) * (H / RES)
    gx, gy = np.meshgrid(px, py)
    mx = x0 + (gx - PAD) / scale
    my = y0 + (H - PAD - gy) / scale

    tr = Transformer.from_crs(f"EPSG:{CRS_M}", "EPSG:4326", always_xy=True)
    lon, lat = tr.transform(mx, my)

    # degrees -> source pixel, accounting for the downsample
    sxp = (lon - lon0) / dlon / shrink
    syp = (lat0 - lat) / dlat / shrink

    xi = np.rint(sxp).astype(np.int32)
    yi = np.rint(syp).astype(np.int32)
    inside = (xi >= 0) & (xi < aw) & (yi >= 0) & (yi < ah)
    xi = np.clip(xi, 0, aw - 1)
    yi = np.clip(yi, 0, ah - 1)

    out = arr[yi, xi]
    # Anything outside the source sheet becomes white rather than a smeared
    # edge pixel, so the layer visibly stops where the map stops.
    out[~inside] = 255

    cover = inside.mean() * 100
    print(f"source covers {cover:.1f}% of the canvas square")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(OUT, quality=82, optimize=True, progressive=True)
    print(f"wrote {OUT.relative_to(ROOT)} "
          f"({OUT.stat().st_size/1_000_000:.2f} MB, {RES}x{RES})")


if __name__ == "__main__":
    sys.exit(main())
