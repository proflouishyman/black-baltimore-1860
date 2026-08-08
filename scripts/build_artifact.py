#!/usr/bin/env python3
"""Render every page of the site from two templates and one shared payload.

Map pages inline the full payload because they draw geometry. The occupations
page inlines only the occupation counts, and the bibliography inlines nothing,
so neither carries a megabyte of street data it never uses.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAP_TPL = ROOT / "web" / "template.html"
CONTENT_TPL = ROOT / "web" / "content.html"
PAYLOAD = ROOT / "data" / "work" / "map_payload.json"
DOCS = ROOT / "docs"

NAV = [("index.html", "Density"), ("1819.html", "1819"), ("1822.html", "1822"),
       ("1842.html", "1842"), ("1845.html", "1845"), ("1851.html", "1851"),
       ("1860.html", "1860"), ("1868.html", "1868"),
       ("wards.html", "Wards"), ("work.html", "Work"), ("trade.html", "Trade"),
       ("building.html", "Building"), ("bias.html", "What's missing"),
       ("checking.html", "Checking"),
       ("sources.html", "Sources")]

# per-year framing: eyebrow, headline, lede, and the paragraph that states the
# method and its limits honestly
YEAR_TEXT = {
    "1819": ("Jackson's Baltimore Directory", "Black Baltimore, 1819",
             "The earliest year we can map at all, and only because someone "
             "transcribed it by hand a quarter-century ago.",
             """<p class="note"><strong>This year exists here on borrowed
      labour.</strong> Jackson's 1819 directory was transcribed from the page
      by Louis S. Diggs, Sr. and published by AfriGeneas. We had no route to it
      otherwise.</p>
      <p class="note"><strong>Only 92 of 526 are placed, and that is the honest
      ceiling for now.</strong> 1819 addresses mostly say <em>near</em>
      something rather than giving a corner and a direction, and the city of
      1819 is small enough that much of its street fabric has since been
      renamed twice over.</p>"""),
    "1822": ("Keenan's Baltimore Directory", "Black Baltimore, 1822",
             "Persons of colour, marked in the original with a dagger, "
             "transcribed by hand and mapped by block face.",
             """<p class="note"><strong>Our own OCR of this book placed 8
      people.</strong> The hand transcription places 230, from 1,061 parsed
      entries against our scan's 414. Small type and dense abbreviations defeat
      the machine; a person reading the page did not have that problem.</p>
      <p class="note">Addresses give street, side and a bearing from a named
      corner (<em>Potter e side n of Pitt</em>), so these are block faces, not
      houses.</p>"""),
    "1842": ("Matchett's Baltimore Director", "Black Baltimore, 1842",
             "The “Colored Householders” section, placed by block face because "
             "the city had no house numbers yet.",
             """<p class="note"><strong>No house numbers existed yet.</strong>
      Matchett's gives directions instead: <em>Pitt st w of Ann</em>. Each
      person sits on a block face, the stretch of street between two
      intersections, never at a house.</p>
      <p class="note"><strong>Coverage is weak and not randomly so.</strong>
      The streets that fail to resolve are disproportionately the alleys:
      Strawberry, Happy, Sugar, Lerew's. They are absent even from the 1930
      survey, having been renamed or cleared before it.</p>"""),
    "1845": ("The Baltimore Directory", "Black Baltimore, 1845",
             "House numbers have arrived. The same population, now locatable "
             "to an address rather than a block.",
             """<p class="note"><strong>The turning point.</strong> Between
      1842 and 1845 Baltimore adopted house numbers, and the directory changes
      with it: <em>13 Lerew's alley</em> instead of <em>w of Gough</em>. From
      here on the anchor method works.</p>
      <p class="note">1845 prints no anchor table of its own, so it borrows
      1860's. Baltimore did not renumber until the 1880s, so the two share a
      numbering scheme, but fifteen years of infill sit between them.</p>"""),
    "1851": ("Matchett's Baltimore Director", "Black Baltimore, 1851",
             "A decade before the war, and the listed population has grown by "
             "three quarters since 1842.",
             """<p class="note">Like 1845, this volume prints no anchor table
      and borrows 1860's, nine years later. A third of its entries give no
      house number at all and cannot be placed.</p>"""),
    "1860": ("Wood's Baltimore City Directory", "Black Baltimore, 1860",
             "The fullest antebellum picture, and the one year with its own "
             "printed anchor table.",
             """<p class="note"><strong>This year is the anchor.</strong>
      Wood's prints a street directory giving the house number standing at each
      cross street, so residents are placed between two named corners in 1860's
      own numbering. The 1880s renumbering never enters the calculation.</p>
      <p class="note">Street names are matched through the 1993 Baltimore City
      Archives index of renamings, which is what lets Strawberry, Brandy, Happy
      and Honey alleys resolve at all: none of them vanished, they were
      renamed Dallas, Perry, Durham and Hughes.</p>"""),
    "1868": ("Wood's Baltimore City Directory", "Black Baltimore, 1868",
             "Three years after emancipation, the listed population has doubled.",
             """<p class="note"><strong>The largest cohort by far.</strong>
      8,512 people, against 4,251 in 1860. The section runs 64 printed pages
      where 1860's ran 31. Emancipation and wartime migration are visible in
      the page count before any analysis begins.</p>
      <p class="note">1868 prints its own anchor table, and a richer one than
      1860's: 387 streets against 215. Baltimore had also redrawn its wards in
      1861, so this year is geocoded against the later boundary.</p>"""),
}


def nav_html(current):
    out = ["<nav>"]
    for href, label in NAV:
        cur = ' aria-current="page"' if href == current else ""
        out.append(f'<a href="{"./" if href == "index.html" else "./" + href}"{cur}>{label}</a>')
    out.append("</nav>")
    return "\n    ".join(out)


def document(body, title, desc):
    doc = ("<!doctype html>\n<html lang=\"en\">\n<head>\n"
           "<meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
           f"<meta name=\"description\" content=\"{desc}\">\n"
           f"<meta property=\"og:title\" content=\"{title}\">\n"
           f"<meta property=\"og:description\" content=\"{desc}\">\n"
           "<link rel=\"icon\" href=\"data:image/svg+xml,"
           "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>"
           "<text y='14' font-size='14'>&#x1F5FA;</text></svg>\">\n" + body)
    for marker in ('<div class="wrap">', '<div class="page">'):
        if marker in doc:
            doc = doc.replace(marker, "</head>\n<body>\n" + marker, 1)
            break
    return doc + "\n</body>\n</html>"


def stat_block(cells):
    inner = "".join(
        f'<div class="stat"><div class="n mono">{n}</div><div class="k">{k}</div></div>'
        for n, k in cells)
    return f'<div class="stats">{inner}</div>'


TIER_CONTROLS = """
    <fieldset>
      <legend>Show</legend>
      <label class="row"><input type="checkbox" id="t0" checked>
        <span class="swatch" style="background:var(--anchored)"></span>
        <span><span class="lab">Anchored &mdash; %(anch)s</span><br>
          <span class="sub">%(anchdesc)s</span></span></label>
      %(tier2)s
      <label class="row"><input type="checkbox" id="tw">
        <span class="ward-key"></span>
        <span><span class="lab">Ward boundaries</span><br>
          <span class="sub">Compare against the density map.</span></span></label>
      <label class="row"><input type="checkbox" id="tm">
        <span class="swatch" style="background:var(--approx);opacity:.35"></span>
        <span><span class="lab">Baltimore today</span><br>
          <span class="sub">Today's streets and avenues, labelled and drawn
            over the top. Switch on to orient, then off. This is not the
            geometry anything is placed on.</span></span></label>
    </fieldset>
