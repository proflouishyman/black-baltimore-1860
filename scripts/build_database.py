#!/usr/bin/env python3
"""Load every dataset in this project into one SQLite database.

Until now each stage of the pipeline wrote its own file in its own format:
GeoJSON for placed people, CSV for ward tables and validation rounds, JSON for
census links, and 2.6 GB of IPUMS microdata that has to be streamed in chunks
every time anyone wants a single number out of it. Answering a question that
crosses two of those - "what did the people we can actually trace do for a
living, by ward" - meant writing a script.

This builds `data/baltimore.db`, where that question is a join.

The database is a DERIVED artifact. It is rebuilt from scratch on every run and
nothing should ever be edited in it directly; fix the upstream file and re-run.
It is small enough (a few MB) to commit, unlike the raw microdata, which stays
out of the repo and is documented in data/MANIFEST.md instead.

## Schema contract

people          one row per directory record we placed on a map
                (id, year, source, surname, given, occupation, house_no,
                 street_raw, street_matched, side, confidence, ward, lat, lon,
                 category, subtype)

households      one row per Baltimore household, 1790-1840, from the IPUMS
                complete-count files
                (year, serial, n_free, n_slave, n_total, n_othfree,
                 free_black, white)

enslaved        one row per enslaved person recorded in Baltimore on the 1850
                and 1860 slave schedules
                (year, holdnum, slavenum, sizehold, age, sex, race,
                 fugitive, manumitted)
                fugitive/manumitted are NULL for 1850: that schedule did not
                ask, which is not the same fact as asking and being told no

ward_census     printed federal census ward tables, transcribed by hand and
                reconciled against the printed totals
                (year, ward, white, free_colored, slave, black_total,
                 aggregate, black_pct)

census_links    residents traced into the 1860 census, with the ward the
                census assigned independently of our geocoding
                (year, surname, given, our_ward, census_ward, agree, age, sex,
                 colour, occupation, confidence, url, accessed)

city_year       one row per census year: the city-level totals, so a timeline
                can be drawn without touching the microdata
                (year, households, population, free, enslaved, free_black,
                 black_total, black_pct, source)

Output: data/baltimore.db
"""

import csv
import json
import sqlite3
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "baltimore.db"

# Directory years we geocoded, and the source volume each came from. The
# source string is what appears on the site, so it stays human-readable.
YEAR_SOURCE = {
    1819: "Woolfolk/AfriGeneas transcription, 1819",
    1822: "Keenan's Baltimore Directory, 1822",
    1842: "Matchett's Baltimore Director, 1842",
    1845: "Baltimore Directory, 1845",
    1851: "Matchett's Baltimore Director, 1851",
    1860: "Wood's Baltimore City Directory, 1860",
    1868: "Wood's Baltimore City Directory, 1868",
}

# Baltimore City in the IPUMS complete-count files. Verified by matching the
# citypop tag against the known city population in every year 1790-1840; see
# docs/HOUSEHOLDS.md. stateicp 52 is Maryland - 21 is Illinois, a trap that
# produced a plausible-looking but entirely wrong series before it was caught.
BALT = {"stateicp": 52, "county": 50, "city": 530}

SCHEMA = """
DROP TABLE IF EXISTS people;
CREATE TABLE people (
  id INTEGER PRIMARY KEY,
  year INTEGER NOT NULL,
  source TEXT,
  surname TEXT,
  given TEXT,
  occupation TEXT,
  house_no INTEGER,
  street_raw TEXT,
  street_matched TEXT,
  side TEXT,
  confidence TEXT,
  ward INTEGER,
  lat REAL,
  lon REAL,
  category TEXT,
  subtype TEXT
);

DROP TABLE IF EXISTS households;
CREATE TABLE households (
  year INTEGER NOT NULL,
  serial INTEGER,
  n_free INTEGER,
  n_slave INTEGER,
  n_total INTEGER,
  n_othfree INTEGER,
  free_black INTEGER,
  white INTEGER
);

DROP TABLE IF EXISTS enslaved;
CREATE TABLE enslaved (
  year INTEGER NOT NULL,
  holdnum INTEGER,
  slavenum INTEGER,
  sizehold INTEGER,
  age REAL,
  sex INTEGER,
  race INTEGER,
  fugitive INTEGER,
  manumitted INTEGER
);

DROP TABLE IF EXISTS ward_census;
CREATE TABLE ward_census (
  year INTEGER NOT NULL,
  ward INTEGER NOT NULL,
  white INTEGER,
  free_colored INTEGER,
  slave INTEGER,
  black_total INTEGER,
  aggregate INTEGER,
  black_pct REAL
);

DROP TABLE IF EXISTS census_links;
CREATE TABLE census_links (
  year INTEGER,
  surname TEXT,
  given TEXT,
  our_ward INTEGER,
  census_ward INTEGER,
  agree INTEGER,
  age TEXT,
  sex TEXT,
  colour TEXT,
  occupation TEXT,
  confidence TEXT,
  url TEXT,
  accessed TEXT
);

DROP TABLE IF EXISTS city_year;
CREATE TABLE city_year (
  year INTEGER PRIMARY KEY,
  households INTEGER,
  population INTEGER,
  free INTEGER,
  enslaved INTEGER,
  free_black INTEGER,
  black_total INTEGER,
  black_pct REAL,
  source TEXT
);
"""

