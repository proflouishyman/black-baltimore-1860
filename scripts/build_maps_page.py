#!/usr/bin/env python3
"""Build docs/maps.html: a gallery of period Baltimore maps, 1804-1876.

These are not the base layer anything on this site is placed against (that is
the c.1930 HUE street survey, chosen because it still carries the alleys). They
are shown because a viewer who has just looked at forty years of dots wants to
see the city itself, and because two of them (1822, 1851) are candidates for
georeferencing this project against a period source rather than a modern one.

Thumbnails are generated here from source images in data/raw/maps/ (already
downloaded LOC/Digital Maryland previews) into docs/img/maps/. The page is
built from the shared web/content.html template, reusing build_artifact's
nav_html() and document() so the chrome matches every other page exactly.
"""

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "maps"
THUMB_DIR = ROOT / "docs" / "img" / "maps"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_artifact import nav_html, document  # noqa: E402

THUMB_LONG_EDGE = 900
JPEG_QUALITY = 80

# Chronological, 1804-1876. window=True for the project's own 1819-1868 range.
# full_res: (label, url, pixel dims or None) pointing at the actual
# full-resolution copy held by the institution, not a resized derivative.
MAPS = [
    dict(
        year=1804, title="Improved plan of the city of Baltimore",
        maker="Warner & Hanna", institution="Library of Congress",
        src="baltimore_1804_improved_plan_preview.jpg",
        item_url="https://www.loc.gov/item/77691636/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/77691636/",
                   "JP2, 3,703 × 2,932 px"),
        window=False,
        caption="A pictorial plan bound into James Robinson's 1804 Baltimore "
                "directory, fifteen years before Jackson's directory gives us "
                "our first mapped year. Included for the shape of the city "
                "just before this project's period begins, not as a source "
                "for anyone on these maps.",
    ),
    dict(
        year=1819, title="Map of Maryland, with inset of the City of Baltimore",
        maker="Fielding Lucas, Jr.",
        institution="Enoch Pratt Free Library, via Digital Maryland (Cator Collection)",
        src="maryland_1819_with_baltimore_inset.jpg",
        item_url="https://collections.digitalmaryland.org/digital/collection/cator/id/163",
        full_res=("Download full resolution", "https://collections.digitalmaryland.org/"
                   "digital/download/collection/cator/id/163/size/full",
                   "5,000 × 4,009 px, 600dpi"),
        window=True,
        caption="The same year as Jackson's directory, the earliest year "
                "mapped on this site. The Baltimore inset is small, a "
                "shaded patch showing how much of the city was actually "
                "built up, with the Washington Monument marked half-finished "
                "at the edge of Howard's woods.",
    ),
    dict(
        year=1822, title="Plan of the city of Baltimore",
        maker="Surveyed by Thomas H. Poppleton, published by Fielding Lucas, Jr.",
        institution="Library of Congress",
        src="baltimore_1822_poppleton_preview.jpg",
        item_url="https://www.loc.gov/item/2002624027/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/2002624027/",
                   "JP2, 6,975 × 5,506 px"),
        window=True,
        caption="The official city plat, the survey Baltimore was actually "
                "laid out from, and contemporary with our 1819 and 1822 "
                "cohorts. Poppleton was commissioned to survey and fix the "
                "city's streets in 1818, and this plan is the printed result "
                "of that survey rather than a later redrawing of it.",
    ),
    dict(
        year=1823, title="This plan of the city of Baltimore",
        maker="Thomas H. Poppleton, cartographer",
        institution="Library of Congress",
        src="baltimore_1823_this_plan_preview.jpg",
        item_url="https://www.loc.gov/item/77691538/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/77691538/",
                   "JP2, 15,196 × 13,376 px"),
        window=True,
        caption="A hand colored, much larger edition of the same survey, "
                "printed one year after the 1822 plat above and adding an "
                "inset of the original 1729 town, sixty acres, drawn to scale "
                "inside the 1823 city that had grown up around it.",
    ),
    dict(
        year=1836, title="Plan of the city of Baltimore",
        maker="Fielding Lucas, Jr.", institution="Library of Congress",
        src="baltimore_1836_plan_preview.jpg",
        item_url="https://www.loc.gov/item/2002624026/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/2002624026/",
                   "JP2, 6,923 × 5,374 px"),
        window=True,
        caption="Fourteen years after Poppleton's plat, with wards drawn and "
                "a population table added. Sits in the gap between our 1822 "
                "and 1842 directory cohorts, where the site has no map of "
                "its own to show.",
    ),
    dict(
        year=1844, title="Plan of Baltimore",
        maker="Fielding Lucas, Jr.", institution="Library of Congress",
        src="baltimore_1844_plan_preview.jpg",
        item_url="https://www.loc.gov/item/2020587086/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/2020587086/",
                   "JP2, 3,816 × 3,936 px"),
        window=True,
        caption="One year before our 1845 cohort, the first year on this "
                "site with house numbers. This plan shows the wards and the "
                "young rail lines the numbered addresses of 1845 sit "
                "alongside.",
    ),
    dict(
        year=1851, title="Plan of the city of Baltimore, Maryland",
        maker="Sidney & Neff", institution="Library of Congress",
        src="baltimore_1851_plan_preview.jpg",
        item_url="https://www.loc.gov/item/2004629026/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/2004629026/",
                   "JP2, 13,414 × 10,643 px"),
        window=True,
        caption="Names every street, draws building footprints, and prints "
                "the ward numbers directly on the map, which is why it is a "
                "candidate for checking our ward polygons against a period "
                "source rather than a modern reconstruction. Its own "
                "population table does not reconcile with the census: the "
                "printed total, 169,303, does not equal the sum of its own "
                "twenty rows, 169,032. The census is the better authority on "
                "numbers.",
    ),
    dict(
        year=1856, title="Scott's map of the city of Baltimore",
        maker="Simon J. Martenet", institution="Library of Congress",
        src="baltimore_1856_scotts_map_preview.jpg",
        item_url="https://www.loc.gov/item/2002624007/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/2002624007/",
                   "JP2, 18,170 × 14,666 px"),
        window=True,
        caption="Wards and landowners, five years before Wood's 1860 "
                "directory. Printed as two large sheets, so this thumbnail is "
                "a small fraction of what the original carries.",
    ),
    dict(
        year=1857, title="Map of the city and county of Baltimore, Maryland",
        maker="Robert Taylor, surveyor", institution="Library of Congress",
        src="baltimore_1857_map_city_county_preview.jpg",
        item_url="https://www.loc.gov/item/2002624019/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/2002624019/",
                   "JP2, 15,804 × 19,291 px"),
        window=True,
        caption="A land ownership map reaching past the city line into the "
                "surrounding county, naming landowners rather than street "
                "residents. Useful for what lay just outside the ward "
                "boundaries this site maps.",
    ),
    dict(
        year=1860, title="Map of Baltimore, published for the Balto. City Directory",
        maker="Surveyed by William Sides, published by John W. Woods",
        institution="Talbot County Free Library, via Digital Maryland",
        src="baltimore_1860_directory_map.jpg",
        item_url="https://collections.digitalmaryland.org/digital/collection/tcgc/id/22",
        full_res=("Download full resolution", "https://collections.digitalmaryland.org/"
                   "digital/download/collection/tcgc/id/22/size/full",
                   "5,000 × 4,009 px, 600dpi"),
        window=True,
        caption="The exact companion to our strongest year: bound into the "
                "same volume the residents on the 1860 page were parsed "
                "from, published by the same John W. Woods. Its margins list "
                "street names and prominent businesses alongside the "
                "directory page numbers where they appear, a built-in index "
                "between the map and the book.",
    ),
    dict(
        year=1866, title="Map of Baltimore",
        maker="William Sides, cartographer, published by John W. Woods",
        institution="Library of Congress",
        src="baltimore_1866_map_of_baltimore_preview.jpg",
        item_url="https://www.loc.gov/item/2020587113/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/2020587113/",
                   "JP2, 6,073 × 4,450 px"),
        window=True,
        caption="The same surveyor and publisher as the 1860 directory map "
                "above, six years later and after Baltimore redrew its wards "
                "in 1861. Our 1868 page is geocoded against that later ward "
                "boundary, so this is the map that shows it.",
    ),
    dict(
        year=1869, title="E. Sachse & Co.'s bird's eye view of the city of Baltimore",
        maker="E. Sachse & Co.", institution="Library of Congress",
        src="baltimore_1869_sachse_birdseye_preview.jpg",
        item_url="https://www.loc.gov/item/75694535/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/75694535/",
                   "JP2, 39,440 × 19,008 px, not downloaded here"),
        window=False,
        caption="Not measurable, drawn in perspective rather than to scale, "
                "one year after the last directory on this site. It shows "
                "the city the way a person standing above it would see it, "
                "which no plan or plat in this gallery does. The master JP2 "
                "is enormous, so only a downsized thumbnail is used here.",
    ),
    dict(
        year=1876, title="Map of Baltimore prepared for the Stranger's guide in Baltimore",
        maker="William Sides, cartographer, published by John W. Woods",
        institution="Library of Congress",
        src="baltimore_1876_strangers_guide_preview.jpg",
        item_url="https://www.loc.gov/item/2020587065/",
        full_res=("View at Library of Congress", "https://www.loc.gov/item/2020587065/",
                   "JP2, 6,477 × 4,592 px"),
        window=False,
        caption="The same survey team as the 1860 and 1866 maps, eight years "
                "after the last directory this site draws on. Shown to mark "
                "how far past this project's period the same mapmakers kept "
                "working, not as a source for anyone on the site.",
    ),
]