"""
TIER2 = """<label class="row"><input type="checkbox" id="t2" checked>
        <span class="swatch" style="background:var(--approx)"></span>
        <span><span class="lab">Street&nbsp;only &mdash; %(approx)s</span><br>
          <span class="sub">Street known, position along it estimated.</span></span></label>"""


TRADE_PANEL = '\n    <div class="years" id="cyears" style="display:flex;gap:6px;margin-bottom:2px">\n      <button data-year="1842" aria-pressed="false">1842</button>\n      <button data-year="1845" aria-pressed="false">1845</button>\n      <button data-year="1851" aria-pressed="false">1851</button>\n      <button data-year="1860" aria-pressed="true">1860</button>\n      <button data-year="1868" aria-pressed="false">1868</button>\n    </div>\n\n    <fieldset>\n      <legend>Show</legend>\n      <label class="row"><input type="checkbox" id="tb" checked>\n        <span class="swatch" style="background:var(--anchored)"></span>\n        <span><span class="lab">Businesses</span><br>\n          <span class="sub">Proprietors, not employees: grocers, eating houses,\n            barbers, hucksters, boarding houses.</span></span></label>\n      <label class="row"><input type="checkbox" id="ti" checked>\n        <span class="swatch" style="background:var(--approx)"></span>\n        <span><span class="lab">Institutions</span><br>\n          <span class="sub">Churches, schools, lodges.</span></span></label>\n      <label class="row"><input type="checkbox" id="tw">\n        <span class="ward-key"></span>\n        <span><span class="lab">Ward boundaries</span></span></label>\n      <label class="row"><input type="checkbox" id="tm">\n        <span class="swatch" style="background:var(--approx);opacity:.35"></span>\n        <span><span class="lab">Baltimore today</span><br>\n          <span class="sub">Switch on to orient, then off.</span></span></label>\n    </fieldset>\n\n    <p class="note"><strong>Ownership, not just labour.</strong> The directories\n      do not separate a Black church, a Black-run eating house and a Black\n      labourer &mdash; all three sit in the same alphabetical list. Pulling the\n      first two out turns a map of where people were made to live into a map of\n      what they built there.</p>\n\n    <p class="note"><strong>These counts are floors.</strong> Businesses are\n      identified from occupation strings, so a proprietor described only as\n      &ldquo;grocer&rdquo; is caught and one described as &ldquo;works at\n      Smith&rsquo;s&rdquo; is not. Institutions are worse: only a handful\n      geocode, because directories give them corner addresses\n      (&ldquo;Sharp near Pratt&rdquo;) with no house number. Sharp Street\n      Methodist, Ebenezer, Israel Church, Asbury, Good Hope Lodge and the\n      Douglass Institute are all in the parsed data even where they are not on\n      this map.</p>\n'
BUILDING_PANEL = '\n    <fieldset>\n      <legend>Value assessed, 1869</legend>\n      <div class="ramp"><div style="background:var(--c1)"></div>\n        <div style="background:var(--c2)"></div><div style="background:var(--c3)"></div>\n        <div style="background:var(--c4)"></div><div style="background:var(--c5)"></div></div>\n      <div class="ramp-lab"><span>under $100k</span><span>over $600k</span></div>\n    </fieldset>\n\n    <fieldset>\n      <legend>Overlay</legend>\n      <label class="row"><input type="checkbox" id="tm">\n        <span class="swatch" style="background:var(--approx);opacity:.35"></span>\n        <span><span class="lab">Baltimore today</span><br>\n          <span class="sub">Switch on to orient, then off.</span></span></label>\n    </fieldset>\n\n    <p class="note"><strong>Where the money was going.</strong> Every other ward\n      series here is about who lived where. This one is about where Baltimore\n      was building. The city assessed $6,615,275 of new dwellings and\n      improvements in 1869, across 2,836 dwellings, and it was not spread\n      evenly: ward 12 saw $825,050 and ward 5 saw $39,900, a twentyfold gap.</p>\n\n    <p class="note"><strong>Compare it against 1868, not against the census\n      choropleth.</strong> These are the 1861&ndash;1882 wards, a different\n      division of the city from the twenty wards of 1850 and 1860. Ward 7 here\n      is not ward 7 there. The 1868 residents map uses this same boundary set,\n      one year apart, so that is the honest pairing.</p>\n'


def build_maps(map_tpl, payload_txt, data):
    density_panel = (
        """
    <div class="years" id="cyears" style="display:flex;gap:6px;margin-bottom:2px">
      <button data-year="1820" aria-pressed="false">1820</button>
      <button data-year="1850" aria-pressed="false">1850</button>
      <button data-year="1860" aria-pressed="true">1860</button>
    </div>
