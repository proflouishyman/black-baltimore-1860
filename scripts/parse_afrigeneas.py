#!/usr/bin/env python3
"""Parse the AfriGeneas transcriptions of Baltimore's early Black householders.

Two directories that our own OCR either could not reach or could not read well
were transcribed by hand decades ago and put online:

  1819  Jackson's Baltimore Directory, "Colored Householders"
  1822-23  Keenan's Baltimore Directory, "persons of color" (A-L and M-Z)

Both were transcribed by Louis S. Diggs, Sr. and published by AfriGeneas. They
are strictly better than what we can get from the scans: our own OCR of the
1822 Keenan volume placed only 8 of 213 addresses, because the type is small
and the addresses are dense with abbreviations. A human read them correctly.
1819 we had no route to at all.

The transcriptions preserve the period address grammar in full, including the
side of the street, which the 1842 volume mostly omits:

    Ackerman, James, caulker, Potter e side n of Pitt ot
    Allen, Sarah, laundress, Argyle al. n Fleet st fp

Trailing tokens are neighbourhoods, not part of the street: ot = Old Town,
fp = Fell's Point, fh = Federal Hill, sg = Spring Gardens, ra = Ridgely's
Addition, hc = Hampstead/Canton, wp = William's Purchase, gh = Gallows Hill.

Output uses the same CSV contract as parse_directory.py so everything
downstream is unchanged.
"""

import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
WORK = ROOT / "data" / "work"

FIELDS = ["year", "source_id", "surname", "given", "occupation",
          "addr_type", "house_no", "street", "bearing", "cross_street", "side",
          "dwelling_raw", "addr_raw", "raw_line"]

SOURCES = {
    "afrigeneas_1819": {"year": 1819, "files": ["afrigeneas_1819.html"]},
    "afrigeneas_1822": {"year": 1822,
                        "files": ["afrigeneas_1822-23.html", "afrigeneas_1822-23b.html"]},
}

# neighbourhood tags that trail an address and must not be read as street names
HOODS = r"(?:ot|fp|fh|sg|ra|hc|wp|gh|op|nl)"
BEARING = r"(?:n|s|e|w|ne|nw|se|sw|north|south|east|west)"

# a transcribed entry starts "Surname, Given, ..." or "Surname, occupation, ..."
ENTRY_RE = re.compile(r"^[A-Z][A-Za-z'’\-\.]+,\s+\S")
# lines that are section letters, headers or transcriber notes
SKIP_RE = re.compile(r"^(?:[A-Z]|Louis S\. Diggs|Catonsville|The following|"
                     r"This ends|Return to|Back to|AfriGeneas|Transcribed|"
                     r"Copyright|Baltimore Directory|\W*)$", re.I)


def page_lines(path):
    raw = path.read_bytes().decode("latin-1")
    txt = html.unescape(re.sub(r"<[^>]+>", "\n", raw))
    return [re.sub(r"\s+", " ", l).strip() for l in txt.split("\n") if l.strip()]


def join_wrapped(lines):
    """A few entries wrap; a line that does not start a new entry continues."""
    out = []
    for l in lines:
        if ENTRY_RE.match(l) or not out:
            out.append(l)
        else:
            out[-1] += " " + l
    return out


def strip_hood(addr):
    """Remove trailing neighbourhood tags and transcriber uncertainty marks."""
    a = re.sub(r"\(\?+\)", " ", addr)
    a = re.sub(rf"[,\s]+{HOODS}\b\.?\s*$", "", a, flags=re.I)
    a = re.sub(rf"[,\s]+{HOODS}\b\.?(?=[,\s])", " ", a, flags=re.I)
    return re.sub(r"\s+", " ", a).strip(" .,")