def make_thumbnails():
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    for m in MAPS:
        src = RAW / m["src"]
        dst = THUMB_DIR / f"{m['year']}.jpg"
        with Image.open(src) as im:
            im = im.convert("RGB")
            w, h = im.size
            scale = THUMB_LONG_EDGE / max(w, h)
            if scale < 1:
                im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
            im.save(dst, "JPEG", quality=JPEG_QUALITY, optimize=True)
        kb = dst.stat().st_size / 1_000
        print(f"  thumb {m['year']}.jpg ({kb:.0f} KB)")


def card_html(m):
    badge = ('<span class="map-badge in">1819&ndash;1868</span>' if m["window"] else
             '<span class="map-badge out">outside the project window</span>')
    label, url, dims = m["full_res"]
    return f"""
    <figure class="map-card">
      <a href="{m['item_url']}" target="_blank" rel="noopener">
        <img src="img/maps/{m['year']}.jpg" alt="{m['title']}, {m['year']}" loading="lazy">
      </a>
      {badge}
      <h3>{m['year']} &middot; {m['title']}</h3>
      <p class="meta">{m['maker']} &middot; {m['institution']}</p>
      <p>{m['caption']}</p>
      <p class="dl"><a href="{url}" target="_blank" rel="noopener">{label}</a>
        <span class="mono" style="color:var(--ink-3);font-size:11.5px"> &middot; {dims}</span></p>
    </figure>"""