""" +
        stat_block([("23.4%", "Black share, 1820"),
                    ("16.8%", "Black share, 1850"),
                    ("13.1%", "Black share, 1860"),
                    ("20 of 20", "Wards falling, 1850&ndash;60")]) +
        """
    <fieldset>
      <legend>Black share of ward population</legend>
      <div class="ramp"><div style="background:var(--c1)"></div>
        <div style="background:var(--c2)"></div><div style="background:var(--c3)"></div>
        <div style="background:var(--c4)"></div><div style="background:var(--c5)"></div></div>
      <div class="ramp-lab"><span>under 5%</span><span>over 21%</span></div>
    </fieldset>

    <fieldset>
      <legend>Overlay</legend>
      <label class="row"><input type="checkbox" id="tm">
        <span class="swatch" style="background:var(--approx);opacity:.35"></span>
        <span><span class="lab">Baltimore today</span><br>
          <span class="sub">Today's streets and avenues, labelled and drawn
            over the top. Switch on to orient, then off. This is not the
            geometry anything is placed on.</span></span></label>
    </fieldset>

    <p class="note"><strong>Forty years, one direction.</strong> Black
      Baltimore was 23.4 per cent of the city in 1820, 16.8 in 1850, 13.1 in
      1860. The 1820 map uses the twelve wards then in force, which are a
      different division of the city from the twenty wards of 1850 and 1860 —
      so read 1820 against the others as a distribution, not ward by ward.</p>
    <p class="note"><strong>1850 and 1860 share the same ward boundaries</strong>,
      so that comparison is exact. The
      Black share of the city fell in <em>every one of the twenty wards</em>.
      Not because Black Baltimore shrank much &mdash; it fell by 490 people,
      under 2 per cent &mdash; but because 43,854 white residents arrived,
      mostly German and Irish, and the denominator exploded beneath a
      population that was standing still.</p>
    <p class="note">The enslaved population fell faster, 2,946 to 2,218. Wards
      11 and 14 barely moved, holding their share within a fifth of a point:
      those are the neighbourhoods that persisted. Ward 17 lost ten points.</p>
    <p class="note"><strong>This is the whole population, not a sample.</strong>
      Every person the census counted, free and enslaved, by ward. The year
      maps show named individuals, but only those a directory chose to list,
      which was never everyone.</p>
    <p class="note">Baltimore held the largest free Black population of any
      American city. The enslaved were 1&nbsp;per&nbsp;cent of the city and
      cannot be mapped more finely: they appear under an owner's name, with no
      address of their own.</p>""")

    pages = [("index.html", "density", "Fourth, Seventh and Eighth Censuses",
              "Where Black Baltimore lived",
              "The whole city by ward, free and enslaved, across forty years \u2014 "
              "1820, 1850 and 1860.",
              density_panel)]

    for y in ["1819", "1822", "1842", "1845", "1851", "1860", "1868"]:
        eyebrow, h1, lede, notes = YEAR_TEXT[y]
        rows = data["people"].get(y, [])
        anch = sum(1 for r in rows if r[2] != 2)
        approx = len(rows) - anch
        parsed = data["parsed"].get(y, 0)
        block = TIER_CONTROLS % {
            "anch": f"{anch:,}",
            "anchdesc": ("Placed on a block face, or at a named corner."
                         if y in ("1819", "1822", "1842") else
                         "Placed between two named corners using printed house numbers."),
            "tier2": (TIER2 % {"approx": f"{approx:,}"}) if approx else "",
        }
        panel = stat_block([(f"{parsed:,}", "Listed"), (f"{len(rows):,}", "Placed"),
                            (f"{anch:,}", "Anchored"),
                            (f"{round(len(rows)/parsed*100) if parsed else 0}%", "Placed rate")])
        pages.append((f"{y}.html", y, eyebrow, h1, lede, panel + block + notes))

    pages.append(("trade.html", "trade", "Directories, 1842\u20131868",
                  "What Black Baltimore built",
                  "Black-owned businesses and Black institutions, pulled out of "
                  "the residential listings they were buried in.",
                  TRADE_PANEL))
    pages.append(("building.html", "building", "Mayor's Message, 1869",
                  "Where Baltimore was building, 1869",
                  "New dwellings and improvements assessed by ward, the year "
                  "after the last directory on this site.",
                  BUILDING_PANEL))

    for fname, mode, eyebrow, h1, lede, panel in pages:
        body = (map_tpl
                .replace("__TITLE__", f"{h1} — Black Baltimore")
                .replace("__NAV__", nav_html(fname))
                .replace("__EYEBROW__", eyebrow).replace("__H1__", h1)
                .replace("__LEDE__", lede).replace("__PANEL__", panel)
                .replace("__MODE__", mode)
                .replace("__PAYLOAD__", payload_txt))
        (DOCS / fname).write_text(document(body, h1, lede), encoding="utf8")
        print(f"wrote docs/{fname} ({(DOCS/fname).stat().st_size/1_000_000:.2f} MB)")


WORK_SCRIPT = """
<script id="occ" type="application/json">__OCC__</script>
<script>
(function () {
  var D = JSON.parse(document.getElementById('occ').textContent);
  var years = Object.keys(D.occupations).sort();
  var cur = '1860';
  var btns = document.getElementById('years'), chart = document.getElementById('chart');
  var caption = document.getElementById('cap');

  years.forEach(function (y) {
    var b = document.createElement('button');
    b.textContent = y; b.setAttribute('aria-pressed', y === cur);
    b.onclick = function () { cur = y; render(); };
    btns.appendChild(b);
  });

  function render() {
    Array.prototype.forEach.call(btns.children, function (b) {
      b.setAttribute('aria-pressed', b.textContent === cur);
    });
    var rows = (D.occupations[cur] || []).slice(0, 18);
    var max = rows.length ? rows[0][1] : 1;
    var listed = D.parsed[cur] || 0;
    var withOcc = (D.occupations[cur] || []).reduce(function (a, r) { return a + r[1]; }, 0);
    chart.innerHTML = '';
    rows.forEach(function (r) {
      var lab = document.createElement('div'); lab.className = 'lab'; lab.textContent = r[0];
      var track = document.createElement('div'); track.className = 'track';
      var fill = document.createElement('div'); fill.className = 'fill';
      fill.style.width = Math.max(2, r[1] / max * 100) + '%';
      track.appendChild(fill);
      var val = document.createElement('div'); val.className = 'val';
      val.textContent = r[1].toLocaleString();
      chart.appendChild(lab); chart.appendChild(track); chart.appendChild(val);
    });
    caption.textContent = 'Top occupations among ' + withOcc.toLocaleString() +
      ' of the ' + listed.toLocaleString() + ' people listed in ' + cur +
      '. The rest give no occupation, which the directories record unevenly ' +
      'and omit far more often for women.';
  }
  render();
})();
</script>
"""


def build_work(content_tpl, data):
    occ_payload = json.dumps({"occupations": data["occupations"],
                              "parsed": data["parsed"]}, separators=(",", ":"))
    body_content = """
  <div class="years" id="years"></div>
  <div class="chart" id="chart"></div>
  <p class="note" id="cap"></p>

  <h2>What the work tells you</h2>
  <p>These are the trades of a population barred from most others. Laborer,
    laundress, drayman, carter, waiter, porter: hauling, washing, serving. The
    directories list occupations unevenly, and omit them far more often for
    women than for men, so the counts understate women's work badly. A woman
    listed with no trade is not a woman who did not work.</p>
  <p>Read across the years and the shape shifts. The maritime trades &mdash;
    caulker, sailor, stevedore, oysterman &mdash; sit close to Fells Point on
    the maps, which is why the dots cluster there. Watch what happens to the
    totals in 1868.</p>

  <h2>Caveats worth stating</h2>
  <p>Occupation strings come from OCR of nineteenth-century type, so spellings
    are folded together by rule (<span class="mono">labourer</span>,
    <span class="mono">iaborer</span> and <span class="mono">labr</span> all
    become <span class="mono">laborer</span>). Entries longer than a few words
    are dropped, because those are usually an address that leaked into the
    field rather than a trade.</p>
  <p>These counts use every parsed record, not only the ones we could place on
    a map, so they cover more people than the year maps do.</p>
