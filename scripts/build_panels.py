#!/usr/bin/env python3
"""Render the maps at print resolution for exhibit panels.

The site is built for a screen. An exhibit panel is a different object: it is
read from two metres away, it is printed once, and nothing about it can be
toggled. This renders the same maps, from the same payload, at a size and
density a printer can use.

Method. The maps draw into a canvas whose renderer already respects
devicePixelRatio, so it draws vector geometry at whatever density it is given
rather than upscaling a screen-sized bitmap. Driving a headless Chrome with a
large `device_scale_factor` therefore produces genuinely sharp output, not an
enlargement. `?bare=1` strips the rail, the HUD and the zoom buttons so the
canvas fills the frame, and the other URL parameters set year, layers and
palette, which means every panel here is reproducible from its URL alone.

Sizes are given in inches at a target DPI. A 24 x 36 inch panel at 300 dpi is
7200 x 10800 pixels, which Chrome will not rasterise in one pass, so the
viewport is kept at a sane CSS size and the density is carried by
`device_scale_factor`. 200 dpi is the default because it is the honest ceiling
for this data: at 300 dpi on a 36 inch panel a single resident dot would be
drawn to a precision the geocoding does not have.

These are drafts for choosing from, not final artwork. There is no title block,
no legend furniture and no caption, because those are design decisions that
depend on how many panels there are and how they hang.

Usage:
    ./.venv/bin/python scripts/build_panels.py            # all panels, 200 dpi
    ./.venv/bin/python scripts/build_panels.py --dpi 300
    ./.venv/bin/python scripts/build_panels.py --only 1840

Output: panels/<name>.png
"""

import argparse
import asyncio
import http.server
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = ROOT / "panels"
PORT = 8901

# Landscape by default, 36 x 24 inches. Baltimore's built extent is
# appreciably wider than it is tall, so a portrait panel spends its top and
# bottom thirds on empty ground. Pass --portrait to flip it. Chrome gets a CSS
# viewport in this aspect and the pixel density comes from device_scale_factor.
PANEL_W_IN, PANEL_H_IN = 36, 24
CSS_W = 1200                       # CSS px; height follows the aspect ratio

PANELS = [
    ("1820_density", "index.html", {"year": "1820"},
     "Black share of ward population, 1820. Twelve wards."),
    ("1840_density", "index.html", {"year": "1840"},
     "Black share of ward population, 1840. Twelve wards."),
    ("1850_density", "index.html", {"year": "1850"},
     "Black share of ward population, 1850. Twenty wards."),
    ("1860_density", "index.html", {"year": "1860"},
     "Black share of ward population, 1860. Twenty wards."),
    ("1842_people", "1842.html", {},
     "744 named Black residents, 1842, placed by block face."),
    ("1860_people", "1860.html", {},
     "3,054 named Black residents, 1860, placed by house number."),
    ("1860_people_on_1851", "1860.html", {"layers": "t51"},
     "1860 residents over Sidney and Neff's 1851 city."),
    ("1868_people", "1868.html", {},
     "6,070 named Black residents, 1868, three years after emancipation."),
]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DOCS), **kw)

    def log_message(self, *a):
        pass


def serve():
    """Serve docs/ locally. The pages are self-contained but the base layer
    image is fetched over HTTP, so file:// would fail on it."""
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", PORT), Quiet)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def url(page, params, theme):
    q = {"bare": "1", "theme": theme, **params}
    qs = "&".join(f"{k}={v}" for k, v in q.items())
    return f"http://127.0.0.1:{PORT}/{page}?{qs}"


async def render(panels, dpi, theme):
    from playwright.async_api import async_playwright

    css_h = round(CSS_W * PANEL_H_IN / PANEL_W_IN)
    scale = PANEL_W_IN * dpi / CSS_W
    px = (round(CSS_W * scale), round(css_h * scale))
    print(f"panel {PANEL_W_IN}x{PANEL_H_IN}in at {dpi}dpi "
          f"-> {px[0]}x{px[1]}px (css {CSS_W}x{css_h}, scale {scale:.2f})")

    OUT.mkdir(exist_ok=True)
    made = []
    async with async_playwright() as p:
        # A fresh browser rather than the shared debug instance: device scale
        # factor is a context-level setting and must not leak into a session
        # someone else is using.
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": CSS_W, "height": css_h},
            device_scale_factor=scale)
        pg = await ctx.new_page()
        for name, page, params, caption in panels:
            u = url(page, params, theme)
            await pg.goto(u, wait_until="networkidle", timeout=120_000)
            # The base-layer image loads lazily on toggle, so give it a beat
            # and confirm the canvas actually has content before capturing.
            await pg.wait_for_timeout(2500 if params.get("layers") else 1200)
            # Sample a grid across the WHOLE canvas, not a corner. On a
            # portrait panel the corners are legitimately empty ground, so a
            # corner sample reports "blank" on a perfectly good map.
            blank = await pg.evaluate("""() => {
              const c = document.getElementById('map');
              if (!c) return 'no canvas';
              const g = c.getContext('2d');
              const seen = new Set();
              const N = 24;
              for (let i = 1; i < N; i++) {
                for (let j = 1; j < N; j++) {
                  const d = g.getImageData(Math.floor(c.width * i / N),
                                           Math.floor(c.height * j / N), 1, 1).data;
                  seen.add(d[0] + ',' + d[1] + ',' + d[2]);
                  if (seen.size > 3) return false;
                }
              }
              return 'only ' + seen.size + ' distinct colours';
            }""")
            if blank:
                print(f"  SKIP {name}: canvas is {blank}")
                continue
            dest = OUT / f"{name}.png"
            await pg.locator("#map").screenshot(path=str(dest))
            mb = dest.stat().st_size / 1_000_000
            print(f"  {dest.name:26s} {mb:6.1f} MB   {caption}")
            made.append((name, caption, u))
        await browser.close()

    (OUT / "PANELS.md").write_text(
        "# Exhibit panel drafts\n\n"
        f"Rendered at {PANEL_W_IN} x {PANEL_H_IN} inches, {dpi} dpi, "
        f"{px[0]} x {px[1]} px, {theme} palette.\n\n"
        "Drafts for selection, not final artwork. No title block, legend "
        "furniture or caption, because those depend on how many panels there "
        "are and how they hang.\n\n"
        "Each panel is reproducible from its URL. Rebuild with "
        "`./.venv/bin/python scripts/build_panels.py`.\n\n"
        + "\n".join(f"- **{n}.png** {c}  \n  `{u}`" for n, c, u in made) + "\n")
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--theme", default="light", choices=["light", "dark"])
    ap.add_argument("--only", help="substring match on panel name")
    ap.add_argument("--portrait", action="store_true",
                    help="24x36 instead of the default 36x24")
    ap.add_argument("--size", help="override, e.g. 48x32 (inches)")
    a = ap.parse_args()

    global PANEL_W_IN, PANEL_H_IN
    if a.size:
        PANEL_W_IN, PANEL_H_IN = (int(v) for v in a.size.lower().split("x"))
    elif a.portrait:
        PANEL_W_IN, PANEL_H_IN = PANEL_H_IN, PANEL_W_IN

    sel = [p for p in PANELS if not a.only or a.only in p[0]]
    if not sel:
        sys.exit(f"no panel matches {a.only!r}")

    srv = serve()
    try:
        made = asyncio.run(render(sel, a.dpi, a.theme))
    finally:
        srv.shutdown()
    print(f"\nwrote {len(made)} panel(s) to {OUT.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