SANBORN_NOTE = """
  <div class="note"><strong>Not shown here: the Sanborn fire insurance
    maps.</strong> Sanborn coverage of Baltimore City begins in 1890, more
    than twenty years after the last directory this site draws on, so no one
    mapped here can be placed against one. They are still worth knowing
    about: Sanborn maps draw individual building footprints and note
    construction material, which is the closest surviving record of the
    alley fabric before it was cleared in the twentieth century. See the
    Library of Congress
    <a href="https://www.loc.gov/collections/sanborn-maps/?q=baltimore"
    target="_blank" rel="noopener">Sanborn Maps collection, filtered to
    Baltimore</a>.</div>
"""


def build_maps_page(content_tpl):
    intro = """
  <p>Thirteen printed maps of Baltimore, 1804 to 1876, shown small below and
    linked out to the full-resolution original held by the Library of
    Congress or Digital Maryland. None of them is the base layer this
    project's residents are placed against, which is a circa-1930 street
    survey, chosen because it still carries the alleys most of this
    population lived on. These are here because a map of dots is easier to
    read once you have seen the city the dots sit on.</p>
  <p>Maps marked <strong>1819&ndash;1868</strong> fall inside the span this
    site's directories cover. The rest are shown for context: one map from
    before Jackson's 1819 directory, and two from after the last directory,
    1868, used here.</p>
"""
    grid = '\n  <div class="map-grid">' + "".join(card_html(m) for m in MAPS) + "\n  </div>\n"
    body = (content_tpl
            .replace("__TITLE__", "Maps — Black Baltimore")
            .replace("__NAV__", nav_html("maps.html"))
            .replace("__EYEBROW__", "Thirteen maps, 1804–1876")
            .replace("__H1__", "Other maps of the city")
            .replace("__LEDE__", "The printed maps Baltimore made of itself "
                                  "across this period, each linked to its "
                                  "full-resolution original.")
            .replace("__CONTENT__", intro + grid + SANBORN_NOTE)
            .replace("__SCRIPT__", ""))
    desc = ("A gallery of period Baltimore maps, 1804-1876, each linked to its "
            "full-resolution original at the Library of Congress or Digital Maryland.")
    out = ROOT / "docs" / "maps.html"
    out.write_text(document(body, "Other maps of the city", desc), encoding="utf8")
    print(f"wrote docs/maps.html ({out.stat().st_size/1_000:.0f} KB)")


def main():
    print("generating map thumbnails...")
    make_thumbnails()
    content_tpl = (ROOT / "web" / "content.html").read_text(encoding="utf8")
    build_maps_page(content_tpl)


if __name__ == "__main__":
    main()