"""
    body = (content_tpl
            .replace("__TITLE__", "Work — Black Baltimore")
            .replace("__NAV__", nav_html("work.html"))
            .replace("__EYEBROW__", "Occupations, 1842–1868")
            .replace("__H1__", "How Black Baltimore worked")
            .replace("__LEDE__", "Every occupation the directories recorded, "
                                 "across five volumes and twenty-six years.")
            .replace("__CONTENT__", body_content)
            .replace("__SCRIPT__", WORK_SCRIPT.replace("__OCC__", occ_payload)))
    desc = "Occupations of Black Baltimoreans recorded in city directories, 1842-1868."
    (DOCS / "work.html").write_text(document(body, "How Black Baltimore worked", desc),
                                    encoding="utf8")
    print(f"wrote docs/work.html ({(DOCS/'work.html').stat().st_size/1_000:.0f} KB)")


BIB = [
    ("The Baltimore Directory for 1822", "Richard J. Matchett (Keenan), 1822",
     "https://archive.org/details/baltimoredirecto1822keen",
     "img/1822_f_marker.jpg",
     "No separate section. Instead a dagger (&dagger;) precedes certain names "
     "&mdash; 360 of them &mdash; which the OCR renders variously as "
     "<span class=\"mono\">f</span> or <span class=\"mono\">t</span>. "
     "<strong>The meaning is inferred, not stated:</strong> this scan's "
     "&ldquo;Directions to the Reader&rdquo; page, which would carry the "
     "legend, is not legible. The reading rests on the flagged entries' "
     "occupations (laundress, labourer, drayman, bootblack), their "
     "concentration in the alleys, and at least one that is also described "
     "outright as <em>coloured</em>. Treat it as a strong inference pending "
     "a clean copy of that page. Note also that trailing "
     "<span class=\"mono\">f. p.</span> and <span class=\"mono\">o. t.</span> "
     "mark Fell's Point and Old Town, not race. Only 8 of this volume's "
     "addresses resolve, so it is parsed but not mapped.",
     "414 residents parsed, 360 flagged"),
    ("Jackson's Baltimore Directory, 1819 — AfriGeneas transcription",
     "Transcribed by Louis S. Diggs, Sr., 1998",
     "https://www.afrigeneas.org/library/baltimore/1819.html", None,
     "A hand transcription of the &ldquo;Colored Householders&rdquo; from "
     "Jackson's 1819 directory, giving name, occupation and address. Without "
     "it this year would not appear here at all. Addresses are mostly of the "
     "form <span class=\"mono\">near Bank st</span>, so they place to a "
     "corner rather than a block face.",
     "526 residents parsed, 92 placed"),
    ("Keenan's Baltimore Directory 1822-23 — AfriGeneas transcription",
     "Transcribed by Louis S. Diggs, Sr., 2000",
     "https://afrigeneas.org/library/baltimore/1822-23.html", None,
     "The same volume our own OCR handled badly, read properly by a person. "
     "It yields 1,061 entries against our scan's 414, and 230 placed against "
     "8. The transcriber's closing note is worth quoting: &ldquo;My poor eyes "
     "got tired of trying to read those little &lsquo;N side W of whatever "
     "street.&rsquo;&rdquo;",
     "1,061 residents parsed, 230 placed"),
    ("Matchett's Baltimore Director", "1842",
     "https://archive.org/details/matchettsbaltimo1842balt",
     "img/1842_colored_householders.jpg",
     "Prints a separate “Colored Householders” section with a note at the front "
     "that they are listed “by themselves.” Addresses are relative, not "
     "numbered. Its appendix also carries the full ward ordinance, with "
     "boundaries described by street centre lines.",
     "2,724 residents parsed"),
    ("The Baltimore Directory", "1845",
     "https://archive.org/details/baltimoredirecto1845balt", None,
     "The first of these volumes with house numbers. Same segregated section, "
     "now giving addresses like <span class=\"mono\">13 Lerew's alley</span>.",
     "2,100 residents parsed"),
    ("Matchett's Baltimore Director", "1851",
     "https://archive.org/details/matchettsbaltimo1851balt", None,
     "Section closes with an explicit <span class=\"mono\">END COLORED "
     "RESIDENTS</span>, which is what bounds the parse. Also prints the 1851 "
     "ward division law.",
     "3,642 residents parsed"),
    ("Wood's Baltimore City Directory", "John W. Woods, 1860",
     "https://archive.org/details/woodsbaltimoreci1860balt",
     "img/1860_colored_persons.jpg",
     "The “Colored Persons” section, 31 printed pages beginning at p. 427, "
     "giving name, occupation and address for each resident. The backbone of "
     "the project.",
     "4,251 residents parsed"),
    ("Wood's Baltimore City Directory — Street Directory", "1860, pp. 509–529",
     "https://archive.org/details/woodsbaltimoreci1860balt",
     "img/1860_street_directory.jpg",
     "The key that makes address-level geocoding possible. For every street it "
     "prints the house number standing at each cross street, in Left and Right "
     "columns, so an 1860 number can be placed between two named corners "
     "without ever being compared to a modern one. The flat OCR destroys this "
     "table; it is rebuilt from per-word coordinates.",
     "1,521 anchors across 215 streets"),
    ("Wood's Baltimore City Directory", "1868",
     "https://archive.org/details/woodsbaltimoreci1868balt",
     "img/1868_colored_persons.jpg",
     "Three years after emancipation. The section runs 64 pages where 1860's "
     "ran 31, and lists twice as many people. Its own street directory is "
     "richer than 1860's, covering 387 streets.",
     "8,512 residents parsed"),
    ("Population of the United States in 1860", "Eighth Census, Table No. 3, p. 214",
     "https://www2.census.gov/library/publications/decennial/1860/population/1860a-18.pdf",
     None,
     "Baltimore ward by ward, with white, free colored and slave counts. The "
     "only ward-level race breakdown available for 1860: IPUMS does not "
     "distribute ward geography in its public complete count. Transcribed from "
     "the scan and checked against the printed totals, which reconcile exactly.",
     "20 wards; 25,680 free Black, 2,218 enslaved"),
    ("Index of Streets and Alleys", "Gunby, Baltimore City Archives, 1993",
     "https://msa.maryland.gov/megafile/msa/speccol/sc5300/sc5339/000097/000000/000017/unrestricted/gunby-bc-streets-1993.pdf",
     None,
     "A card index of every Baltimore street renaming, and the fix for this "
     "project's largest source of silent loss. The streets that failed to "
     "geocode were overwhelmingly the alleys the Black population lived on, "
     "and most had not been demolished at all &mdash; they were renamed. "
     "Strawberry became Dallas, Brandy became Perry, Bottle became Dover, "
     "Happy became Durham, Honey became Hughes, German became Redwood. "
     "1,460 alias pairs extracted.",
     "1,460 name changes; lifted 1822 from 8 placed to 230"),
    ("Population of the United States in 1850", "Seventh Census, Table II, Maryland report p. 221",
     "https://www2.census.gov/library/publications/decennial/1850/1850a/1850-census-report-maryland.pdf",
     None,
     "Baltimore by ward, on the same model as 1860 and on the same ward "
     "boundaries, which makes the two directly comparable. Unlike the 1860 "
     "volume this PDF carries a text layer. Checked against the printed "
     "totals, which reconcile exactly, and that check corrected ward 20's "
     "enslaved count.",
     "20 wards; 25,442 free Black, 2,946 enslaved"),
    ("Historical Urban Ecological (HUE) Data", "Center for Population Economics, ICPSR 35617",
     "https://www.icpsr.umich.edu/web/ICPSR/studies/35617", None,
     "Baltimore street centrelines c.1930 and ward boundaries in period "
     "slices. Chosen over modern street data for one reason: it still carries "
     "the alleys &mdash; Camel, Pin, Welcome &mdash; where much of this "
     "population lived and which modern data has lost.",
     "20,459 street segments; ward layers 1818–1930"),
]


def build_sources(content_tpl):
    parts = ["""
  <p>Every figure on this site comes from one of the documents below. All are
    public and linked. Where a page image is shown, it is the actual page the
    data was read from.</p>

  <div class="note"><strong>On the language.</strong> The section headings
    quoted here &mdash; “Colored Persons,” “Colored Householders” &mdash; are
    the directories' own. They are reproduced because they are what makes this
    project possible: the publishers segregated these residents into separate
    lists, and that act of separation is why they can be identified and counted
    today. The words are theirs, not ours.</div>
