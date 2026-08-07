#!/usr/bin/env python3
"""Parse the segregated Black-resident sections of Baltimore city directories
(archive.org OCR text) into structured, geocodable records.

Two distinct address grammars appear across the period, and the parser must
handle both because they demand different geocoding strategies downstream:

  numbered  -- "Adams Dennis, coachman, 11 Temple"
               house number + street. Geocodable by address interpolation
               along a street segment. Dominant from ~1850 on.

  relative  -- "Barnet Stephen, caulker, Wolfe st s of Fleet"
               street + bearing + cross street (sometimes + side of street).
               Geocodable only to a block face: the stretch of one street
               between two intersections. Dominant before ~1850, because
               Baltimore had no systematic house numbering yet.

Output is one CSV per source directory with a stable column contract (see
FIELDS). Downstream geocoding consumes that contract and nothing else.
"""

import csv
import re
import sys
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
WORK = Path(__file__).resolve().parent.parent / "data" / "work"

# Stable output contract. Do not reorder or rename without updating docs/.
FIELDS = [
    "year", "source_id", "surname", "given", "occupation",
    "addr_type", "house_no", "street", "bearing", "cross_street", "side",
    "dwelling_raw", "addr_raw", "raw_line",
]

# Section bounds per directory. The Black-resident listing is a physically
# separate part of each book, marked by a running page header; we locate the
# first and last occurrence of that header and take everything between.
SOURCES = {
    "woodsbaltimoreci1860balt": {
        "year": 1860,
        "header": r"^\s*COLORED\s+PERSONS[.,]?\s*$",
        "end": None,
        "marker": None,
    },
    "matchettsbaltimo1842balt": {
        "year": 1842,
        # This header appears only on the section title page, not as a running
        # head, so the section must be closed by its terminator instead.
        "header": r"^\s*COLORED\s+HOUSEHOLDERS[.,]?\s*$",
        "end": r"^\s*APPENDIX\s*$",
        "marker": None,
    },
    "baltimoredirecto1822keen": {
        "year": 1822,
        # Keenan's 1822 has no separate section; free people of colour are
        # flagged inline by a lowercase "f" prefix on the entry.
        "header": None,
        "end": None,
        "marker": r"^f\s*(?=[A-Z])",
    },
}

# Street-type tokens the OCR renders inconsistently; used to find where the
# street name ends and the cross-street clause begins.
ST_SUFFIX = r"(?:st|street|al|alley|la|lane|av|ave|avenue|road|rd|court|ct|wharf|row)"
BEARING = r"(?:n|s|e|w|ne|nw|se|sw|north|south|east|west)"


def join_wrapped(lines):
    """OCR breaks long entries across lines. Rejoin continuations.

    A new entry begins on a line that starts with a capitalised surname *and*
    contains a comma. Both halves of that test are needed: directories differ
    on whether the comma follows the surname ("Ailand, Harriot," in 1822) or
    the full name ("Adams Benjamin," in 1860), while true continuations are
    either lowercase fragments ("atoga, dw 214 Montgomery") or bare
    capitalised street names with no comma ("Chesnut").
    """
    out = []
    start = re.compile(r"^(?:f\s*)?[A-Z][A-Za-z'’\-]+")
    for ln in lines:
        s = " ".join(ln.split())
        if not s:
            continue
        if (start.match(s) and "," in s) or not out:
            out.append(s)
        elif out[-1].endswith("-"):
            out[-1] = out[-1][:-1] + s     # word split across a line break
        else:
            out[-1] += " " + s
    return out


def split_address(addr):
    """Classify an address string and pull out its components."""
    a = addr.strip(" .,")
    rec = {"addr_type": "unknown", "house_no": "", "street": "",
           "bearing": "", "cross_street": "", "side": ""}
    if not a:
        return rec

    # side-of-street clause, e.g. "e side" / "w. side"
    m_side = re.search(rf"\b({BEARING})\.?\s+side\b", a, re.I)
    if m_side:
        rec["side"] = m_side.group(1).lower().rstrip(".")
        a = (a[:m_side.start()] + " " + a[m_side.end():]).strip()

    # relative: "<street> <bearing> of <cross street>"
    m_rel = re.search(rf"\b({BEARING})\.?\s+(?:of|oi|ot)\b\s*(.*)$", a, re.I)
    if m_rel:
        rec["addr_type"] = "relative"
        rec["bearing"] = m_rel.group(1).lower().rstrip(".")
        rec["cross_street"] = m_rel.group(2).strip(" .,")
        rec["street"] = a[:m_rel.start()].strip(" .,")
        # a leading house number can still appear before a relative clause
        m_no = re.match(r"^(\d+)\s+(.*)$", rec["street"])
        if m_no:
            rec["house_no"], rec["street"] = m_no.group(1), m_no.group(2)
        return rec

    # numbered: "<house no> <street>"
    m_no = re.match(r"^(\d+)\s*[½|]?\s+(.+)$", a)
    if m_no:
        rec["addr_type"] = "numbered"
        rec["house_no"] = m_no.group(1)
        rec["street"] = m_no.group(2).strip(" .,")
        return rec

    # bare street name with no locator
    if re.search(rf"\b{ST_SUFFIX}\b", a, re.I) or a:
        rec["addr_type"] = "street_only"
        rec["street"] = a
    return rec