def split_address(addr):
    rec = {"addr_type": "unknown", "house_no": "", "street": "",
           "bearing": "", "cross_street": "", "side": ""}
    a = strip_hood(addr)
    if not a:
        return rec

    # corner entries: "cor. Gough st. & Star alley"
    m = re.match(r"^cor\.?\s+(.+?)\s*[&x]\s*(.+)$", a, re.I)
    if m:
        rec.update({"addr_type": "corner", "street": m.group(1).strip(" .,"),
                    "cross_street": m.group(2).strip(" .,")})
        return rec

    # 1819 mostly says "near X" instead of giving a bearing from a corner
    m_near = re.match(r"^(.+?)[,\s]+(?:near|opposite|opp\.?|adjoining)\s+(.+)$", a, re.I)
    if m_near and not re.search(rf"\b{BEARING}\.?\s+of\b", a, re.I):
        rec.update({"addr_type": "near", "street": m_near.group(1).strip(" .,"),
                    "cross_street": m_near.group(2).strip(" .,")})
        m_no = re.match(r"^(\d+)\s+(.*)$", rec["street"])
        if m_no:
            rec["house_no"], rec["street"] = m_no.group(1), m_no.group(2)
        return rec

    m_side = re.search(rf"\b({BEARING})\.?\s+side\b", a, re.I)
    if m_side:
        rec["side"] = m_side.group(1).lower()[:1]
        a = (a[:m_side.start()] + " " + a[m_side.end():]).strip(" .,")

    # relative: "<street> <bearing> of <cross street>"
    m = re.search(rf"\b({BEARING})\.?\s+(?:of|off)\b\s*(.*)$", a, re.I)
    if m:
        rec.update({"addr_type": "relative", "bearing": m.group(1).lower()[:1],
                    "cross_street": m.group(2).strip(" .,"),
                    "street": a[:m.start()].strip(" .,")})
    else:
        # "Argyle al. n Fleet st" - bearing with the 'of' left out
        m = re.search(rf"\b({BEARING})\.?\s+(?=[A-Z])(.*)$", a)
        if m and m.group(2):
            rec.update({"addr_type": "relative", "bearing": m.group(1).lower()[:1],
                        "cross_street": m.group(2).strip(" .,"),
                        "street": a[:m.start()].strip(" .,")})
        else:
            rec.update({"addr_type": "street_only", "street": a})

    m_no = re.match(r"^(\d+)\s+(.*)$", rec["street"])
    if m_no:
        rec["house_no"], rec["street"] = m_no.group(1), m_no.group(2)
        if rec["addr_type"] == "street_only":
            rec["addr_type"] = "numbered"
    return rec


# an address can open with a lowercase word, so a lowercase field is only an
# occupation if it is not one of these openers
ADDR_OPEN = re.compile(r"^(?:cor\b|corner\b|near\b|opposite\b|opp\b|rear\b|"
                       r"end\b|foot\b|head\b|side\b|back\b|\d|[nsew]\.?\s|"
                       r"[nsew]\.?\s*(?:side|end|of)\b)", re.I)


def parse_entry(line, year, source_id):
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        return None
    surname = parts[0].strip(" .")
    rest = parts[1:]

    # second field is a given name unless it reads as an occupation or address
    given = ""
    if rest and re.match(r"^[A-Z][A-Za-z'’\-\.]*\.?$", rest[0]) and len(rest) > 1:
        given, rest = rest[0], rest[1:]

    # These transcriptions put the trade in its own field, lowercase, and the
    # address in everything after it. 1819 splits the address across further
    # commas ("German, near Market, fp"), so the address is the remainder
    # rejoined rather than the last field alone.
    occ = ""
    if rest and rest[0][:1].islower() and not ADDR_OPEN.match(rest[0]):
        occ, rest = rest[0], rest[1:]
    addr = ", ".join(rest)

    rec = split_address(addr)
    rec.update({"year": year, "source_id": source_id, "surname": surname,
                "given": given.strip(" ."), "occupation": occ,
                "dwelling_raw": "", "addr_raw": addr, "raw_line": line})
    return rec


def run(key):
    cfg = SOURCES[key]
    lines = []
    for f in cfg["files"]:
        lines += page_lines(RAW / f)
    rows = []
    for e in join_wrapped(lines):
        if SKIP_RE.match(e) or len(e) < 12 or not ENTRY_RE.match(e):
            continue
        # institutions, not householders
        if re.match(r"^(African|Bethel|Sharp|Union)\s", e) and "church" in e.lower():
            continue
        r = parse_entry(e, cfg["year"], key)
        if r and r["surname"] and r["addr_raw"]:
            rows.append(r)

    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / f"{key}_people.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    kinds = {}
    for r in rows:
        kinds[r["addr_type"]] = kinds.get(r["addr_type"], 0) + 1
    print(f"{key} ({cfg['year']}): {len(rows)} records -> {out.name}")
    for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
        print(f"    {k:14s} {v:5d}")
    return rows


if __name__ == "__main__":
    for k in SOURCES:
        run(k)