"""]
    for title, meta, url, img, desc, yield_ in BIB:
        fig = (f'<figure><img src="{img}" alt="Page from {title}" loading="lazy">'
               f'<figcaption>{title}, {meta}.</figcaption></figure>') if img else ""
        parts.append(f"""
  <div class="biblio">
    <h3>{title}</h3>
    <p class="meta">{meta} &middot; <a href="{url}">view the original</a></p>
    <p>{desc}</p>
    <p class="mono" style="color:var(--approx);font-size:12.5px">{yield_}</p>
    {fig}
  </div>""")

    parts.append("""
  <h2>Method and code</h2>
  <p>Every step is scripted and the repository is public:
    <a href="https://github.com/proflouishyman/black-baltimore-1860">github.com/proflouishyman/black-baltimore-1860</a>.
    It includes the parsers, the geocoders, the transcription check on the
    census table, and a log of every bug found and what caused it.</p>""")

    body = (content_tpl
            .replace("__TITLE__", "Sources — Black Baltimore")
            .replace("__NAV__", nav_html("sources.html"))
            .replace("__EYEBROW__", "Bibliography")
            .replace("__H1__", "Where all of this comes from")
            .replace("__LEDE__", "Nine primary sources, spanning 1822 to 1868, "
                                 "each linked to the original scan.")
            .replace("__CONTENT__", "\n".join(parts))
            .replace("__SCRIPT__", ""))
    desc = "Primary sources behind the Black Baltimore mapping project, 1822-1868."
    (DOCS / "sources.html").write_text(document(body, "Where all of this comes from", desc),
                                       encoding="utf8")
    print(f"wrote docs/sources.html ({(DOCS/'sources.html').stat().st_size/1_000:.0f} KB)")


WARDS_SCRIPT = """
<script id="wd" type="application/json">__WARDS__</script>
<script>
(function () {
  var D = JSON.parse(document.getElementById('wd').textContent);
  var tb = document.getElementById('wbody'), hr = document.getElementById('whead');
  var sortKey = 'ward', asc = true;
  var COLS = [
    {k:'ward',  t:'Ward',             n:false},
    {k:'fc50',  t:'Free Black 1850',  n:true},
    {k:'sl50',  t:'Enslaved 1850',    n:true},
    {k:'pct50', t:'Black % 1850',     n:true},
    {k:'fc60',  t:'Free Black 1860',  n:true},
    {k:'sl60',  t:'Enslaved 1860',    n:true},
    {k:'pct60', t:'Black % 1860',     n:true},
    {k:'dpct',  t:'Change',           n:true},
    {k:'agg60', t:'Ward total 1860',  n:true}
  ];
  var max = Math.max.apply(null, D.map(function (r) { return r.pct60; }));

  function render() {
    var rows = D.slice().sort(function (a, b) {
      var x = a[sortKey], y = b[sortKey];
      return (x === y ? 0 : (x > y ? 1 : -1)) * (asc ? 1 : -1);
    });
    tb.innerHTML = '';
    rows.forEach(function (r) {
      var tr = document.createElement('tr');
      COLS.forEach(function (c) {
        var td = document.createElement('td'), v = r[c.k];
        if (c.k === 'pct50' || c.k === 'pct60') {
          td.className = 'n bar';
          td.innerHTML = '<span class="bw" style="width:' + (v / max * 100).toFixed(1) +
            '%"></span><span class="bv">' + v.toFixed(2) + '%</span>';
        } else if (c.k === 'dpct') {
          td.className = 'n';
          td.textContent = (v > 0 ? '+' : '') + v.toFixed(2);
          if (v < -5) td.style.color = 'var(--anchored)';
        } else {
          td.className = c.n ? 'n' : '';
          td.textContent = c.n ? v.toLocaleString() : v;
        }
        tr.appendChild(td);
      });
      tb.appendChild(tr);
    });
  }

  COLS.forEach(function (c) {
    var th = document.createElement('th');
    th.className = c.n ? 'n' : '';
    th.textContent = c.t;
    th.tabIndex = 0;
    th.setAttribute('role', 'button');
    function go() {
      if (sortKey === c.k) { asc = !asc; } else { sortKey = c.k; asc = (c.k === 'ward'); }
      Array.prototype.forEach.call(hr.children, function (o) { o.removeAttribute('aria-sort'); });
      th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
      render();
    }
    th.onclick = go;
    th.onkeydown = function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
    };
    hr.appendChild(th);
  });
  render();
})();
</script>
"""

WARDS_BODY = """
  <p>Both censuses used the same twenty wards, so this is a like-for-like
    comparison. Click any column to sort. <em>Change</em> is the shift in Black
    share between the two years, in percentage points.</p>

  <div class="scroll">
    <table class="data" id="wtab">
      <thead><tr id="whead"></tr></thead>
      <tbody id="wbody"></tbody>
    </table>
  </div>

  <h2>What to notice</h2>
  <p>Sort by <em>Change</em> and the pattern is unmistakable: every ward moved
    the same direction. Not one of the twenty gained Black share between 1850
    and 1860. That is not a story about Black Baltimore leaving. The Black
    population fell by 490 people, under two per cent. It is a story about
    43,854 white arrivals, largely German and Irish, landing on top of a
    population that was standing still.</p>
  <p>Sort by <em>Black&nbsp;% 1860</em> and wards 11, 15 and 12 sit at the top,
    the same wards that top 1850. Sort by <em>Change</em> and wards 11 and 14
    sit at the bottom of the movement, having shifted by a fifth of a point.
    Those are the neighbourhoods that held. Ward 17 lost ten points, the
    largest single change in the city.</p>
  <p>The enslaved columns carry their own story: 2,946 people in 1850 down to
    2,218 in 1860, a quarter gone in a decade, in a city where free Black
    residents already outnumbered them more than eleven to one.</p>

  <h2>Provenance</h2>
  <p>1850 from the Seventh Census, Table II of the Maryland report,
    p.&nbsp;221. 1860 from the Eighth Census, Table No.&nbsp;3, p.&nbsp;214.
    Both were transcribed from the page and checked by summing every column
    against the printed city totals. Both reconcile exactly, and the check
    caught a real error in each: a misread white female count in 1860 ward 1,
    and an enslaved count in 1850 ward 20.</p>