INDEXES = """
CREATE INDEX ix_people_year ON people(year);
CREATE INDEX ix_people_name ON people(surname, given);
CREATE INDEX ix_people_ward ON people(year, ward);
CREATE INDEX ix_people_street ON people(street_matched);
CREATE INDEX ix_people_conf ON people(confidence);
CREATE INDEX ix_hh_year ON households(year);
CREATE INDEX ix_ens_year ON enslaved(year);
CREATE INDEX ix_ward_year ON ward_census(year, ward);
CREATE INDEX ix_links_name ON census_links(surname, given);
"""


def load_categories():
    """category/subtype keyed by (source_id, row) from classify_records.py."""
    out = {}
    f = WORK / "record_categories.csv"
    if not f.exists():
        return out
    for r in csv.DictReader(open(f)):
        try:
            out[(str(r["source_id"]), int(r["row"]))] = (r.get("category"),
                                                         r.get("subtype"))
        except (ValueError, KeyError):
            continue
    return out


def load_people(con):
    """Every placed directory record, one row each, with ward where known."""
    cats = load_categories()
    rows, pid = [], 0

    for year, source in sorted(YEAR_SOURCE.items()):
        f = WORK / f"people_{year}_geocoded.geojson"
        if not f.exists():
            print(f"  people {year}: MISSING {f.name}")
            continue
        g = gpd.read_file(f)

        # Ward comes from a separate spatial join and only exists for 1860.
        # Match on name + house number rather than row order, because the ward
        # file drops records that fall outside every ward polygon and the
        # indices no longer line up.
        wards = {}
        wf = WORK / f"people_{year}_wards.geojson"
        if wf.exists():
            gw = gpd.read_file(wf)
            for _, r in gw.iterrows():
                w = r.get("Ward_Num")
                if w is None or str(w) == "nan":
                    continue
                k = (str(r.get("surname") or "").strip().lower(),
                     str(r.get("given") or "").strip().lower(),
                     r.get("house_no"))
                wards.setdefault(k, int(float(w)))

        for i, r in g.iterrows():
            geom = r.geometry
            lat = lon = None
            if geom is not None and not geom.is_empty:
                lon, lat = geom.x, geom.y
            k = (str(r.get("surname") or "").strip().lower(),
                 str(r.get("given") or "").strip().lower(),
                 r.get("house_no"))
            cat, sub = cats.get((str(year), int(i)), (None, None))
            hn = r.get("house_no")
            try:
                hn = int(hn) if hn is not None and str(hn) != "nan" else None
            except (TypeError, ValueError):
                hn = None
            pid += 1
            rows.append((pid, year, source,
                         r.get("surname"), r.get("given"), r.get("occupation"),
                         hn, r.get("street_raw"), r.get("street_matched"),
                         r.get("side"), r.get("confidence"),
                         wards.get(k), lat, lon, cat, sub))
        print(f"  people {year}: {len(g)} records")

    con.executemany("INSERT INTO people VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    rows)
    return len(rows)


# Free-Black count columns per year. These MUST be keyed by year, not by which
# columns exist: IPUMS ships an identical 134-column schema for every file, so
# all twenty nbm*/nbf* columns are present in 1790 even though the 1790 census
# never collected them, and they are all zero. Selecting columns by existence
# therefore sums to zero and silently reports no free Black population at all.
#
# The three schemes are three different census categories and must not be read
# as one continuous variable:
#   1790-1810  no race-labelled column exists; `nothfree` ("other free persons
#              except Indians not taxed") is the standard historians' proxy
#   1820       four age bands, labelled "Colored"
#   1830-1840  six differently-cut age bands, labelled "Black"
BLACK_BANDS = {
    1820: ["nbmlt14", "nbm14", "nbm26", "nbm45",
           "nbflt14", "nbf14", "nbf26", "nbf45"],
    1830: ["nbmlt10", "nbm10", "nbm24", "nbm36", "nbm55", "nbm100",
           "nbflt10", "nbf10", "nbf24", "nbf36", "nbf55", "nbf100"],
}
BLACK_BANDS[1840] = BLACK_BANDS[1830]


def black_columns(year, cols):
    """Columns holding the free-Black count for `year`, or [] to use nothfree."""
    return [c for c in BLACK_BANDS.get(year, []) if c in cols]


def load_households(con):
    """Baltimore City households from the IPUMS complete-count files."""
    total = 0
    for year in (1790, 1800, 1810, 1820, 1830, 1840):
        f = RAW / f"H_{year}.csv"
        if not f.exists():
            print(f"  households {year}: MISSING (see data/MANIFEST.md)")
            continue
        keep, n = [], 0
        for chunk in pd.read_csv(f, chunksize=300_000, low_memory=False):
            sub = chunk[(chunk["stateicp"] == BALT["stateicp"]) &
                        (chunk["county"] == BALT["county"]) &
                        (chunk["city"] == BALT["city"])]
            if sub.empty:
                continue
            bcols = black_columns(year, sub.columns)
            fb = (sub[bcols].sum(axis=1) if bcols
                  else sub["nothfree"].fillna(0).astype(int))
            # White age bands OVERLAP in some years (1820's nwm1618 is nested
            # inside nwm16), so summing the nwm*/nwf* columns double-counts.
            # numperhh is the total FREE persons in the household, so the free
            # white count is that minus the free Black count, which is exact by
            # construction and immune to the band problem.
            white = sub["numperhh"] - fb
            for row in zip(sub["serial"], sub["numperhh"], sub["nslave"],
                           sub["ntotal"], sub.get("nothfree", pd.Series(0, index=sub.index)),
                           fb, white):
                keep.append((year,) + tuple(int(x) if pd.notna(x) else None
                                            for x in row))
            n += len(sub)
        con.executemany(
            "INSERT INTO households VALUES (?,?,?,?,?,?,?,?)", keep)
        total += n
        print(f"  households {year}: {n} Baltimore households")
    return total


def load_enslaved(con):
    """Baltimore rows from the 1850/1860 slave-schedule full-count files."""
    total = 0
    for year, names in ((1850, ["slave_1850.dta"]),
                        (1860, ["slave_1860.dta", "slave_1860_v1.dta",
                                "slave_1860_v2.dta"])):
        path = next((RAW / n for n in names if (RAW / n).exists()), None)
        if path is None:
            print(f"  enslaved {year}: MISSING (see data/MANIFEST.md)")
            continue
        keep, n = [], 0
        # convert_categoricals=False is required: several value-label sets in
        # these files are non-unique and pandas refuses to build categoricals.
        reader = pd.read_stata(path, convert_categoricals=False,
                               chunksize=200_000)
        for chunk in reader:
            # The slave schedules code `county` differently from the household
            # files: 520310-style (stateicp concatenated with the county code)
            # rather than the bare 50 that identifies Baltimore in H_*.csv.
            # Filtering on county here silently returns zero rows. `city` uses
            # the SAME code in both (530), and within Maryland it is unique -
            # confirmed by its citypop tag of 169,054, Baltimore's actual 1850
            # population - so match on state and city only.
            sub = chunk[(chunk["stateicp"] == BALT["stateicp"]) &
                        (chunk["city"] == BALT["city"])]
            if sub.empty:
                continue
            # fugitive_ind/manumit_ind exist only in the 1860 file. They stay
            # NULL for 1850 rather than being coerced to 0, because "the 1850
            # schedule did not ask" and "asked, answered no" are different
            # facts and must not look the same in a query.
            blank = pd.Series([None] * len(sub), index=sub.index)
            for row in zip(sub["holdnum"], sub["slavenum"], sub["sizehold"],
                           sub["age"], sub["sex"], sub["race"],
                           sub.get("fugitive_ind", blank),
                           sub.get("manumit_ind", blank)):
                keep.append((year,) + tuple(
                    None if pd.isna(x) else (float(x) if i == 3 else int(x))
                    for i, x in enumerate(row)))
            n += len(sub)
        con.executemany("INSERT INTO enslaved VALUES (?,?,?,?,?,?,?,?,?)", keep)
        total += n
        print(f"  enslaved {year}: {n} people ({path.name})")
    return total


def load_ward_census(con):
    rows = 0
    for f in sorted(WORK.glob("ward_census_*.csv")):
        year = int(f.stem.split("_")[-1])
        for r in csv.DictReader(open(f)):
            con.execute("INSERT INTO ward_census VALUES (?,?,?,?,?,?,?,?)",
                        (year, int(r["ward"]), int(r["white"]),
                         int(r["free_colored"]), int(r["slave"]),
                         int(r["black_total"]), int(r["aggregate"]),
                         float(r["black_pct"])))
            rows += 1
        print(f"  ward_census {year}: {sum(1 for _ in csv.DictReader(open(f)))} wards")
    return rows


def load_census_links(con):
    f = WORK / "census_links.json"
    if not f.exists():
        return 0
    data = json.loads(f.read_text())
    n = 0
    for k, v in data.items():
        year, surname, given = k.split("|")

        def num(x):
            return int(x) if x and str(x).isdigit() else None

        con.execute("INSERT INTO census_links VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (int(year), surname, given, num(v.get("ward_ours")),
                     num(v.get("ward_census")),
                     None if v.get("agree") is None else int(v["agree"]),
                     v.get("age"), v.get("sex"), v.get("colour"),
                     v.get("occupation"), v.get("confidence"),
                     v.get("url"), v.get("accessed")))
        n += 1
    print(f"  census_links: {n} traced residents")
    return n


