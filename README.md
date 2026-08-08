# Black Baltimore, 1820–1860

Mapping the free and enslaved Black population of Baltimore City from the
surviving city directories, for a public exhibit.

**Live map: https://proflouishyman.github.io/black-baltimore-1860/**

## What this is

Baltimore had the largest free Black population of any city in the United
States before the Civil War. Several of its nineteenth-century city directories
list those residents in a section of their own — "Colored Persons" in Wood's
1860, "Colored Householders" in Matchett's 1842 — with name, occupation and
address. This project parses those sections and puts the people back on the
map.

Current state: **~22,800 residents parsed** across seven directory years
spanning 49 years, **13,081 of them placed** as points or block faces, and the
whole city mapped by ward from the printed censuses of 1820, 1850 and 1860.

The headline finding: **Black Baltimore was 23.40% of the city in 1820, 16.79%
in 1850, and 13.13% in 1860.** A forty-year decline, driven not by Black
departure — the population barely moved — but by white in-migration piling up
around a community that was standing still.

| Year | Directory | Residents parsed | Addressing |
|---|---|---|---|
| 1819 | Jackson's | 526 | relative and "near", hand transcription |
| 1822 | Keenan's | 1,061 | relative, dagger-marked, hand transcription |
| 1842 | Matchett's | 2,724 | relative ("Wolfe st s of Fleet") |
| 1845 | Baltimore Directory | 2,100 | house number + street |
| 1851 | Matchett's | 3,642 | house number + street |
| 1860 | Wood's | 4,251 | house number + street |
| 1868 | Wood's | 8,512 | house number + street |

House numbering arrives between 1842 and 1845, which is why the addressing
column changes. The 1868 section is twice the size of 1860's: emancipation and
wartime migration, visible in the page count alone.

## The two problems this project had to solve

**Baltimore renumbered its houses in the 1880s**, so an 1860 house number does
not correspond to a modern one. That would normally make address-level
geocoding guesswork. It does not here, because Wood's 1860 prints its own
Street Directory (pp. 509–529) giving the house number standing at each cross
street, in Left and Right columns. Its worked example:

> "55 is on the N.E. corner of Charles and Saratoga-sts., hence the desired
> No. 71 will be between Saratoga and Pleasant-sts., right hand."

That is a house-number-to-intersection lookup in 1860 numbering. Residents are
placed by interpolating between two named corners, so an 1860 number is never
compared to a modern one. `scripts/extract_anchors.py` rebuilds that table from
OCR word coordinates, recovering **1,520 anchors across 214 streets**.

**The alleys are gone.** Much of this population lived on alleys — Camel, Pin,
Welcome, Strawberry, Homespun, Lerew's — that no longer exist in modern street
data. Geocoding against a modern basemap silently drops those residents, which
would quietly empty the densest blocks while looking like a clean result. So
the base geometry is the Historical Urban Ecological (HUE) c.1930 Baltimore
street file, which still carries them, clipped to the 1846–1860 ward boundary.

## Honest limits

- The street geometry is a c.1930 survey, not an 1860 one. It is the closest
  layer that retains the alleys, but a properly georeferenced 1860s map is the
  next step and **will move these dots**.
- Only 848 of the placed residents are anchored between two named corners. The
  other 2,020 have a known street and an estimated position along it.
- Directories undercount the poor and the transient. Wood's lists ~4,251 Black
  entries against a free Black population well over 20,000, so this is a map of
  listed householders, not of everyone.
- **Enslaved people cannot be mapped this way at all.** They appear in the
  census under an owner's name with no address, so they can only ever be a
  ward-level layer, never points.

## Layout

```
scripts/parse_directory.py   directory OCR -> people records
scripts/extract_anchors.py   street directory -> house-number anchor table
scripts/geocode_1860.py      anchors + geometry -> located residents
scripts/prep_map_data.py     -> compact payload for the web map
scripts/build_artifact.py    -> docs/index.html
docs/FINDINGS.md             data feasibility, what exists and what does not
docs/PLAN.md                 geocoding method and census linkage
SOLUTIONS.md                 bugs found and fixed, with root causes
```

Run scripts with the project venv, not the system python:

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/geocode_1860.py
```

## Sources

- *Wood's Baltimore City Directory for 1860*, *Matchett's Baltimore Director*
  (1842), and *The Baltimore Directory for 1822*, scanned by the Internet
  Archive.
- Historical Urban Ecological (HUE) Data, Center for Population Economics,
  ICPSR study 35617 — street centrelines and ward boundaries. Incorporates
  U.S. Census Bureau TIGER/Line data, acknowledged as the source per its terms
  of use.
- 1860 census aggregates from IPUMS USA complete count.

Parsing, geocoding and cartography by Louis Hyman, Johns Hopkins University.
