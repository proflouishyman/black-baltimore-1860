#!/usr/bin/env python3
"""Render docs/timeline.html: Black Baltimore, 1790-1868, as a narrative timeline.

Everything on the page is computed here from data/baltimore.db at build time, so
the prose and the tables cannot drift apart. Nothing is hard-coded that the
database can supply, and the few facts that come from outside the database
(Maryland's 1864 abolition, the 1861 ward redivision) are marked on the page as
context rather than as measurements.

Three things this page has to get right, because a reader will misread the data
otherwise:

1. Black share of Baltimore peaked in 1820 and fell to 1860 while the Black
   population itself GREW. The fall is a denominator effect - European arrivals
   grew the white population far faster. The page pairs an absolute-counts chart
   with a share chart precisely so that the two are read together.

2. The free-Black series is three different census categories, not one variable
   (nothfree 1790-1810, four "Colored" age bands in 1820, six differently-cut
   "Black" bands in 1830-1840). This is stated where the chart is shown.

3. 1790 does not reconcile: the IPUMS household rows sum to 10,641 people
   against a tagged city population of 13,503, a 21% shortfall in the source
   rows themselves. 1790 is marked wherever it appears and excluded from every
   trend claim.

Household composition is recomputed here from the `households` table rather than
copied from docs/HOUSEHOLDS.md, and the script prints both so the two can be
compared on every run.

Reads:  data/baltimore.db, web/content.html, data/work/map_payload.json (for the
        directory "listed" counts, optional)
Writes: docs/timeline.html, data/work/timeline_payload.json
"""

import json
import math
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Reuse the site's own document wrapper, nav and stat block. build_artifact.py
# is the owner of all three and is not modified here.
from build_artifact import document, nav_html, stat_block  # noqa: E402

DB = ROOT / "data" / "baltimore.db"
TPL = ROOT / "web" / "content.html"
OUT = ROOT / "docs" / "timeline.html"
PAYLOAD_OUT = ROOT / "data" / "work" / "timeline_payload.json"
MAP_PAYLOAD = ROOT / "data" / "work" / "map_payload.json"

# Census years whose underlying rows do not reconcile against the known city
# population. See docs/HOUSEHOLDS.md: 1790 is a 21% shortfall in IPUMS's own
# household rows, not a filter error, so it is flagged everywhere and excluded
# from trend statements.
UNRELIABLE = {1790}

# Published city population per the IPUMS citypop tag, used only to state the
# size of the 1790 gap. Not used in any series.
CITYPOP_1790 = 13503


# ---------------------------------------------------------------- data ------

def city_series(con):
    """City totals per census year, with free-white derived as a residual.

    `white` is population minus black_total rather than a summed set of age
    bands: the white bands overlap in some years, so summing them double-counts,
    while the residual is exact by construction.
    """
    rows = []
    for (y, hh, pop, free, ens, fb, black, pct, src) in con.execute(
            "SELECT year, households, population, free, enslaved, free_black, "
            "black_total, black_pct, source FROM city_year ORDER BY year"):
        rows.append({
            "year": y, "hh": hh, "pop": pop, "white": pop - black,
            "fb": fb, "ens": ens, "black": black, "pct": pct,
            "src": src,
            "printed": src.startswith("printed"),
            "flag": y in UNRELIABLE,
        })
    return rows


def ward_rows(con):
    """Ward tables keyed by year. 1820 uses twelve wards, 1850/1860 twenty."""
    out = {}
    for (y, w, white, fc, sl, black, agg, pct) in con.execute(
            "SELECT year, ward, white, free_colored, slave, black_total, "
            "aggregate, black_pct FROM ward_census ORDER BY year, ward"):
        out.setdefault(str(y), []).append({
            "ward": w, "white": white, "fb": fc, "ens": sl,
            "black": black, "agg": agg, "pct": pct,
        })
    return out


def composition(con):
    """Black-only versus mixed households, recomputed from the microdata.

    A household counts as Black-present if it records at least one free Black
    resident. It is Black-only when it records no free white residents, and
    mixed when it records both. `white` is stored as free persons minus free
    Black persons, so `white <= 0` is the Black-only test (the <= guards against
    any row where the band sum exceeds the free-person count).

    No head-of-household race exists in this file, so "Black-only" is a
    statement about who was counted in the house, not about who headed it.
    """
    out = []
    for (y,) in con.execute("SELECT DISTINCT year FROM households ORDER BY year"):
        allhh, = con.execute(
            "SELECT COUNT(*) FROM households WHERE year=?", (y,)).fetchone()
        bh, bp = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(free_black),0) FROM households "
            "WHERE year=? AND free_black>0 AND white<=0", (y,)).fetchone()
        mh, mp = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(free_black),0) FROM households "
            "WHERE year=? AND free_black>0 AND white>0", (y,)).fetchone()
        neg, = con.execute(
            "SELECT COUNT(*) FROM households WHERE year=? AND white<0",
            (y,)).fetchone()
        present = bh + mh
        out.append({
            "year": y, "allhh": allhh, "present": present,
            "bh": bh, "bp": bp, "mh": mh, "mp": mp,
            "pct_mixed": round(mh / present * 100, 1) if present else None,
            "pct_people_mixed": round(mp / (bp + mp) * 100, 1) if (bp + mp) else None,
            "b_mean": round(bp / bh, 2) if bh else None,
            "m_mean": round(mp / mh, 2) if mh else None,
            "negwhite": neg,
            "flag": y in UNRELIABLE,
        })
    return out