def parse_entry(line, year, source_id):
    """Split one directory entry into name / occupation / address parts."""
    raw = line
    line = re.sub(r"^f\s*", "", line)          # strip the free-colour flag
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        return None

    # "Surname Given" or "Surname, Given" depending on the directory's style
    head = parts[0]
    m = re.match(r"^([A-Z][A-Za-z'’\-]+)\s+(.*)$", head)
    if m:
        surname, given = m.group(1), m.group(2)
    else:
        surname, given = head, ""
    rest = parts[1:]
    if not given and rest:
        given, rest = rest[0], rest[1:]

    # A "dw" (dwelling) clause means the preceding address is the workplace and
    # the dw address is the home. For residential density the dw wins.
    tail = ", ".join(rest)
    dwelling = ""
    m_dw = re.search(r"\bdw\.?\s*(.*)$", tail, re.I)
    if m_dw:
        dwelling = m_dw.group(1).strip(" .,")
        tail = tail[:m_dw.start()].strip(" .,")

    # Matchett's often separates occupation from address with a period rather
    # than a comma ("Adams Charles, labourer. Pierce st w of Pearl"), which
    # would otherwise leave "labourer." glued to the street name and break
    # street matching. Split on ". " only where a lowercase word is followed by
    # a capitalised one, so real abbreviations survive: "Penn. avenue" is not
    # split (next word is lowercase) and neither is "L. Sharp st" (previous
    # token is a capital initial).
    tail = re.sub(r"\b([a-z]{3,})\.\s+(?=[A-Z])", r"\1, ", tail)

    seg = [s.strip() for s in tail.split(",") if s.strip()]
    # the address is the last comma-segment containing a digit or street word;
    # everything before it is occupation
    addr, occ = "", ""
    if seg:
        addr = seg[-1]
        occ = ", ".join(seg[:-1])
    # if the "occupation" itself looks like an address and addr doesn't, swap
    if occ and re.match(r"^\d", occ) and not re.search(r"\d", addr):
        occ, addr = addr, occ

    target = dwelling if dwelling else addr
    rec = split_address(target)
    rec.update({
        "year": year, "source_id": source_id,
        "surname": surname, "given": given.strip(" .,"),
        "occupation": occ, "dwelling_raw": dwelling,
        "addr_raw": target, "raw_line": raw,
    })
    return rec


def extract_section(text, cfg):
    lines = text.split("\n")
    if cfg["header"]:
        hdr = re.compile(cfg["header"])
        idx = [i for i, l in enumerate(lines) if hdr.match(l)]
        if not idx:
            return []
        stop = idx[-1] + 250
        if cfg.get("end"):
            end_re = re.compile(cfg["end"])
            after = [i for i, l in enumerate(lines) if i > idx[0] and end_re.match(l)]
            if after:
                stop = after[0]
        seg = lines[idx[0]: stop]
        seg = [l for l in seg if not hdr.match(l)]
        return join_wrapped(seg)
    # marker-based (1822): keep only flagged entries
    mk = re.compile(cfg["marker"])
    joined = join_wrapped(lines)
    return [l for l in joined if mk.match(l)]


def run(source_id):
    cfg = SOURCES[source_id]
    path = RAW / f"{source_id}.txt"
    text = path.read_text(encoding="utf8", errors="ignore")
    entries = extract_section(text, cfg)

    rows = []
    for e in entries:
        # drop page furniture and advertising noise
        if len(e) < 12 or re.match(r"^[A-Z\s.,'&]+$", e):
            continue
        r = parse_entry(e, cfg["year"], source_id)
        if r and r["surname"] and r["addr_raw"]:
            rows.append(r)

    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / f"{source_id}_people.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    kinds = {}
    for r in rows:
        kinds[r["addr_type"]] = kinds.get(r["addr_type"], 0) + 1
    print(f"{source_id} ({cfg['year']}): {len(rows)} records -> {out.name}")
    for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
        print(f"    {k:12s} {v:5d}")
    return rows


if __name__ == "__main__":
    targets = sys.argv[1:] or list(SOURCES)
    for s in targets:
        run(s)
