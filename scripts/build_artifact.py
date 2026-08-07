#!/usr/bin/env python3
"""Render the site's three pages from one template and one shared payload.

Each page is a full standalone document with the geometry inlined, because the
published pages must not fetch anything at runtime.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "web" / "template.html"
PAYLOAD = ROOT / "data" / "work" / "map_payload.json"
DOCS = ROOT / "docs"

PANEL_DENSITY = """
    <div class="stats">
      <div class="stat"><div class="n mono">25,680</div><div class="k">Free Black</div></div>
      <div class="stat"><div class="n mono">2,218</div><div class="k">Enslaved</div></div>
      <div class="stat"><div class="n mono">13.1%</div><div class="k">Of the city</div></div>
      <div class="stat"><div class="n mono">25.9%</div><div class="k">Ward 11, the highest</div></div>
    </div>

    <fieldset>
      <legend>Black share of ward population</legend>
      <div class="ramp">
        <div style="background:var(--c1)"></div><div style="background:var(--c2)"></div>
        <div style="background:var(--c3)"></div><div style="background:var(--c4)"></div>
        <div style="background:var(--c5)"></div>
      </div>
      <div class="ramp-lab"><span>under 5%</span><span>over 21%</span></div>
    </fieldset>

    <p class="note"><strong>This is the whole population, not a sample.</strong>
      Every person the census counted, free and enslaved, by ward. It is the
      reliable picture of where Black Baltimore lived. The two dot maps show
      named individuals, but only those a directory chose to list, which was
      never everyone.</p>

    <p class="note">Baltimore held the largest free Black population of any
      American city in 1860. The enslaved were 1&nbsp;per&nbsp;cent of the
      city and cannot be mapped more finely than this: they appear in the
      census under an owner's name, with no address of their own.</p>
"""

PANEL_1860 = """
    <div class="stats">
      <div class="stat"><div class="n mono">4,251</div><div class="k">Listed</div></div>
      <div class="stat"><div class="n mono">2,866</div><div class="k">Placed</div></div>
      <div class="stat"><div class="n mono">848</div><div class="k">Anchored</div></div>
      <div class="stat"><div class="n mono">1 in 4</div><div class="k">Street gone by 1930</div></div>
    </div>

    <fieldset>
      <legend>Show</legend>
      <label class="row"><input type="checkbox" id="t0" checked>
        <span class="swatch" style="background:var(--anchored)"></span>
        <span><span class="lab">Anchored &mdash; 848</span><br>
          <span class="sub">Placed between two named corners using the house
            numbers the directory itself prints.</span></span></label>
      <label class="row"><input type="checkbox" id="t2" checked>
        <span class="swatch" style="background:var(--approx)"></span>
        <span><span class="lab">Street&nbsp;only &mdash; 2,018</span><br>
          <span class="sub">Street is known, position along it is estimated.</span></span></label>
      <label class="row"><input type="checkbox" id="tw">
        <span class="ward-key"></span>
        <span><span class="lab">Ward boundaries</span><br>
          <span class="sub">Compare against the density map.</span></span></label>
    </fieldset>

    <p class="note"><strong>Working prototype.</strong> Street geometry is a
      c.1930 survey, the closest layer that still carries the alleys &mdash;
      Camel, Pin, Welcome &mdash; where much of this population lived. Of the
      1860 addresses, 26% sit on streets already gone by 1930 and a further
      12% on streets lost since. A georeferenced 1860s map is the next step
      and will move these dots.</p>
"""

PANEL_1842 = """
    <div class="stats">
      <div class="stat"><div class="n mono">2,724</div><div class="k">Listed</div></div>
      <div class="stat"><div class="n mono">637</div><div class="k">Placed</div></div>
      <div class="stat"><div class="n mono">2,133</div><div class="k">Relative addresses</div></div>
      <div class="stat"><div class="n mono">18</div><div class="k">Years before 1860</div></div>
    </div>

    <p class="note"><strong>No house numbers existed yet.</strong> Matchett's
      gives directions instead: <em>Pitt st w of Ann</em>, or
      <em>w side Strawberry al n of Gough st</em>. So each person is placed on
      a block face &mdash; the stretch of one street between two intersections
      &mdash; not at a house. These dots are deliberately coarser than 1860's
      and should never be read as addresses.</p>

    <p class="note"><strong>Coverage is the weak point here, and it is not
      random.</strong> Only 637 of 2,133 relative addresses resolve, because
      the streets that fail are disproportionately the alleys: Strawberry,
      Happy, Sugar, Lerew's. They are absent even from the 1930 survey, having
      been renamed or cleared before it. Recovering them needs the
      nineteenth-century street-name concordances, which is the next task.</p>
"""

PAGES = [
    ("index.html", "density", "Density",
     "Eighth Census of the United States",
     "Where Black Baltimore lived, 1860",
     "The whole city by ward, free and enslaved, as the census counted it.",
     PANEL_DENSITY),
    ("1860.html", "1860", "1860",
     "Wood's Baltimore City Directory",
     "Black Baltimore, 1860",
     "Every resident listed in the directory's separate “Colored Persons” "
     "section, placed on the streets they lived on.",
     PANEL_1860),
    ("1842.html", "1842", "1842",
     "Matchett's Baltimore Director",
     "Black Baltimore, 1842",
     "The “Colored Householders” section, placed by block face because "
     "the city had no house numbers yet.",
     PANEL_1842),
]


def main():
    tpl = TPL.read_text(encoding="utf8")
    payload = PAYLOAD.read_text(encoding="utf8").replace("</", "<\\/")
    DOCS.mkdir(parents=True, exist_ok=True)

    for i, (fname, mode, _short, eyebrow, h1, lede, panel) in enumerate(PAGES):
        body = (tpl
                .replace("__TITLE__", f"{h1} — Black Baltimore")
                .replace("__EYEBROW__", eyebrow)
                .replace("__H1__", h1)
                .replace("__LEDE__", lede)
                .replace("__PANEL__", panel)
                .replace("__MODE__", mode))
        for n in range(3):
            body = body.replace(f"__NAV{n}__", 'aria-current="page"' if n == i else "")
        body = body.replace("__PAYLOAD__", payload)

        doc = ("<!doctype html>\n<html lang=\"en\">\n<head>\n"
               "<meta charset=\"utf-8\">\n"
               "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
               f"<meta name=\"description\" content=\"{lede}\">\n"
               f"<meta property=\"og:title\" content=\"{h1}\">\n"
               f"<meta property=\"og:description\" content=\"{lede}\">\n"
               "<link rel=\"icon\" href=\"data:image/svg+xml,"
               "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>"
               "<text y='14' font-size='14'>&#x1F5FA;</text></svg>\">\n"
               + body)
        doc = doc.replace('<div class="wrap">', '</head>\n<body>\n<div class="wrap">', 1)
        doc += "\n</body>\n</html>"
        (DOCS / fname).write_text(doc, encoding="utf8")
        print(f"wrote docs/{fname} ({(DOCS/fname).stat().st_size/1_000_000:.2f} MB)")


if __name__ == "__main__":
    main()