def slaveholding(con):
    """Slaveholding households per year, plus the overlap with free Black presence."""
    out = []
    for (y,) in con.execute("SELECT DISTINCT year FROM households ORDER BY year"):
        allhh, = con.execute(
            "SELECT COUNT(*) FROM households WHERE year=?", (y,)).fetchone()
        sh, ens = con.execute(
            "SELECT COUNT(*), COALESCE(SUM(n_slave),0) FROM households "
            "WHERE year=? AND n_slave>0", (y,)).fetchone()
        overlap, = con.execute(
            "SELECT COUNT(*) FROM households WHERE year=? AND n_slave>0 "
            "AND free_black>0", (y,)).fetchone()
        med = None
        if sh:
            med, = con.execute(
                "SELECT n_slave FROM households WHERE year=? AND n_slave>0 "
                "ORDER BY n_slave LIMIT 1 OFFSET ?", (y, sh // 2)).fetchone()
        out.append({
            "year": y, "allhh": allhh, "sh": sh,
            "pct_sh": round(sh / allhh * 100, 1) if allhh else None,
            "mean": round(ens / sh, 2) if sh else None,
            "median": med, "ens": ens,
            "overlap": overlap,
            "pct_overlap": round(overlap / sh * 100, 1) if sh else None,
            "flag": y in UNRELIABLE,
        })
    return out


# Age bands for the 1850 slave schedule. 999 is IPUMS's missing-age code and is
# kept as its own row rather than folded into a band or dropped.
AGE_BANDS = [(0, 10, "Under 10"), (10, 20, "10 to 19"), (20, 30, "20 to 29"),
             (30, 40, "30 to 39"), (40, 50, "40 to 49"), (50, 60, "50 to 59"),
             (60, 900, "60 and over")]


def enslaved_profile(con, year):
    """Age and sex of everyone on Baltimore's slave schedule for one year.

    IPUMS codes an unknown age as 999 and an unknown sex as 9. Both are kept as
    their own rows or columns rather than dropped or folded into a real band,
    because silently discarding them would make the totals stop matching the
    schedule.
    """
    rows, tot_m, tot_f, tot_u = [], 0, 0, 0
    bands = list(AGE_BANDS) + [(900, 10 ** 6, "Age not recorded")]
    for lo, hi, label in bands:
        m, f, u = (con.execute(
            "SELECT COUNT(*) FROM enslaved WHERE year=? AND sex=? "
            "AND age>=? AND age<?", (year, s, lo, hi)).fetchone()[0]
            for s in (1, 2, 9))
        if lo == 900 and (m + f + u) == 0:
            continue
        rows.append({"band": label, "m": m, "f": f, "u": u, "all": m + f + u})
        tot_m += m
        tot_f += f
        tot_u += u
    total, = con.execute(
        "SELECT COUNT(*) FROM enslaved WHERE year=?", (year,)).fetchone()
    holds, = con.execute(
        "SELECT COUNT(DISTINCT holdnum) FROM enslaved WHERE year=?",
        (year,)).fetchone()
    return {"rows": rows, "m": tot_m, "f": tot_f, "u": tot_u,
            "total": total, "holds": holds}


def holding_sizes(con, year):
    """How many enslaved people lived in holdings of each size."""
    buckets = [(1, 1, "1 person"), (2, 2, "2 people"), (3, 5, "3 to 5"),
               (6, 10, "6 to 10"), (11, 10 ** 6, "11 or more")]
    out = []
    for lo, hi, label in buckets:
        n, = con.execute(
            "SELECT COUNT(*) FROM enslaved WHERE year=? AND sizehold>=? "
            "AND sizehold<=?", (year, lo, hi)).fetchone()
        h, = con.execute(
            "SELECT COUNT(DISTINCT holdnum) FROM enslaved WHERE year=? "
            "AND sizehold>=? AND sizehold<=?", (year, lo, hi)).fetchone()
        out.append({"band": label, "holds": h, "people": n})
    return out


def placed_counts(con):
    """Directory records we placed on a map, by volume year."""
    return {str(y): n for (y, n) in con.execute(
        "SELECT year, COUNT(*) FROM people GROUP BY year ORDER BY year")}


def listed_counts():
    """Directory records parsed, by volume year, from the shared map payload."""
    if not MAP_PAYLOAD.exists():
        return {}
    try:
        return json.loads(MAP_PAYLOAD.read_text(encoding="utf8")).get("parsed", {})
    except (ValueError, OSError):
        return {}


# --------------------------------------------------------------- charts -----

CW, CH = 560, 320
ML, MR, MT, MB = 56, 14, 16, 30


def nice_max(hi, n=5):
    """A round axis maximum at or above `hi`, with a matching step."""
    if hi <= 0:
        return 1, 1
    raw = hi / n
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if step >= raw:
            break
    top = step * math.ceil(hi / step)
    return top, step


def fmt_int(v):
    return f"{int(round(v)):,}"


def fmt_pct(v):
    return f"{v:g}%"


def line_chart(years, series, title, desc, fmt=fmt_int, y_top=None,
               flag_years=(), n_ticks=5, annotations=()):
    """One SVG line chart. `series` is a list of dicts with name, var, values.

    `var` is a CSS custom property name from the site palette, applied through a
    style attribute rather than a presentation attribute so that the colours
    follow the page's light and dark themes.

    Any segment touching a year in `flag_years` is drawn dashed and its point is
    drawn hollow, so an unreliable year cannot be read as an ordinary one.
    """
    hi = max(max(s["values"]) for s in series)
    top, step = (nice_max(hi, n_ticks) if y_top is None
                 else (y_top, y_top / n_ticks))
    x0, x1 = ML, CW - MR
    y0, y1 = CH - MB, MT

    def px(i):
        return x0 + (x1 - x0) * (i / (len(years) - 1) if len(years) > 1 else 0)

    def py(v):
        return y0 - (y0 - y1) * (v / top if top else 0)

    parts = [f'<svg viewBox="0 0 {CW} {CH}" role="img" '
             f'aria-label="{title}" style="width:100%;height:auto;display:block" '
             f'preserveAspectRatio="xMidYMid meet">',
             f"<title>{title}</title><desc>{desc}</desc>"]

    # horizontal grid and value labels
    t = 0.0
    while t <= top + step * 0.001:
        y = py(t)
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" '
                     f'style="stroke:var(--rule);stroke-width:1"/>')
        parts.append(f'<text x="{x0 - 8}" y="{y + 3.5:.1f}" text-anchor="end" '
                     f'style="fill:var(--ink-3);font-size:10.5px;'
                     f'font-variant-numeric:tabular-nums">{fmt(t)}</text>')
        t += step

    # year labels
    for i, yr in enumerate(years):
        parts.append(f'<text x="{px(i):.1f}" y="{y0 + 17}" text-anchor="middle" '
                     f'style="fill:var(--ink-3);font-size:10.5px;'
                     f'font-variant-numeric:tabular-nums">{yr}</text>')

    for s in series:
        col = f'var({s["var"]})'
        # split into solid and dashed runs so a flagged year is visibly separate
        for i in range(len(years) - 1):
            dashed = years[i] in flag_years or years[i + 1] in flag_years
            d = ' stroke-dasharray="4 3"' if dashed else ""
            parts.append(
                f'<line x1="{px(i):.1f}" y1="{py(s["values"][i]):.1f}" '
                f'x2="{px(i+1):.1f}" y2="{py(s["values"][i+1]):.1f}"'
                f'{d} style="stroke:{col};stroke-width:2;'
                f'stroke-linecap:round;fill:none"/>')
        for i, v in enumerate(years):
            hollow = v in flag_years
            fill = "var(--ground)" if hollow else col
            parts.append(
                f'<circle cx="{px(i):.1f}" cy="{py(s["values"][i]):.1f}" r="3" '
                f'style="fill:{fill};stroke:{col};stroke-width:1.5"/>')

    # callouts on a specific year, used to name the peak rather than leave a
    # reader to find it
    for yr, text, si in annotations:
        i = years.index(yr)
        v = series[si]["values"][i]
        anchor = "start" if i < len(years) / 2 else "end"
        dx = 7 if anchor == "start" else -7
        parts.append(
            f'<text x="{px(i) + dx:.1f}" y="{py(v) - 9:.1f}" '
            f'text-anchor="{anchor}" style="fill:var(--ink-2);'
            f'font-size:11px;font-weight:600">{text}</text>')

    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" '
                 f'style="stroke:var(--ink-3);stroke-width:1"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def legend(series, fmt=fmt_int):
    items = []
    for s in series:
        items.append(
            f'<span class="lg"><span class="lgs" style="background:var({s["var"]})">'
            f'</span>{s["name"]} <span class="mono lgv">{fmt(s["values"][-1])} '
            f'in {s["last_year"]}</span></span>')
    return f'<div class="legend">{"".join(items)}</div>'


# ------------------------------------------------------------- page CSS -----

EXTRA_CSS = """<style>
  /* timeline page only: everything else is inherited from the shared sheet */
  .chartgrid { display: grid; gap: 26px; margin: 22px 0 4px;
    grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); }
  .cardfig { margin: 0; border: 1px solid var(--rule); background: var(--panel);
    padding: 14px 14px 10px; border-radius: 3px; }
  .cardfig h3 { font-size: 14.5px; margin: 0 0 2px; font-weight: 600; }
  .cardfig .sub { font-size: 12px; color: var(--ink-3); margin: 0 0 10px;
    max-width: none; }
  .legend { display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: 10px; }
  .legend .lg { font-size: 12px; color: var(--ink-2); display: flex;
    align-items: center; gap: 6px; }
  .legend .lgs { width: 11px; height: 11px; border-radius: 2px; flex: none; }
  .legend .lgv { color: var(--ink-3); font-size: 11.5px; }

  .tbar { display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center;
    margin: 16px 0 2px; }
  .tbar label { font-size: 12px; color: var(--ink-3); letter-spacing: .04em;
    text-transform: uppercase; }
  .tbar input { font: inherit; font-size: 13px; padding: 6px 10px;
    background: var(--panel); color: var(--ink); border: 1px solid var(--rule);
    border-radius: 2px; min-width: 210px; }
  .tbar input:focus-visible { outline: 2px solid var(--anchored);
    outline-offset: 1px; }
  .tbar .count { font-size: 12.5px; color: var(--ink-3);
    font-variant-numeric: tabular-nums; margin-left: auto; }

  table.data td.n, table.data th.n { font-variant-numeric: tabular-nums; }
  table.data tr.flagged td { background: color-mix(in srgb, var(--anchored) 8%,
    transparent); }
  .flag { color: var(--anchored); font-weight: 600; cursor: help; }
  .src { font-size: 11.5px; letter-spacing: .03em; }
  .src.printed { color: var(--approx); }
  .src.micro { color: var(--anchored); }
  p.fn { font-size: 12px; color: var(--ink-3); margin: 9px 0 0; max-width: 68ch; }

  ol.tl { list-style: none; margin: 20px 0 0; padding: 0 0 0 20px;
    border-left: 2px solid var(--rule); }
  ol.tl li { position: relative; padding: 0 0 24px 6px; }
  ol.tl li::before { content: ""; position: absolute; left: -27px; top: 6px;
    width: 10px; height: 10px; border-radius: 50%; background: var(--anchored);
    border: 2px solid var(--ground); }
  ol.tl li.k-directory::before { background: var(--approx); }
  ol.tl li.k-context::before { background: var(--ground);
    border-color: var(--ink-3); }
  ol.tl .yr { font-size: 12px; letter-spacing: .1em; color: var(--ink-3);
    font-variant-numeric: tabular-nums; }
  ol.tl h3 { font-size: 16px; margin: 1px 0 5px; font-weight: 600;
    letter-spacing: -.01em; }
  ol.tl p { font-size: 13.5px; color: var(--ink-2); margin: 0; max-width: 66ch; }
  ol.tl li.hide { display: none; }

  .stats { display: flex; flex-wrap: wrap; gap: 18px 34px; margin: 24px 0 6px; }
  .stat .n { font-size: 26px; font-weight: 600; letter-spacing: -.02em; }
  .stat .k { font-size: 12px; color: var(--ink-3); letter-spacing: .04em; }
</style>
"""


# ------------------------------------------------------------- page body ----

def build_body(D, M):
    """Assemble the page content. Every number here comes from `M`."""
    c = {r["year"]: r for r in D["city"]}
    comp = {r["year"]: r for r in D["composition"]}
    sh = {r["year"]: r for r in D["slaveholding"]}

    stats = stat_block([
        (f'{c[1860]["fb"]:,}', "Free Black Baltimoreans, 1860"),
        (f'{c[1860]["ens"]:,}', "Still enslaved, 1860"),
        (f'{c[1820]["pct"]:.1f}%', "Black share of the city, 1820 peak"),
        (f'{c[1860]["pct"]:.1f}%', "Black share of the city, 1860"),
    ])

    # ---- charts
    years = [r["year"] for r in D["city"]]
    abs_series = [
        {"name": "White", "var": "--ink-3",
         "values": [r["white"] for r in D["city"]], "last_year": years[-1]},
        {"name": "Free Black", "var": "--anchored",
         "values": [r["fb"] for r in D["city"]], "last_year": years[-1]},
        {"name": "Enslaved", "var": "--approx",
         "values": [r["ens"] for r in D["city"]], "last_year": years[-1]},
    ]
    share_series = [
        {"name": "Black share of the city", "var": "--anchored",
         "values": [r["pct"] for r in D["city"]], "last_year": years[-1]},
    ]
    black_series = [
        {"name": "Free Black", "var": "--anchored",
         "values": [r["fb"] for r in D["city"]], "last_year": years[-1]},
        {"name": "Enslaved", "var": "--approx",
         "values": [r["ens"] for r in D["city"]], "last_year": years[-1]},
    ]

    chart_abs = line_chart(
        years, abs_series,
        "Baltimore population by status, 1790 to 1860",
        "Three lines. The white population rises from about 9,000 in 1790 to "
        f"{c[1860]['white']:,} in 1860. Free Black Baltimoreans rise from a few "
        f"hundred to {c[1860]['fb']:,}. The enslaved population peaks at "
        f"{c[1810]['ens']:,} in 1810 and falls to {c[1860]['ens']:,}.",
        flag_years=UNRELIABLE, n_ticks=4)
    chart_share = line_chart(
        years, share_series,
        "Black share of Baltimore's population, 1790 to 1860",
        f"A single line rising to a peak of {c[1820]['pct']:.1f} per cent in "
        f"1820 and falling to {c[1860]['pct']:.1f} per cent in 1860.",
        fmt=fmt_pct, y_top=25, flag_years=UNRELIABLE,
        annotations=[(1820, "peak", 0)])
    chart_black = line_chart(
        years, black_series,
        "Free and enslaved Black Baltimoreans, 1790 to 1860",
        "Two lines on one scale. The free line crosses above the enslaved line "
        "between 1800 and 1810 and never returns.",
        flag_years=UNRELIABLE, n_ticks=6,
        annotations=[(1810, "slavery peaks", 1)])

    charts = f"""
  <div class="chartgrid">
    <figure class="cardfig">
      <h3>The counts</h3>
      <p class="sub">Every group grew except one. Read this chart first.</p>
      {chart_abs}
      {legend(abs_series)}
    </figure>
    <figure class="cardfig">
      <h3>The share</h3>
      <p class="sub">The same city, expressed as a proportion. It moves the
        other way after 1820.</p>
      {chart_share}
      {legend(share_series, fmt=lambda v: f"{v:.1f}%")}
    </figure>
  </div>
"""

    # ---- narrative timeline
    tl = "\n".join(
        f'    <li class="k-{e["kind"]}" data-kind="{e["kind"]}">'
        f'<div class="yr">{e["year"]}</div>'
        f'<h3>{e["title"]}</h3><p>{e["text"]}</p></li>'
        for e in D["events"])

    # ---- fragments of prose that depend on computed values
    hh40 = comp[1840]
    hh90 = comp[1790]
    hh00 = comp[1800]

    body = f"""
  {stats}

  <div class="note"><strong>The single most misread number on this page is the
    percentage.</strong> Black Baltimore was {c[1820]['pct']:.1f} per cent of
    the city in 1820 and {c[1860]['pct']:.1f} per cent in 1860. That fall is not
    a fall in population. Between those two censuses the number of free Black
    Baltimoreans rose from {c[1820]['fb']:,} to {c[1860]['fb']:,}. What changed
    was the denominator. Baltimore added roughly
    {(c[1860]['white'] - c[1820]['white']):,} white residents over the same
    forty years, mostly German and Irish arrivals, and a growing population
    became a smaller fraction of a city growing faster still.</div>

  <h2>Two charts, read together</h2>
  {charts}

  <p class="note"><strong>The free Black line is three different census
    categories, not one variable.</strong> 1790 to 1810 have no race-labelled
    column at all, so the count is <span class="mono">nothfree</span>, the
    census category "other free persons except Indians not taxed," which is the
    standard proxy historians use. 1820 introduces four age bands labelled
    "Colored." 1830 and 1840 switch to six differently cut bands labelled
    "Black." 1850 and 1860 come from the printed ward tables and their "free
    colored" column. A single line drawn through all of that is comparing at
    least three things, and the joins are at 1820 and at 1850. Read the shape,
    not the year-to-year steps.</p>

  <p class="note"><strong>1790 does not reconcile and is drawn dashed and
    hollow wherever it appears.</strong> The IPUMS household rows for Baltimore
    sum to {c[1790]['pop']:,} people against a tagged city population of
    {CITYPOP_1790:,}, a shortfall of
    {round((1 - c[1790]['pop'] / CITYPOP_1790) * 100)} per cent in the source
    rows themselves rather than in our filter. Independent verification
    reproduced the same gap. No trend statement on this page starts at 1790.</p>

  <h2>The city year by year</h2>
  <p>Click any column heading to sort. Type in the box to filter. The
    <em>Source</em> column matters: two different kinds of evidence feed this
    table and they are not blended. The printed federal census ward tables were
    transcribed by hand and reconciled against the printed totals, so they are
    authoritative. The IPUMS complete-count microdata runs slightly under the
    published aggregates in every year.</p>

  <div class="tbar">
    <label for="cq">Filter</label>
    <input type="search" id="cq" placeholder="year, source, any figure">
    <span class="count" id="cq-count"></span>
  </div>
  <div class="scroll">
    <table class="data" id="tab-city">
      <thead><tr></tr></thead><tbody></tbody>
    </table>
  </div>
  <p class="fn">&dagger; 1790 does not reconcile. Its household rows sum to 21 per cent under the city population the census itself records, so the row is tinted here and excluded from every trend claim on this page.</p>

  <p class="note"><strong>All of these counts are floors.</strong> Household
    sums run between 0.1 and 1.9 per cent below the printed figures in the years
    where both exist. Read every number as "at least this many." Where the two
    sources disagree we keep the printed volume, because it is what the Census
    actually published.</p>

  <h2>1790 to 1868, in order</h2>
  <p>Census years are marked in one colour, city directories in another, and the
    two entries that come from outside this data are marked as context. Use the
    buttons to show one kind at a time.</p>

  <div class="years" id="tlfilter">
    <button data-kind="all" aria-pressed="true">Everything</button>
    <button data-kind="census" aria-pressed="false">Census years</button>
    <button data-kind="directory" aria-pressed="false">Directories</button>
    <button data-kind="context" aria-pressed="false">Context</button>
  </div>

  <ol class="tl" id="tl">
{tl}
  </ol>

  <h2>Slavery contracting inside a growing city</h2>
  <div class="chartgrid">
    <figure class="cardfig">
      <h3>Free and enslaved, on one scale</h3>
      <p class="sub">The crossing happens between 1800 and 1810 and is never
        reversed.</p>
      {chart_black}
      {legend(black_series)}
    </figure>
    <figure class="cardfig">
      <h3>Who was still enslaved</h3>
      <p class="sub">Age and sex of every person on Baltimore's slave
        schedules. Choose a year, then click a heading to sort.</p>
      <div class="years" id="eyears" style="margin:2px 0 10px"></div>
      <div class="scroll">
        <table class="data" id="tab-ens"><thead><tr></tr></thead><tbody></tbody></table>
      </div>
    </figure>
  </div>

  <p>The enslaved population of Baltimore reached {c[1810]['ens']:,} in 1810 and
    never grew again. By 1860 it was {c[1860]['ens']:,}, a fall of
    {round((1 - c[1860]['ens'] / c[1810]['ens']) * 100)} per cent across fifty
    years in a state where slavery remained fully legal and where no abolition
    statute was passed until 1864. Over the same fifty years the free Black
    population of the city grew from {c[1810]['fb']:,} to {c[1860]['fb']:,}. By
    1860 free Black Baltimoreans outnumbered the enslaved more than
    {c[1860]['fb'] // c[1860]['ens']} to one, which is why this city, and not a
    Northern one, held the largest free Black population in the United States.</p>

  <p><strong>Two thirds of the people still held in Baltimore were women and
    girls.</strong> The 1850 schedule records {M['f50']:,} females against
    {M['m50']:,} males, which is {M['fpct50']:.0f} per cent female, and 1860 is
    almost identical at {M['fpct60']:.0f} per cent. Urban slavery in Baltimore
    was domestic work, and the schedules show it in the sex ratio before they
    show it anywhere else. The age profile points the same way. The largest
    single band in both years is people in their teens.</p>

  <p>The schedules also show how small the holdings were. In 1850,
    {M['ens_total']:,} people were held in {M['ens_holds']:,} separate holdings,
    an average of {M['ens_total'] / M['ens_holds']:.1f} people each.
    {M['hold1_people']:,} of them, {M['hold1_pct']:.0f} per cent, were the only
    enslaved person recorded in their holding, and only
    {M['hold11_people']:,} people were held in a group of eleven or more. This
    was not plantation slavery moved indoors. It was mostly one or two people
    inside a household, which is also why they cannot be mapped: the schedules
    record them under an owner's name, with no address of their own.</p>

  <div class="note"><strong>One cross-check that came out well, twice.</strong>
    The IPUMS 1850 slave schedule counts {M['ens_total']:,} enslaved people in
    Baltimore. The printed 1850 census volume, which this project transcribed by
    hand from the page and reconciled ward by ward, gives
    {M['printed_1850_slave']:,}. That is a gap of
    {abs(M['ens_total'] - M['printed_1850_slave'])} people out of nearly three
    thousand, or
    {abs(M['ens_total'] - M['printed_1850_slave']) / M['printed_1850_slave'] * 100:.1f}
    per cent. The same check on 1860 gives {M['ens_total_60']:,} against
    {M['printed_1860_slave']:,}, a gap of
    {abs(M['ens_total_60'] - M['printed_1860_slave'])}. Two independent sources,
    transcribed by different methods more than a century apart, agreeing to a
    tenth of a per cent in both years. That is the kind of agreement that makes
    the rest of the table worth trusting.</div>

  <h2>Ward by ward</h2>
  <p>Three census years survive with a ward-level race breakdown.
    <strong>1820 used twelve wards and 1850 and 1860 used twenty</strong>, so
    1820 is a different division of the same city and should be read as a
    distribution rather than compared ward against ward. 1850 and 1860 share
    boundaries exactly, so that pair is a like-for-like comparison.</p>

  <div class="years" id="wyears"></div>
  <div class="tbar">
    <label for="wq">Filter</label>
    <input type="search" id="wq" placeholder="ward number or any figure">
    <span class="count" id="wq-count"></span>
  </div>
  <div class="scroll">
    <table class="data" id="tab-ward"><thead><tr></tr></thead><tbody></tbody></table>
  </div>
  <p class="note">Sort 1860 by <em>Black share</em> and the top of the table is
    wards 11, 15 and 12, the same wards that top 1850. The Black share of the
    population fell in every one of the twenty wards between those two
    censuses. The <a href="./wards.html">ward page</a> puts the two years side
    by side with the change in each.</p>

  <h2>Whose household, 1790 to 1840</h2>
  <p>This is the part of the story the maps cannot tell. The household
    microdata carries <strong>no name, no address and no ward</strong>. The
    finest geography in the file is the whole city, so nothing in this section
    can be placed on a street. What it can do is answer a different question,
    and an earlier one than any directory this project maps: not where Black
    Baltimoreans lived, but with whom.</p>

  <p>A household counts as Black-present here if it recorded at least one free
    Black resident. It is <em>Black-only</em> when no free white resident was
    recorded in it, and <em>mixed</em> when both were. There is no
    head-of-household race in this file, so a Black-only household is a
    statement about who was counted in the house, not proof of who headed it.
    A mixed household's head cannot be determined from this data at all.</p>

  <div class="tbar">
    <label for="hq">Filter</label>
    <input type="search" id="hq" placeholder="year or any figure">
    <span class="count" id="hq-count"></span>
  </div>
  <p><em>Mean Black, Black-only</em> is the average number of free Black
    residents recorded in a Black-only household, and <em>Mean Black, mixed</em>
    the same figure for mixed households. <em>People in mixed</em> is the share
    of all free Black people counted that year who were living in a mixed
    household.</p>

  <div class="scroll">
    <table class="data" id="tab-hh"><thead><tr></tr></thead><tbody></tbody></table>
  </div>
  <p class="fn">&dagger; 1790 does not reconcile. Its household rows sum to 21 per cent under the city population the census itself records, so the row is tinted here and excluded from every trend claim on this page.</p>

  <p><strong>Free Black Baltimoreans increasingly lived in their own
    households.</strong> Mixed households were
    {hh00['pct_mixed']:.0f} per cent of all Black-present households in 1800 and
    {hh40['pct_mixed']:.0f} per cent by 1840. Household size says the same thing
    from the other direction. A Black-only household held an average of
    {min(r['b_mean'] for r in D['composition'] if not r['flag']):.1f} to
    {max(r['b_mean'] for r in D['composition'] if not r['flag']):.1f} free Black
    residents across these years, while a mixed household held
    {min(r['m_mean'] for r in D['composition'] if not r['flag']):.1f} to
    {max(r['m_mean'] for r in D['composition'] if not r['flag']):.1f}. One or
    two Black residents inside a larger white household is a different
    arrangement from a Black family unit, and the second was becoming the more
    common one.</p>

  <p class="note"><strong>These figures were recomputed from the household
    table for this page rather than copied from the project's earlier
    write-up</strong>, and they reproduce it. The share of Black-present
    households that were mixed comes out at {hh90['pct_mixed']:.1f} per cent in
    1790 and {hh40['pct_mixed']:.1f} per cent in 1840, against 61.1 and 46.3 in
    <a href="https://github.com/proflouishyman/black-baltimore-1860/blob/main/docs/HOUSEHOLDS.md">docs/HOUSEHOLDS.md</a>.
    Every household count, mean and share in the two tables here matches that
    document exactly. The 1790 row is flagged in both.</p>

  <p>The people-level column does not fall smoothly. It dips at 1810 and
    partly rebounds at 1820, and that wiggle lands exactly on the year the
    underlying measure changes from the <span class="mono">nothfree</span> proxy
    to explicit age-banded race columns. Read it as a possible artifact of the
    category boundary rather than a real reversal in how people were living. The
    household-level column moves the same direction across the whole period and
    is not affected by it.</p>

  <h2>Slaveholding households</h2>
  <p>Slavery in Baltimore did not end by shrinking evenly. It became a smaller
    and smaller part of city life while the households that kept it held fewer
    and fewer people.</p>

  <div class="tbar">
    <label for="sq">Filter</label>
    <input type="search" id="sq" placeholder="year or any figure">
    <span class="count" id="sq-count"></span>
  </div>
  <div class="scroll">
    <table class="data" id="tab-sl"><thead><tr></tr></thead><tbody></tbody></table>
  </div>
  <p class="fn">&dagger; 1790 does not reconcile. Its household rows sum to 21 per cent under the city population the census itself records, so the row is tinted here and excluded from every trend claim on this page.</p>

  <p>Slaveholding households fell from {sh[1800]['pct_sh']:.1f} per cent of all
    Baltimore households in 1800 to {sh[1840]['pct_sh']:.1f} per cent in 1840,
    even though the absolute number of slaveholding households kept rising until
    1830, because the city itself grew roughly tenfold over the period. The
    median holding fell from two people to one between 1820 and 1830, and the
    mean from {sh[1800]['mean']:.2f} to {sh[1840]['mean']:.2f}.</p>

  <p><strong>The last column is the one worth pausing on.</strong> The share of
    slaveholding households that also recorded free Black residents rose from
    {sh[1790]['pct_overlap']:.1f} per cent in 1790 to
    {sh[1840]['pct_overlap']:.1f} per cent in 1840. The shrinking population of
    slaveholders and the growing free Black population were not two separate
    stories happening in different houses. They increasingly overlapped inside
    the same ones. The rise from 1790 to 1810 rests on a single consistent proxy
    and is a clean trend. The further jump at 1820 crosses the category boundary
    flagged above and is less clean, though the direction holds either way.</p>

  <p class="note"><strong>The enslaved totals in this table will not match the
    city table above, and that is deliberate.</strong> These come from the
    household microdata. The city table prefers the printed volume wherever one
    exists. 1820 is the one year where both are available, and they disagree:
    {sh[1820]['ens']:,} here against {c[1820]['ens']:,} there, a gap of
    {abs(sh[1820]['ens'] - c[1820]['ens']) / c[1820]['ens'] * 100:.1f} per cent.
    Merging the two would hide exactly the kind of seam a reader needs to see,
    so both are shown with their source named.</p>

  <h2>What this page cannot tell you</h2>
  <p><strong>1790 is unreliable.</strong> Its household rows account for about
    {round(c[1790]['pop'] / CITYPOP_1790 * 100)} per cent of the city the census
    itself says was there. It is shown because omitting it silently would be
    worse, and it is marked everywhere it appears.</p>
  <p><strong>The free Black series is not one measurement.</strong> Three census
    categories and two transcription methods sit behind that line. It is honest
    about direction and magnitude and should not be read as a precise annual
    series.</p>
  <p><strong>Every count is a floor.</strong> Where an independent check exists,
    the microdata runs under the printed figures, never over. Read every number
    on this page as a minimum.</p>
  <p><strong>None of the household data can be mapped.</strong> No name, no
    address, no ward. Anyone wanting street-level evidence should use the
    <a href="./index.html">density maps</a> and the year maps, and should read
    <a href="./bias.html">what those maps miss</a> first, because the
    directories under-recorded exactly the densest Black wards.</p>
  <p><strong>The enslaved cannot be placed at all.</strong> They appear in the
    schedules under an owner's name, with no address of their own. Where they
    lived in the city is a question this evidence cannot answer.</p>

  <h2>Where the numbers come from</h2>
  <p>City and ward figures for 1820, 1850 and 1860 come from the printed federal
    census ward tables, transcribed by hand from the scans and checked by
    summing every column against the printed city totals. Figures for 1790,
    1800, 1810, 1830 and 1840 come from the IPUMS complete-count household
    microdata for Baltimore City. The enslaved profiles for 1850 and 1860 come
    from the IPUMS complete-count slave schedules, which are a separate file from
    the household data. Directory counts come from this project's own
    parsing and geocoding of the volumes listed on the
    <a href="./sources.html">sources page</a>. Every step is scripted and the
    repository is public.</p>
"""
    return body


# ------------------------------------------------------------- page JS ------

PAGE_JS = r"""
<script id="tld" type="application/json">__DATA__</script>
<script>
(function () {
  var D = JSON.parse(document.getElementById('tld').textContent);

  function fmt(v, kind) {
    if (v === null || v === undefined || v === '') return 'not in file';
    if (kind === 'int') return Number(v).toLocaleString();
    if (kind === 'pct1') return Number(v).toFixed(1) + '%';
    if (kind === 'pct2') return Number(v).toFixed(2) + '%';
    if (kind === 'num2') return Number(v).toFixed(2);
    return String(v);
  }

  /* One sortable, filterable table. Sorting is on the raw value, filtering on
     the rendered text, so a reader filtering "printed" matches what they see. */
  function makeTable(opts) {
    var table = document.getElementById(opts.id);
    var hr = table.tHead.rows[0], tb = table.tBodies[0];
    var input = opts.filter ? document.getElementById(opts.filter) : null;
    var countEl = opts.count ? document.getElementById(opts.count) : null;
    var key = opts.sort, asc = opts.asc !== false, rows = opts.rows;

    function cellText(r, c) {
      if (c.render) return c.render(r).text;
      return fmt(r[c.k], c.f);
    }

    function render() {
      var q = input ? input.value.trim().toLowerCase() : '';
      var out = rows.filter(function (r) {
        if (!q) return true;
        return opts.cols.some(function (c) {
          return cellText(r, c).toLowerCase().indexOf(q) >= 0;
        });
      });
      out = out.slice().sort(function (a, b) {
        var x = a[key], y = b[key];
        if (x === null || x === undefined) x = -Infinity;
        if (y === null || y === undefined) y = -Infinity;
        if (typeof x === 'string' || typeof y === 'string') {
          x = String(x).toLowerCase(); y = String(y).toLowerCase();
        }
        return (x === y ? 0 : (x > y ? 1 : -1)) * (asc ? 1 : -1);
      });
      tb.innerHTML = '';
      out.forEach(function (r) {
        var tr = document.createElement('tr');
        if (r.flag) tr.className = 'flagged';
        opts.cols.forEach(function (c) {
          var td = document.createElement('td');
          td.className = c.n ? 'n' : '';
          if (c.render) {
            var v = c.render(r);
            td.innerHTML = v.html;
          } else {
            td.textContent = fmt(r[c.k], c.f);
          }
          tr.appendChild(td);
        });
        tb.appendChild(tr);
      });
      if (countEl) {
        countEl.textContent = out.length === rows.length
          ? rows.length + (rows.length === 1 ? ' row' : ' rows')
          : out.length + ' of ' + rows.length + ' rows';
      }
    }

    function head() {
      hr.innerHTML = '';
      opts.cols.forEach(function (c) {
        var th = document.createElement('th');
        th.className = c.n ? 'n' : '';
        th.textContent = c.t;
        th.tabIndex = 0;
        th.setAttribute('role', 'button');
        th.setAttribute('scope', 'col');
        if (c.k === key) th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
        function go() {
          if (key === c.k) { asc = !asc; } else { key = c.k; asc = !c.n; }
          Array.prototype.forEach.call(hr.children, function (o) {
            o.removeAttribute('aria-sort');
          });
          th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
          render();
        }
        th.onclick = go;
        th.onkeydown = function (e) {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); }
        };
        hr.appendChild(th);
      });
    }

    if (input) input.oninput = render;
    head();
    render();
    return { setRows: function (r) { rows = r; render(); } };
  }

  /* Flagged years carry a marker and a tooltip. The marker is kept to a single
     character so it never wraps the column and never widens the table. Each
     affected table carries a footnote spelling the marker out. */
  function yearCell(r) {
    return {
      text: String(r.year) + (r.flag ? ' unreliable' : ''),
      html: r.flag
        ? String(r.year) + ' <span class="flag" title="1790 does not ' +
          'reconcile. The household rows sum to 21 per cent under the city ' +
          'population the census itself records.">&dagger;</span>'
        : String(r.year)
    };
  }

  function srcCell(r) {
    var printed = r.printed;
    var label = printed ? 'Printed census, ward tables' : 'IPUMS household microdata';
    return {
      text: label,
      html: '<span class="src ' + (printed ? 'printed' : 'micro') + '">' +
        label + '</span>'
    };
  }

  makeTable({
    id: 'tab-city', rows: D.city, sort: 'year', asc: true,
    filter: 'cq', count: 'cq-count',
    cols: [
      { k: 'year',  t: 'Year',             render: yearCell },
      { k: 'pop',   t: 'City population',  n: true, f: 'int' },
      { k: 'white', t: 'White',            n: true, f: 'int' },
      { k: 'fb',    t: 'Free Black',       n: true, f: 'int' },
      { k: 'ens',   t: 'Enslaved',         n: true, f: 'int' },
      { k: 'black', t: 'Black total',      n: true, f: 'int' },
      { k: 'pct',   t: 'Black share',      n: true, f: 'pct2' },
      { k: 'hh',    t: 'Households',       n: true, f: 'int' },
      { k: 'printed', t: 'Source',         render: srcCell }
    ]
  });

  var wardTable = makeTable({
    id: 'tab-ward', rows: D.wards[D.wardYears[D.wardYears.length - 1]],
    sort: 'ward', asc: true, filter: 'wq', count: 'wq-count',
    cols: [
      { k: 'ward',  t: 'Ward',        n: true, f: 'int' },
      { k: 'white', t: 'White',       n: true, f: 'int' },
      { k: 'fb',    t: 'Free Black',  n: true, f: 'int' },
      { k: 'ens',   t: 'Enslaved',    n: true, f: 'int' },
      { k: 'black', t: 'Black total', n: true, f: 'int' },
      { k: 'agg',   t: 'Ward total',  n: true, f: 'int' },
      { k: 'pct',   t: 'Black share', n: true, f: 'pct2' }
    ]
  });

  var wy = document.getElementById('wyears');
  D.wardYears.forEach(function (y, i) {
    var b = document.createElement('button');
    b.textContent = y;
    b.setAttribute('data-year', y);
    b.setAttribute('aria-pressed', i === D.wardYears.length - 1 ? 'true' : 'false');
    b.onclick = function () {
      Array.prototype.forEach.call(wy.children, function (o) {
        o.setAttribute('aria-pressed', o === b ? 'true' : 'false');
      });
      wardTable.setRows(D.wards[y]);
    };
    wy.appendChild(b);
  });

  makeTable({
    id: 'tab-hh', rows: D.composition, sort: 'year', asc: true,
    filter: 'hq', count: 'hq-count',
    cols: [
      { k: 'year',    t: 'Year',                    render: yearCell },
      { k: 'allhh',   t: 'All households',          n: true, f: 'int' },
      { k: 'present', t: 'Black-present',           n: true, f: 'int' },
      { k: 'bh',      t: 'Black-only',              n: true, f: 'int' },
      { k: 'mh',      t: 'Mixed',                   n: true, f: 'int' },
      { k: 'pct_mixed', t: 'Mixed share',           n: true, f: 'pct1' },
      { k: 'b_mean',  t: 'Mean Black, Black-only',  n: true, f: 'num2' },
      { k: 'm_mean',  t: 'Mean Black, mixed',       n: true, f: 'num2' },
      { k: 'pct_people_mixed', t: 'People in mixed', n: true, f: 'pct1' }
    ]
  });

  makeTable({
    id: 'tab-sl', rows: D.slaveholding, sort: 'year', asc: true,
    filter: 'sq', count: 'sq-count',
    cols: [
      { k: 'year',   t: 'Year',                render: yearCell },
      { k: 'allhh',  t: 'All households',      n: true, f: 'int' },
      { k: 'sh',     t: 'Slaveholding',        n: true, f: 'int' },
      { k: 'pct_sh', t: 'Share of all',        n: true, f: 'pct1' },
      { k: 'mean',   t: 'Mean holding',        n: true, f: 'num2' },
      { k: 'median', t: 'Median holding',      n: true, f: 'int' },
      { k: 'ens',    t: 'Enslaved people',     n: true, f: 'int' },
      { k: 'overlap', t: 'Also free Black present', n: true, f: 'int' },
      { k: 'pct_overlap', t: 'Overlap share',  n: true, f: 'pct1' }
    ]
  });

  var ensTable = makeTable({
    id: 'tab-ens', rows: D.enslaved[D.enslavedYears[0]].rows,
    sort: 'all', asc: false,
    cols: [
      { k: 'band', t: 'Age' },
      { k: 'm',    t: 'Male',        n: true, f: 'int' },
      { k: 'f',    t: 'Female',      n: true, f: 'int' },
      { k: 'u',    t: 'Not recorded', n: true, f: 'int' },
      { k: 'all',  t: 'All',         n: true, f: 'int' }
    ]
  });

  var ey = document.getElementById('eyears');
  D.enslavedYears.forEach(function (y, i) {
    var b = document.createElement('button');
    b.textContent = y;
    b.setAttribute('aria-pressed', i === 0 ? 'true' : 'false');
    b.onclick = function () {
      Array.prototype.forEach.call(ey.children, function (o) {
        o.setAttribute('aria-pressed', o === b ? 'true' : 'false');
      });
      ensTable.setRows(D.enslaved[y].rows);
    };
    ey.appendChild(b);
  });

  /* timeline filter */
  var tl = document.getElementById('tl'), tf = document.getElementById('tlfilter');
  Array.prototype.forEach.call(tf.children, function (b) {
    b.onclick = function () {
      var kind = b.getAttribute('data-kind');
      Array.prototype.forEach.call(tf.children, function (o) {
        o.setAttribute('aria-pressed', o === b ? 'true' : 'false');
      });
      Array.prototype.forEach.call(tl.children, function (li) {
        var show = kind === 'all' || li.getAttribute('data-kind') === kind;
        li.className = li.className.replace(/ ?hide/, '') + (show ? '' : ' hide');
      });
    };
  });
})();
</script>
"""


# ------------------------------------------------------------- events -------

def build_events(D):
    """The narrative spine. Every figure is interpolated from the data above."""
    c = {r["year"]: r for r in D["city"]}
    sh = {r["year"]: r for r in D["slaveholding"]}
    comp = {r["year"]: r for r in D["composition"]}
    placed = D["placed"]
    listed = D["listed"]

    def dirline(y):
        p = placed.get(str(y))
        l = listed.get(str(y))
        if l and p:
            return f"{l:,} residents parsed from the volume, {p:,} placed on a map."
        if p:
            return f"{p:,} residents placed on a map."
        return ""

    E = []

    E.append(dict(year=1790, kind="census", title="The first federal census",
                  text=f"{c[1790]['hh']:,} Baltimore households, "
                       f"{c[1790]['fb']:,} free Black residents and "
                       f"{c[1790]['ens']:,} enslaved people. These are the least "
                       "reliable figures on this page. The household rows account "
                       f"for only {round(c[1790]['pop']/CITYPOP_1790*100)} per cent "
                       "of the population the census itself recorded for the city, "
                       "so treat every 1790 number as a floor with materially lower "
                       "confidence than the rest."))
    E.append(dict(year=1800, kind="census", title="Free and enslaved almost level",
                  text=f"{c[1800]['fb']:,} free Black Baltimoreans against "
                       f"{c[1800]['ens']:,} enslaved. In ten years the free "
                       "population had gone from a few hundred to nearly the size "
                       "of the enslaved population. Slaveholding was at its widest "
                       f"reach in the city this year, in {sh[1800]['pct_sh']:.1f} "
                       "per cent of all households, and it never reached that far "
                       "again."))
    E.append(dict(year=1810, kind="census", title="Slavery peaks and stops growing",
                  text=f"{c[1810]['ens']:,} enslaved people, the largest number "
                       "Baltimore ever recorded. Free Black residents pass them "
                       f"this year at {c[1810]['fb']:,}. From here the two lines "
                       "move apart in opposite directions for fifty years."))
    E.append(dict(year=1819, kind="directory",
                  title="The earliest year we can map",
                  text="Jackson's Baltimore Directory lists Black householders "
                       "with addresses. " + dirline(1819) + " The addresses mostly "
                       "say near something rather than giving a corner, which is "
                       "why so few of them resolve. This year exists on borrowed "
                       "labour, transcribed from the page by Louis S. Diggs, Sr."))
    E.append(dict(year=1820, kind="census",
                  title="The peak: 23.4 per cent of the city",
                  text=f"{c[1820]['fb']:,} free Black residents and "
                       f"{c[1820]['ens']:,} enslaved, together "
                       f"{c[1820]['pct']:.1f} per cent of Baltimore. This is the "
                       "highest Black share the city ever records in this period. "
                       "It is also the first year with a printed ward table, which "
                       "used twelve wards rather than the twenty in use by 1850."))
    E.append(dict(year=1822, kind="directory", title="Marked with a dagger",
                  text="Keenan's directory prints no separate section. Instead a "
                       "dagger precedes certain names. " + dirline(1822) +
                       " The meaning of the dagger is inferred from occupations and "
                       "addresses rather than stated, because the page carrying the "
                       "legend is not legible in the scan we have."))
    E.append(dict(year=1830, kind="census", title="Growth on both sides of the line",
                  text=f"{c[1830]['fb']:,} free Black residents, up more than "
                       "four thousand in a decade, and "
                       f"{c[1830]['ens']:,} enslaved, down again. Black share holds "
                       f"near its peak at {c[1830]['pct']:.1f} per cent. Inside the "
                       "houses, the median slaveholding falls from two people to "
                       "one."))
    E.append(dict(year=1840, kind="census", title="Slaveholding becomes marginal",
                  text=f"Slaveholding households are {sh[1840]['pct_sh']:.1f} per "
                       f"cent of the city, down from {sh[1800]['pct_sh']:.1f} per "
                       "cent in 1800. Free Black Baltimoreans number "
                       f"{c[1840]['fb']:,}. Mixed households have fallen to "
                       f"{comp[1840]['pct_mixed']:.0f} per cent of all "
                       "Black-present households, from two thirds in 1800."))
    E.append(dict(year=1842, kind="directory", title="Colored Householders, listed apart",
                  text="Matchett's prints a separate section with a note at the "
                       "front that these residents are listed by themselves. " +
                       dirline(1842) + " Baltimore had no house numbers yet, so "
                       "each person sits on a block face rather than at an "
                       "address."))
    E.append(dict(year=1845, kind="directory", title="House numbers arrive",
                  text="Between 1842 and 1845 the city adopted house numbers and "
                       "the directory changes with it. " + dirline(1845) +
                       " From this volume on, a resident can be placed between two "
                       "named corners instead of somewhere along a block."))
    E.append(dict(year=1850, kind="census", title="The largest free Black city",
                  text=f"{c[1850]['fb']:,} free Black Baltimoreans, more than any "
                       "other American city, and "
                       f"{c[1850]['ens']:,} still enslaved. Black share has fallen "
                       f"to {c[1850]['pct']:.1f} per cent even though the Black "
                       "population grew by more than seven thousand since 1840. "
                       "The city grew faster."))
    E.append(dict(year=1851, kind="directory", title="A decade before the war",
                  text="Matchett's again, with the section closing on an explicit "
                       "line reading END COLORED RESIDENTS. " + dirline(1851) +
                       " A third of the entries give no house number at all and "
                       "cannot be placed."))
    E.append(dict(year=1860, kind="census", title="Falling share, growing city",
                  text=f"{c[1860]['fb']:,} free Black residents and "
                       f"{c[1860]['ens']:,} enslaved, "
                       f"{c[1860]['pct']:.1f} per cent of Baltimore. The Black "
                       "share fell in every one of the twenty wards over the "
                       "previous decade. The Black population itself fell by under "
                       "two per cent while 43,854 white residents arrived."))
    E.append(dict(year=1861, kind="context", title="The wards are redrawn",
                  text="Baltimore redivides itself, so ward numbers after this "
                       "date do not mean what they meant in 1850 and 1860. This is "
                       "why the 1868 map and the 1869 building figures are drawn on "
                       "a different boundary set from the census maps. Not a "
                       "figure from this data, but necessary for reading it."))
    E.append(dict(year=1864, kind="context", title="Maryland abolishes slavery",
                  text="The new state constitution took effect on 1 November 1864 "
                       "and freed the people the 1860 census had counted as "
                       "property. Nothing in this database records that moment. It "
                       "sits between the last census on this page and the last "
                       "directory, and it is the reason the two look so "
                       "different."))
    E.append(dict(year=1868, kind="directory", title="After emancipation",
                  text="Wood's directory devotes 64 printed pages to the section "
                       "that ran 31 pages in 1860. " + dirline(1868) +
                       " The listed population has doubled in eight years. "
                       "Emancipation and wartime migration are visible in the page "
                       "count before any analysis begins."))
    return E


# ----------------------------------------------------------------- main -----

def main():
    if not DB.exists():
        sys.exit(f"missing {DB}, run scripts/build_database.py first")
    con = sqlite3.connect(DB)

    ens_years = [str(y) for (y,) in con.execute(
        "SELECT DISTINCT year FROM enslaved ORDER BY year")]
    D = {
        "city": city_series(con),
        "wards": ward_rows(con),
        "composition": composition(con),
        "slaveholding": slaveholding(con),
        "enslaved": {y: enslaved_profile(con, int(y)) for y in ens_years},
        "enslavedYears": ens_years,
        "holdings": {y: holding_sizes(con, int(y)) for y in ens_years},
        "placed": placed_counts(con),
        "listed": listed_counts(),
    }
    if not D["city"]:
        sys.exit("city_year is empty, rebuild the database before running this")
    D["wardYears"] = sorted(D["wards"])

    e50, e60 = D["enslaved"]["1850"], D["enslaved"]["1860"]
    printed = dict(con.execute(
        "SELECT year, SUM(slave) FROM ward_census GROUP BY year"))
    hold1 = next(h for h in D["holdings"]["1850"] if h["band"] == "1 person")
    hold11 = next(h for h in D["holdings"]["1850"] if h["band"] == "11 or more")
    M = {
        "ens_total": e50["total"], "ens_holds": e50["holds"],
        "ens_total_60": e60["total"],
        "m50": e50["m"], "f50": e50["f"],
        "fpct50": e50["f"] / e50["total"] * 100,
        "fpct60": e60["f"] / e60["total"] * 100,
        "printed_1850_slave": printed[1850],
        "printed_1860_slave": printed[1860],
        "hold1_people": hold1["people"],
        "hold1_pct": hold1["people"] / e50["total"] * 100,
        "hold11_people": hold11["people"],
    }
    D["events"] = build_events(D)
    con.close()

    # report the recomputation against docs/HOUSEHOLDS.md so a drift is visible
    print("household composition, recomputed from data/baltimore.db")
    print(f"{'year':>6} {'blk-only':>9} {'people':>8} {'mixed':>7} {'people':>8} "
          f"{'%mixed':>7} {'blk mean':>9} {'mix mean':>9} {'%ppl mixed':>11}")
    for r in D["composition"]:
        print(f"{r['year']:>6} {r['bh']:>9,} {r['bp']:>8,} {r['mh']:>7,} "
              f"{r['mp']:>8,} {r['pct_mixed']:>6.1f}% {r['b_mean']:>9.2f} "
              f"{r['m_mean']:>9.2f} {r['pct_people_mixed']:>10.1f}%"
              + ("   [1790 unreliable]" if r["flag"] else ""))
    bad = [r["year"] for r in D["composition"] if r["negwhite"]]
    if bad:
        print(f"  WARNING: rows with free-Black count above free-person count "
              f"in {bad}")
    for y, ipums, pr in ((1850, M["ens_total"], M["printed_1850_slave"]),
                         (1860, M["ens_total_60"], M["printed_1860_slave"])):
        print(f"\n{y} enslaved cross-check: IPUMS slave schedule {ipums:,} vs "
              f"printed ward tables {pr:,} "
              f"({abs(ipums - pr) / pr * 100:.2f}% apart)")

    PAYLOAD_OUT.parent.mkdir(parents=True, exist_ok=True)
    PAYLOAD_OUT.write_text(json.dumps(D, indent=1), encoding="utf8")
    print(f"wrote {PAYLOAD_OUT.relative_to(ROOT)}")

    # the page only needs the table data, not the prose it already carries
    slim = {k: D[k] for k in ("city", "wards", "wardYears", "composition",
                              "slaveholding", "enslavedYears")}
    slim["enslaved"] = {y: {"rows": v["rows"]}
                        for y, v in D["enslaved"].items()}
    payload = json.dumps(slim, separators=(",", ":")).replace("</", "<\\/")

    tpl = TPL.read_text(encoding="utf8")
    # slip the page-specific CSS in ahead of the .page marker so document()
    # lands it inside <head> rather than in the body
    tpl = tpl.replace('<div class="page">', EXTRA_CSS + '<div class="page">', 1)

    h1 = "A timeline of Black Baltimore"
    lede = ("Eight censuses and seven city directories, 1790 to 1868, with the "
            "household data behind them.")
    desc = ("Black Baltimore 1790-1868: population, household composition and "
            "slaveholding, from the federal censuses and IPUMS microdata.")
    body = (tpl
            .replace("__TITLE__", "Timeline — Black Baltimore")
            .replace("__NAV__", nav_html("timeline.html"))
            .replace("__EYEBROW__", "Censuses and directories, 1790–1868")
            .replace("__H1__", h1)
            .replace("__LEDE__", lede)
            .replace("__CONTENT__", build_body(D, M))
            .replace("__SCRIPT__", PAGE_JS.replace("__DATA__", payload)))

    OUT.write_text(document(body, h1, desc), encoding="utf8")
    print(f"wrote docs/{OUT.name} ({OUT.stat().st_size/1_000:.0f} KB)")


if __name__ == "__main__":
    main()
