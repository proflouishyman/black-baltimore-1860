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
       ("wards.html", "Wards"), ("work.html", "Work"), ("sources.html", "Sources")]

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
          <span class="sub">Modern streets, faint, for orientation only. Not
            the geometry anything is placed on.</span></span></label>
    </fieldset>
"""
TIER2 = """<label class="row"><input type="checkbox" id="t2" checked>
        <span class="swatch" style="background:var(--approx)"></span>
        <span><span class="lab">Street&nbsp;only &mdash; %(approx)s</span><br>
          <span class="sub">Street known, position along it estimated.</span></span></label>"""


def build_maps(map_tpl, payload_txt, data):
    density_panel = (
        """
    <div class="years" id="cyears" style="display:flex;gap:6px;margin-bottom:2px">
      <button data-year="1850" aria-pressed="false">1850</button>
      <button data-year="1860" aria-pressed="true">1860</button>
    </div>
""" +
        stat_block([("16.8% &rarr; 13.1%", "Black share, 1850 to 1860"),
                    ("&minus;490", "Change in Black population"),
                    ("+43,854", "Change in white population"),
                    ("20 of 20", "Wards where the share fell")]) +
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
          <span class="sub">Modern streets, faint, for orientation only. Not
            the geometry anything is placed on.</span></span></label>
    </fieldset>

    <p class="note"><strong>Switch between 1850 and 1860.</strong> The two
      censuses share the same ward boundaries, so the comparison is exact. The
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

    pages = [("index.html", "density", "Seventh and Eighth Censuses",
              "Where Black Baltimore lived",
              "The whole city by ward, free and enslaved, in 1850 and 1860 \u2014 the "
              "decade the ground shifted beneath it.",
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
    build_sources(content_tpl)


if __name__ == "__main__":
    main()