def build_city_year(con):
    """City-level totals per census year, so a timeline needs no microdata.

    Two sources feed this and they are kept distinct rather than blended: the
    hand-transcribed printed ward tables (authoritative, reconciled against the
    printed totals) and the IPUMS household microdata (complete-count but
    running slightly under the printed aggregates). Where both exist the
    printed volume wins, because it is what the Census actually published.
    """
    rows = {}

    # microdata first
    for (year, hh, free, slave, total, fb) in con.execute(
            "SELECT year, COUNT(*), SUM(n_free), SUM(n_slave), SUM(n_total), "
            "SUM(free_black) FROM households GROUP BY year"):
        black = (fb or 0) + (slave or 0)
        rows[year] = dict(
            year=year, households=hh, population=total, free=free,
            enslaved=slave, free_black=fb, black_total=black,
            black_pct=round(black / total * 100, 2) if total else None,
            source="IPUMS complete-count household microdata")

    # printed ward tables override
    for (year, white, fc, slave, black, agg) in con.execute(
            "SELECT year, SUM(white), SUM(free_colored), SUM(slave), "
            "SUM(black_total), SUM(aggregate) FROM ward_census GROUP BY year"):
        rows[year] = dict(
            year=year, households=rows.get(year, {}).get("households"),
            population=agg, free=(white or 0) + (fc or 0), enslaved=slave,
            free_black=fc, black_total=black,
            black_pct=round(black / agg * 100, 2) if agg else None,
            source="printed federal census, ward tables")

    for r in sorted(rows.values(), key=lambda x: x["year"]):
        con.execute(
            "INSERT INTO city_year VALUES (?,?,?,?,?,?,?,?,?)",
            (r["year"], r["households"], r["population"], r["free"],
             r["enslaved"], r["free_black"], r["black_total"], r["black_pct"],
             r["source"]))
    print(f"  city_year: {len(rows)} census years")
    return len(rows)


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)

    print("loading people...")
    load_people(con)
    print("loading households (streamed from IPUMS microdata)...")
    load_households(con)
    print("loading enslaved...")
    load_enslaved(con)
    print("loading ward census...")
    load_ward_census(con)
    print("loading census links...")
    load_census_links(con)
    print("building city_year...")
    build_city_year(con)

    con.executescript(INDEXES)
    con.commit()

    print("\n--- table counts ---")
    for t in ("people", "households", "enslaved", "ward_census",
              "census_links", "city_year"):
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t:16s} {n:>9,}")
    con.execute("VACUUM")
    con.close()
    print(f"\nwrote {DB.relative_to(ROOT)} "
          f"({DB.stat().st_size/1_000_000:.1f} MB)")


if __name__ == "__main__":
    sys.exit(main())