"""


def build_checking(content_tpl):
    import json as _json
    v = (ROOT / "data" / "work" / "validation_summary.json")
    if not v.exists():
        return
    data = _json.loads(v.read_text(encoding="utf8"))
    slim = {"tiers": data["tiers"], "total": data["total"]}
    body = (content_tpl
            .replace("__TITLE__", "Checking the map \u2014 Black Baltimore")
            .replace("__NAV__", nav_html("checking.html"))
            .replace("__EYEBROW__", "Validation against the 1860 census")
            .replace("__H1__", "Checking the map")
            .replace("__LEDE__", "We looked people up in the census to see whether "
                                 "we had put them in the right place. Here is what "
                                 "that found, including the bugs.")
            .replace("__CONTENT__", VAL_BODY)
            .replace("__SCRIPT__", VAL_SCRIPT.replace("__VAL__",
                     _json.dumps(slim, separators=(",", ":")))))
    desc = ("Validating a historical geocode against the 1860 census: method, "
            "error rates, and the bugs it exposed.")
    (DOCS / "checking.html").write_text(document(body, "Checking the map", desc),
                                        encoding="utf8")
    print(f"wrote docs/checking.html ({(DOCS/'checking.html').stat().st_size/1_000:.0f} KB)")


VAL_SCRIPT = '\n<script id="vd" type="application/json">__VAL__</script>\n<script>\n(function () {\n  var D = JSON.parse(document.getElementById(\'vd\').textContent);\n  var order = [\'bracketed\', \'single_anchor\', \'extrapolated\', \'street_proportional\'];\n  var label = {bracketed: \'Anchored between two named corners\',\n               single_anchor: \'One anchor only\',\n               extrapolated: \'Beyond the anchored range\',\n               street_proportional: \'Street known, position estimated\',\n               unknown: \'Tier not recorded\'};\n  var tb = document.getElementById(\'vbody\');\n  var keys = order.filter(function (k) { return D.tiers[k]; })\n    .concat(Object.keys(D.tiers).filter(function (k) { return order.indexOf(k) < 0; }));\n  keys.forEach(function (k) {\n    var v = D.tiers[k], tr = document.createElement(\'tr\');\n    var rate = v.ward ? (v.match / v.ward * 100).toFixed(0) + \'%\' : \'\\u2014\';\n    [[label[k] || k, false], [v.n, true], [v.found, true], [v.ward, true],\n     [v.match, true], [rate, true]].forEach(function (c) {\n      var td = document.createElement(\'td\');\n      td.className = c[1] ? \'n\' : \'\';\n      td.textContent = c[0];\n      tr.appendChild(td);\n    });\n    tb.appendChild(tr);\n  });\n  var t = D.total, mism = t.ward - t.match;\n  document.getElementById(\'vtot\').textContent =\n    t.found + \' of \' + t.n + \' traced (\' + (t.found / t.n * 100).toFixed(0) + \'%)\';\n  document.getElementById(\'vmatch\').textContent =\n    t.match + \' of \' + t.ward + \' wards agree\';\n  document.getElementById(\'vadj\').textContent =\n    mism ? t.adjacent + \' of \' + mism + \' misses adjacent\' : \'no misses\';\n})();\n</script>\n'
VAL_BODY = '\n  <div class="note"><strong>Nobody had checked whether any of this was\n    right.</strong> So we started looking people up in the 1860 federal census,\n    which recorded each person\'s ward independently of anything we did. If our\n    placements are sound, the wards should agree.</div>\n\n  <div class="scroll">\n    <table class="data">\n      <thead><tr>\n        <th>Placement method</th><th class="n">Checked</th><th class="n">Traced</th>\n        <th class="n">Ward known</th><th class="n">Agree</th><th class="n">Rate</th>\n      </tr></thead>\n      <tbody id="vbody"></tbody>\n    </table>\n  </div>\n  <p class="note"><span id="vtot"></span> &middot; <span id="vmatch"></span>\n    &middot; <span id="vadj"></span></p>\n\n  <h2>It found real bugs</h2>\n  <p>The first eight lookups matched on only one of three traceable people. That\n    was not noise. It exposed two faults in the highest-confidence placements.</p>\n  <p><strong>Split streets shared one ladder.</strong> North Charles and South\n    Charles both reduce to &ldquo;Charles&rdquo;, so one silently overwrote the\n    other and their geometry fused. Thirty-four street names were affected,\n    covering 473 of our best placements. Someone on the north half could be\n    interpolated onto the south half.</p>\n  <p><strong>Some streets are drawn backwards.</strong> On North Caroline the\n    digitised line runs north to south while the house numbers run south to\n    north. The code assumed numbers rise with distance, so it discarded every\n    anchor but the first and pinned people at the wrong end of the street.</p>\n  <p>Both are fixed. Nothing internal to the data would have revealed either:\n    the ladders were monotone, the anchors were real, and the output looked\n    entirely plausible.</p>\n\n  <h2>When we are wrong, we are wrong by one ward</h2>\n  <p>This is the reassuring part. <strong>Every mismatch found so far is an\n    adjacent ward</strong> &mdash; boundary distance zero, computed from the\n    ward polygons rather than judged by eye. Not one person has been placed\n    across the city from where the census puts them. The errors look like\n    boundary ambiguity, which is what you would expect when a house sits near a\n    ward line, rather than broken geocoding.</p>\n\n  <h2>The real problem is not accuracy</h2>\n  <p>It is that most people cannot be checked at all. Roughly two thirds of\n    those we look for cannot be positively identified in the census, even with\n    occupation and race filters and generous spelling variants.</p>\n  <p>That is not evidence of bad placement. It is the same gap the\n    <a href="./bias.html">bias page</a> measures from the other direction: the\n    directories and the census are two partial views of the same population,\n    and the people who fall between them are disproportionately the poorest and\n    most mobile. It does mean our confidence rests on a small, self-selected\n    subset &mdash; people distinctive enough to trace &mdash; and cannot be\n    extended to the majority we cannot verify either way.</p>\n\n  <h2>How a match is decided</h2>\n  <p>A name alone is not enough. There were two John Ashtons in 1860 Baltimore:\n    a White printer in the ward we predicted, and a Mulatto drayman in a\n    different one. Matching on ward agreement would have produced a confident,\n    wrong link that made our method look better than it is. Matches require\n    occupation or race corroboration, and identification is done before the\n    wards are compared.</p>\n  <p>Every record consulted is kept &mdash; the matches, the rejected\n    candidates, and the search results showing what the alternatives were. A\n    claim about a person in 1860 that cannot be traced back to the page it came\n    from is not worth making.</p>\n'


def build_bias(content_tpl):
    bias = (ROOT / "data" / "work" / "directory_bias_1860.json").read_text(encoding="utf8")
    body = (content_tpl
            .replace("__TITLE__", "What's missing \u2014 Black Baltimore")
            .replace("__NAV__", nav_html("bias.html"))
            .replace("__EYEBROW__", "Directory bias, measured")
            .replace("__H1__", "What the maps miss")
            .replace("__LEDE__", "The dot maps show who a directory chose to "
                                 "list. Here is exactly how that choice was skewed, "
                                 "measured against the census.")
            .replace("__CONTENT__", BIAS_BODY)
            .replace("__SCRIPT__", BIAS_SCRIPT.replace("__BIAS__", bias)))
    desc = ("How far the Baltimore city directories under-represent the densest "
            "Black wards, measured against the 1860 census.")
    (DOCS / "bias.html").write_text(document(body, "What the maps miss", desc),
                                    encoding="utf8")
    print(f"wrote docs/bias.html ({(DOCS/'bias.html').stat().st_size/1_000:.0f} KB)")


BIAS_SCRIPT = '\n<script id="bd" type="application/json">__BIAS__</script>\n<script>\n(function () {\n  var D = JSON.parse(document.getElementById(\'bd\').textContent);\n  var tb = document.getElementById(\'bbody\'), hr = document.getElementById(\'bhead\');\n  var key = \'rep\', asc = true;\n  var COLS = [\n    {k:\'ward\',      t:\'Ward\',                    n:false},\n    {k:\'cen_n\',     t:\'Black residents (census)\', n:true},\n    {k:\'cen_pct\',   t:\'Share of Black city\',      n:true},\n    {k:\'dir_n\',     t:\'On our map\',               n:true},\n    {k:\'dir_pct\',   t:\'Share of our map\',         n:true},\n    {k:\'rep\',       t:\'Representation\',           n:true},\n    {k:\'bracketed\', t:\'Best-anchored %\',          n:true}\n  ];\n  function render() {\n    var rows = D.slice().sort(function (a, b) {\n      var x = a[key], y = b[key];\n      return (x === y ? 0 : (x > y ? 1 : -1)) * (asc ? 1 : -1);\n    });\n    tb.innerHTML = \'\';\n    rows.forEach(function (r) {\n      var tr = document.createElement(\'tr\');\n      COLS.forEach(function (c) {\n        var td = document.createElement(\'td\'), v = r[c.k];\n        td.className = c.n ? \'n\' : \'\';\n        if (c.k === \'rep\') {\n          td.textContent = v.toFixed(2) + \'\\u00d7\';\n          if (v < 0.7) { td.style.color = \'var(--anchored)\'; td.style.fontWeight = \'600\'; }\n          else if (v > 1.4) { td.style.color = \'var(--approx)\'; td.style.fontWeight = \'600\'; }\n        } else if (c.k === \'cen_pct\' || c.k === \'dir_pct\') {\n          td.textContent = v.toFixed(1) + \'%\';\n        } else if (c.k === \'bracketed\') {\n          td.textContent = v + \'%\';\n        } else {\n          td.textContent = c.n ? v.toLocaleString() : v;\n        }\n        tr.appendChild(td);\n      });\n      tb.appendChild(tr);\n    });\n  }\n  COLS.forEach(function (c) {\n    var th = document.createElement(\'th\');\n    th.className = c.n ? \'n\' : \'\'; th.textContent = c.t;\n    th.tabIndex = 0; th.setAttribute(\'role\', \'button\');\n    function go() {\n      if (key === c.k) { asc = !asc; } else { key = c.k; asc = (c.k === \'ward\'); }\n      Array.prototype.forEach.call(hr.children, function (o) { o.removeAttribute(\'aria-sort\'); });\n      th.setAttribute(\'aria-sort\', asc ? \'ascending\' : \'descending\');\n      render();\n    }\n    th.onclick = go;\n    th.onkeydown = function (e) { if (e.key === \'Enter\' || e.key === \' \') { e.preventDefault(); go(); } };\n    hr.appendChild(th);\n  });\n  render();\n})();\n</script>\n'
BIAS_BODY = '\n  <div class="note"><strong>Read this before trusting any dot map on this\n    site.</strong> The maps show people a directory chose to list. That choice\n    was not random, and we can now measure exactly how it was skewed.</div>\n\n  <h2>The measurement</h2>\n  <p>The 1860 census counted every Black Baltimorean by ward. Our 1860 map shows\n    2,939 of them. Comparing the two distributions gives a\n    <em>representation index</em>: 1.00 means a ward appears on our map at\n    exactly its true weight, 0.50 means it appears at half.</p>\n\n  <div class="scroll">\n    <table class="data" id="btab">\n      <thead><tr id="bhead"></tr></thead>\n      <tbody id="bbody"></tbody>\n    </table>\n  </div>\n\n  <h2>What it says</h2>\n  <p><strong>The map is worst exactly where Black Baltimore was densest.</strong>\n    Ward 11 held 9.8 per cent of the city\'s Black population &mdash; more than\n    any other ward &mdash; and appears on our map at <strong>0.46&times;</strong>\n    its true weight. Ward 3 held 6.7 per cent and appears at\n    <strong>1.95&times;</strong>. A viewer reading the 1860 map without this\n    table would conclude Ward 3 was a bigger centre of Black life than Ward 11.\n    The census says the opposite.</p>\n\n  <p><strong>And the error is not random noise.</strong> Sort by\n    <em>Best-anchored&nbsp;%</em> &mdash; the share of each ward\'s residents we\n    could place precisely between two named corners. Ward 3 is 95 per cent\n    well-anchored. Ward 11 is <strong>zero</strong>. Across all twenty wards the\n    correlation between geocoding quality and over-representation is\n    <strong>+0.52</strong>. We show most confidently the places we happened to\n    be able to place.</p>\n\n  <h2>Why</h2>\n  <p>Two causes compound, and both run the same direction.</p>\n  <p>First, <strong>the directories under-recorded the poorest households</strong>.\n    Wood\'s lists 4,251 Black residents against a census count of 27,898. It was\n    a commercial product, canvassed for people worth listing, and it thinned\n    where rents were lowest.</p>\n  <p>Second, <strong>the addresses that survive least well are alley\n    addresses</strong>. Our anchor method needs a printed house number on a\n    street we can locate. Alleys often have neither, and alleys are where the\n    densest Black settlement was. So the same neighbourhoods are lost twice:\n    once by the canvasser in 1860, once by the geocoder in 2026.</p>\n\n  <h2>What this does not mean</h2>\n  <p>It does not mean the maps are wrong about the people they show. Every dot\n    is a real person at a real address, and the anchored ones are placed by the\n    directory\'s own printed table. It means the maps are <em>incomplete in a\n    patterned way</em>, and the pattern runs against the densest Black\n    neighbourhoods.</p>\n  <p>The honest use of these maps is as evidence of presence, never of absence.\n    A thin area on a dot map here is not a place where few Black Baltimoreans\n    lived. It may be a place we could not see.</p>\n  <p>The ward choropleths do not have this problem. They come from the census,\n    which counted everyone, and they are the right layer for any question about\n    how many and where.</p>\n'


def build_wards(content_tpl):
    import csv as _csv
    w50 = {int(r["ward"]): r for r in _csv.DictReader(
        open(ROOT / "data" / "work" / "ward_census_1850.csv"))}
    w60 = {int(r["ward"]): r for r in _csv.DictReader(
        open(ROOT / "data" / "work" / "ward_census_1860.csv"))}
    rows = []
    for w in sorted(w60):
        a, b = w50.get(w), w60[w]
        if not a:
            continue
        rows.append({
            "ward": w,
            "fc50": int(a["free_colored"]), "sl50": int(a["slave"]),
            "pct50": float(a["black_pct"]),
            "fc60": int(b["free_colored"]), "sl60": int(b["slave"]),
            "pct60": float(b["black_pct"]),
            "dpct": round(float(b["black_pct"]) - float(a["black_pct"]), 2),
            "agg60": int(b["aggregate"]),
        })
    body = (content_tpl
            .replace("__TITLE__", "Wards — Black Baltimore")
            .replace("__NAV__", nav_html("wards.html"))
            .replace("__EYEBROW__", "Seventh and Eighth Censuses")
            .replace("__H1__", "Twenty wards, two censuses")
            .replace("__LEDE__", "The ward table behind the density map, sortable, "
                                 "with 1850 and 1860 side by side.")
            .replace("__CONTENT__", WARDS_BODY)
            .replace("__SCRIPT__", WARDS_SCRIPT.replace("__WARDS__",
                     json.dumps(rows, separators=(",", ":")))))
    desc = "Baltimore population by ward and race, 1850 and 1860, from the printed censuses."
    (DOCS / "wards.html").write_text(document(body, "Twenty wards, two censuses", desc),
                                     encoding="utf8")
    print(f"wrote docs/wards.html ({(DOCS/'wards.html').stat().st_size/1_000:.0f} KB)")


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    data = json.loads(PAYLOAD.read_text(encoding="utf8"))
    payload_txt = PAYLOAD.read_text(encoding="utf8").replace("</", "<\\/")
    build_maps(MAP_TPL.read_text(encoding="utf8"), payload_txt, data)
    content_tpl = CONTENT_TPL.read_text(encoding="utf8")
    build_work(content_tpl, data)
    build_wards(content_tpl)
    build_bias(content_tpl)
    build_checking(content_tpl)
    build_sources(content_tpl)


if __name__ == "__main__":
    main()
