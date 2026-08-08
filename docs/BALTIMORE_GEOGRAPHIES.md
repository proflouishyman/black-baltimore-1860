# Baltimore historical geographies: what exists and what is worth acquiring

Survey compiled 2026-08-08. Every URL below was fetched during the survey unless
the entry says otherwise. Where something is login-gated, paywalled or could not
be verified, the entry says so in those words rather than implying availability.

The project currently places every resident against one base layer, the HUE
street centreline file (ICPSR 35617), a circa-1930 digitisation. It is seventy
years later than the earliest year we map and it is known to be wrong near the
Jones Falls. The question this survey set out to answer is whether somebody has
already done work we are about to redo.

**They have.** Two independent bodies of georeferenced Baltimore work already
exist, both free, both public, and neither was in the project's inventory.

---

## Ranked recommendation: the five things worth acquiring next

### 1. The Map Warper control-point network for the 1836 Fielding Lucas plan

**151 ground control points, median residual 18.8 m, 108 of 151 under 25 m,
spanning 7.4 km east-west by 5.2 km north-south.** Downloaded already to
`data/raw/gis/mapwarper/mapwarper_109684_1836_lucas_gcps.json`.

This is the single most valuable find in the survey. The project's own 1851
georeference rests on 12 control points with a 56 m RMSE, concentrated along
Baltimore Street, and `docs/GEOREFERENCE.md` correctly identifies that
concentration as its main weakness. Somebody has already built a control network
an order of magnitude denser on an in-period Baltimore city plan, and 98 of those
151 points fall in the longitude band that covers the Jones Falls corridor, which
is exactly where our displacement is worst.

**What it concretely fixes:** it gives an independent, dense, in-period reference
against which to test the c.1930 HUE alignment street by street, and a second
georeferenced base map fifteen years earlier than 1851, close to the 1819-1842
directories where a 1930 street file is least defensible.

**Caveat, stated plainly:** these are one uploader's points, not a scholarly
product. The residuals are Map Warper's own, computed against its own fit, not
independently validated. Points should be spot-checked before being trusted, and
the 262 m maximum residual shows at least one bad point is in there.

### 2. The Johns Hopkins georeferenced tile services

A Johns Hopkins ArcGIS Online account (`jgillis2_GISandData`, Jim Gillispie,
Sheridan Libraries) publishes **publicly accessible, georeferenced XYZ tile
layers** of Baltimore for 1784, 1833, 1836, 1851, 1852, 1869, 1876, 1914, 1928
and 1937. Verified by fetching real 256x256 tiles anonymously, no login. All are
EPSG:3857 with the standard Google tiling scheme, so they drop straight into
Leaflet or MapLibre as `.../MapServer/tile/{z}/{y}/{x}`.

The 1851 layer's licence field records why it exists: *"Map was georeferenced for
Prof. Lawrence Jackson's 'Mapping Frederick Douglass's Escape: An Historic
Maryland Odyssey' course (AS.060.630). Spring semester 2017."* A Johns Hopkins
Black-Baltimore mapping project already georeferenced the same 1851 Sidney and
Neff sheet this project georeferenced from scratch.

**What it concretely fixes:** an immediate visual base layer for the exhibit at
five in-period dates, with no georeferencing labour at all, plus a second opinion
on the 1851 fit. A single spot check placed the JHU 1851 layer within roughly
35 m of the HUE-derived Charles and Baltimore intersection, against the project's
own 53 m residual at the same point. One point is not an accuracy assessment. A
proper comparison against the project's twelve control points is the obvious next
step and is cheap to run.

### 3. NOAA T-sheet T00217, "Resurvey of Baltimore City," 1849

A US Coast Survey trigonometric survey at 1:10,000, from inside the study period,
showing the city grid and the Jones Falls before straightening and culverting.
14835 x 9031 px, US federal public domain, already downloaded to
`data/raw/gis/noaa_charts/`.

Coast Survey work is geodetically in a different class from commercial city
plans. Sidney and Neff drew a handsome map. Bache's surveyors ran triangulation.
If any single sheet can adjudicate where the Jones Falls actually ran in the
1840s, this is it.

NOAA serves it as a flat JPEG only. It is **not** georeferenced by NOAA. However
Map Warper has a warped "U.S. Coast Survey Map of Baltimore Harbour and City"
(map 91461, GCPs downloaded), so a starting control set exists.

### 4. The 1890 Sanborn atlas of Baltimore, Library of Congress

258 sheets across three volumes, free, public domain, full-resolution JPEG2000
plus IIIF per sheet. Item IDs `sanborn03573_001` through `_003`.

Sanborn sheets show individual building footprints, construction materials, lot
lines, alley names and street numbers at roughly 1:600. Nothing the project holds
is remotely this detailed. It is 22 years past the 1868 cutoff, which is a real
limitation, but for the alleys where our residents actually lived, and where
modern street data has nothing at all, it is the best surviving evidence of what
was physically there.

**One caveat that must be checked before relying on the numbers.** The 1887 Polk
directory map in this repository carries the printed instruction "SEE R.L. POLK &
CO'S STREET DIRECTORY FOR LOCATION OF WHARVES, CHANGES IN NUMBERS." Baltimore
appears to have renumbered houses in the later 1880s. If so, Sanborn 1890 street
numbers will not correspond to pre-1870 directory numbers, and the sheets are
useful for geometry and alley names but not as a direct number key. This has not
been verified and should be, against a directory of each date, before any
number-matching is attempted.

### 5. The missing HUE Baltimore water-infrastructure layer

ICPSR 35617 DS1 is documented as "Baltimore GIS: Wards, Streets, Sanitation," and
the study abstract notes that for Baltimore specifically only water infrastructure
was digitised. This repository holds `HUE_Baltimore_Wards` and
`HUE_Baltimore_Streets` and nothing else, so the sanitation component of a
dataset we already have licensed appears never to have been extracted.

Water mains follow streets. A 19th-century in-street water main layer from the
same source, on the same geometry, is a free consistency check on the street file
we are already using, and it costs one login and one re-download.

---

## What is already georeferenced for Baltimore

This was the primary question. The answer has three parts.

### Map Warper (mapwarper.net): yes, substantially

38 warped maps at Baltimore city scale were confirmed by title search across the
public API. The in-period ones, with control-point counts and Map Warper's own
residuals, are below. All GCP files listed have been downloaded to
`data/raw/gis/mapwarper/`.

| ID | Map | GCPs | Median resid. | Max resid. | Source image |
|---|---|---:|---:|---:|---|
| 55464 | Baltimore 1792, Folie | 5 | 0.7 m | 1.8 m | 3000x2714 |
| 36610 | Warner & Hanna 1801 | 4 | 16.3 m | 21.5 m | 12206x8413 |
| 36809 | Warner & Hanna 1801, colour | 5 | 5.2 m | 7.5 m | 8319x5735 |
| **109684** | **Fielding Lucas 1836** | **151** | **18.8 m** | **262.5 m** | 6584x4908 |
| 31201 | Map of Baltimore 1838 | 6 | 12.1 m | 25.8 m | 1600x1280 |
| 31175 | Baltimore 1845-1855 | 3 | 0.0 m | 0.0 m | 1354x1083 |
| 35860 | Baltimore, Williams, 1848 | 5 | 29.2 m | 106.8 m | 4288x2848 |
| 37609 | Baltimore 1851 | 5 | 27.3 m | 98.7 m | 4500x3650 |
| 91461 | US Coast Survey, Baltimore Harbour & City | 4 | 71.2 m | 109.7 m | 15392x8904 |
| 16095 | Map of the City and Suburbs of Baltimore | 4 | 19.4 m | 20.7 m | 7462x5428 |
| 34005 | Baltimore, Maryland, 1873 | 15 | 9.0 m | 38.8 m | 1730x1549 |
| 58710 | Baltimore 1876 Papenfuse Atlas | 3 | 0.0 m | 0.0 m | 1500x997 |
| 36406 | 1876 Baltimore Atlas, Harbor to Saratoga | 14 | 8.7 m | 78.5 m | 1500x978 |
| 29712 | Bromley 1896, Plate 12 section | 9 | 194.3 m | 625.1 m | 10110x13524 |
| 28259 | 1914 Atlas, Sheet 1S-1W | 7 | 20.2 m | 31.4 m | 27429x21012 |

Read the residuals with care. A three-point fit is exactly determined, so its
"0.0 m" residual means nothing at all. The 1896 Bromley plate at 194 m median is
simply a bad georeference and should not be used. The 1836 Lucas entry is the
only one with a control network dense enough to be worth adopting wholesale.

- **URL, verified 2026-08-08:** <https://mapwarper.net/>
- **API used:** `https://mapwarper.net/api/v1/maps?query=<term>&field=title`, and
  `https://mapwarper.net/api/v1/maps/<id>/gcps` for control points. Both return
  JSON without a login.
- **Access:** browsing and the JSON API are free. The site is behind an hCaptcha
  human check for plain HTTP clients, so requests must come from a real browser
  session. The GeoTIFF export (`/maps/<id>/export.tif`) and the CSV GCP export
  return an HTML page rather than a file without a signed-in session. A free
  account removes that. The JSON GCP API does not need one.
- **Licence:** varies by uploader and is not stated per map. Map Warper is a
  volunteer service. Treat control points as data to verify and cite, not as a
  licensed product.
- **Format:** XYZ tiles, WMS, GeoTIFF export (login), GCPs as JSON or CSV.

### Johns Hopkins ArcGIS Online: yes, as finished tile layers

Account `jgillis2_GISandData` (Jim Gillispie, JHU Sheridan Libraries), 158 public
items. All services below returned HTTP 200 for item metadata and, where noted,
for real tile requests, anonymously on 2026-08-08.

| Map | Service URL (append `/tile/{z}/{y}/{x}`) | Max zoom | Tiles verified |
|---|---|---:|---|
| Griffith 1784 | `https://tiles.arcgis.com/tiles/0MSEUqKaxRlEPj5g/arcgis/rest/services/Griffith_1784_rectified_jpg/MapServer` | 23 | metadata only |
| Baltimore 1833 directory map | `.../services/Baltimore_1833_Map/MapServer` | 19 | yes |
| Fielding Lucas 1836 | `.../services/Lucas_Balt_1836_clip_rectified_tif/MapServer` | 23 | yes |
| Sidney & Neff 1851 | `.../services/Baltimore_1851/MapServer` | 19 | yes |
| Poppleton 1852, JHMI area | `.../services/Poppleton_JHMI_rectified_jpg/MapServer` | 23 | metadata only |
| Sachse 1869, City Hall area | `.../services/Sacshe_City_Hall_Area/MapServer` | 19 | yes |
| Sachse 1869, Philpot St | `.../services/Sachse_Fells_Point_THREE_WTL1/MapServer` | - | metadata only |
| Sachse 1869, Upper Fells Point | `.../services/Fells_Point_Upper_Area_WTL1/MapServer` | - | metadata only |
| Sachse 1869, Douglas Fells Point | `.../services/Sachse_Douglas_Fells_Point_rectified_jpg/MapServer` | - | metadata only |
| Hopkins 1876 City Atlas | `.../services/Baltimore_1876_Atlas_GeoRefed/MapServer` | 19 | 404 at test tile |
| 1914 Atlas, Fulton Av to Jones Falls | `.../services/Sheets15_16_Final_rectified_jpg/MapServer` | - | metadata only |
| 1914 Atlas, Inner Harbor W to Patterson Pk | `.../services/Sheet_23___24_Final_rectified_jpg/MapServer` | - | metadata only |
| Baltimore 1928 | `.../services/Balt1928/MapServer` | 23 | yes |
| Residential Security (HOLC) 1937 | `.../services/ResidSecurity/MapServer` | 19 | metadata only |

Item pages are at `https://www.arcgis.com/home/item.html?id=<item id>`, and the
item IDs are recorded in the notes at the end of this file.

- **Access:** all items report `access: public`. Tiles were fetched with no
  credentials.
- **Licence:** mostly blank. Two items carry restrictive-sounding notes. The 1876
  City Atlas says "Available for use by all Johns Hopkins students, faculty and
  staff," as does the 1937 Residential Security map. The project lead is JHU
  faculty, so use is covered, but these should not be redistributed as if they
  were open data, and the 1876 atlas layer in particular should not be baked into
  a public exhibit without asking Sheridan Libraries first.
- **Provenance worth quoting:** the 1836 Lucas item states it "was georeferenced
  from a printed copy held by the Johns Hopkins, Sheridan Libraries," and that
  "the hand coloring and numbers designate administrative wards." The 1833 item
  says "Full map is available in JScholarship."
- **Related JHU work:** the same account holds a "Billie Holiday Residences"
  feature service and web maps, that is, a residence-level Black Baltimore
  mapping exercise on the same base layers. Worth looking at for method.

### Allmaps and the IIIF Georeference Annotation ecosystem: no

This is a clean negative and it is worth recording so nobody re-checks it.

Querying the Allmaps API at five separate points across downtown Baltimore
returned **96 georeferenced maps whose footprints cover Baltimore, and not one of
them is a city-scale map.** The smallest footprint in the entire set is
341,000 km², a regional map. Every Baltimore hit is a map of North America, the
United States, the mid-Atlantic or the world that happens to include the city.

- **URL, verified 2026-08-08:** `https://api.allmaps.org/maps?intersects=-76.615,39.290&limit=200`
- **Access:** free, no login, no rate limiting encountered.
- **Implication:** there is an opportunity here. Allmaps consumes IIIF, the
  Library of Congress and David Rumsey both serve Baltimore sheets over IIIF, and
  publishing this project's georeferences back as IIIF Georeference Annotations
  would make it the first city-scale Baltimore georeference in that ecosystem.

### NYPL Map Warper: dead

`https://maps.nypl.org/warper/` now 301-redirects to an Archive-It capture from
May 2021 (`https://wayback.archive-it.org/13216/20210520171637/...`). The New
York Public Library has retired its Map Warper instance. Do not plan around it.

### David Rumsey Georeferencer: exists, could not be verified

`https://davidrumsey.georeferencer.com/` redirects to
`https://davidrumsey.oldmapsonline.org/`, which returned HTTP 403 behind a
Cloudflare interstitial to both plain HTTP clients and a headless browser on
2026-08-08. `https://www.oldmapsonline.org/api/v1/search` likewise returned 403.
Rumsey's georeferenced holdings for Baltimore are therefore **not confirmed**.
They should be checked by hand in an ordinary browser. Given that none of
Rumsey's Baltimore city sheets appear in Allmaps, it is likely that any Rumsey
georeferences live only inside their own viewer.

---

## Scanned maps: what exists that the project does not already hold

### Library of Congress, Geography and Map Division

The LOC JSON API (`https://www.loc.gov/maps/?q=baltimore&dates=1780/1900&fo=json`)
was queried directly and returns 220 results, of which the Baltimore city plans
are a short list. Most of them are already in `data/raw/maps/`. These are the
ones that are not, all free and public domain, all with full-resolution JPEG2000
at `https://tile.loc.gov/storage-services/service/gmd/...`:

| Date | Map | LOC item | Notes |
|---|---|---|---|
| 1792 | Plan of the town of Baltimore and it's environs | <https://www.loc.gov/item/2002624037/> | Predates the project window, useful for the earliest street fabric |
| 1851 | A map of the medical topography of Baltimore | <https://www.loc.gov/item/2020587062/> | Small sheet, but a thematic map contemporaneous with our best plan |
| 1880 | Map of Baltimore, with new precincts, J.W. Woods | <https://www.loc.gov/item/2020587068/> | **Downloaded.** Same publisher as the 1860 and 1868 directories the project transcribes. Wards 1-20 in red, precincts, a full street index with map-grid references, a wharf index and a market index |
| 1887 | Map of Baltimore, published with R.L. Polk & Co's Baltimore City directory | <https://www.loc.gov/item/2020587112/> | **Downloaded.** 1,000 feet to the inch, roughly 1:12,000. Wards in Roman numerals, precincts and police precincts numbered, block-level detail across the whole city, 8775x6830 px |
| 1891 | Lloyd's Baltimore elevated building map of the business district | <https://www.loc.gov/item/2011587226/> | Two large sheets, building-by-building |
| 1819 | Survey of the River Patapsco and part of Chesapeake Bay | <https://www.loc.gov/item/76697578/> | Four related items. Shoreline in the first year the project maps |

**Rights:** LOC states the Geography and Map Division's digitised collections are
free to use with no known restrictions.

**Downloaded to `data/raw/gis/loc_maps/`:** the 1880 precinct map and the 1887
Polk directory map. Both are the directory-publisher's own maps, which makes them
the closest cartographic relatives of the sources the project transcribes.

The 1880 sheet is worth a second look for its street index alone. It lists every
street with a map-grid reference, which is a ready-made gazetteer of street names
in use in 1880 with an approximate location for each.

### Library of Congress, Sanborn Fire Insurance Maps

Free, public domain, no login. Collection at
<https://www.loc.gov/collections/sanborn-maps/>.

| Edition | Items | Sheets |
|---|---|---:|
| 1890 | `sanborn03573_001` / `_002` / `_003` | 258 |
| 1901-1902 | `sanborn03573_004` through `_007` | 490 |

Later Baltimore City editions run 1914 through 1953 as `sanborn03573_008`
through `_055`. Separate items exist for Baltimore County towns, earliest Towson
1885. Beware of Baltimore, Ohio and Baltimore, Michigan sheets sharing the search
term.

**Per-sheet formats:** full-resolution JP2 (8-14 MB), master TIFF (130-150 MB, do
not bulk fetch), IIIF JPEG derivatives at fractional scale, and a full IIIF
`info.json`. Example verified at HTTP 200:
`https://tile.loc.gov/storage-services/service/gmd/gmd384m/g3844m/g3844bm/g3844bm_g03573189001/03573_01_1890-0000L.jp2`

**Bulk recipe:** `GET https://www.loc.gov/item/<ID>/?fo=json`, iterate
`resources[0].files`, take the `image/jp2` entry per sheet. The loc.gov item HTML
endpoint sits behind a bot challenge for plain clients, but the `tile.loc.gov`
asset URLs it returns download fine with curl. Full recipe and verification log
in `data/raw/gis/sanborn/manifest.json`. One sample sheet is downloaded.

**Assessment:** the highest-detail source available for Baltimore alleys, but
1890 and after. Use it for alley geometry and alley names, not for house numbers,
until the renumbering question above is settled.

### Property atlases: Hopkins and Bromley

Two independent free sources, verified 2026-08-08.

**Johns Hopkins JScholarship**, collection "Maryland State, County and Baltimore
City Atlases." No login, but Cloudflare blocks plain clients, so downloads need a
real browser session. Full item list and download recipe in
`data/raw/gis/atlases/manifest.json`.

| Atlas | Date | Files | Item |
|---|---|---:|---|
| Hopkins, City Atlas of Baltimore | 1876-1877 | 167 | <https://jscholarship.library.jhu.edu/items/aac86a81-aa13-49db-8816-4daa2fc311ee> |
| Bromley, Atlas of the City of Baltimore | 1885-1887 | 106 (JP2) | <https://jscholarship.library.jhu.edu/items/42fa0470-960f-41f8-a291-76dd7cea4630> |
| Bromley, Atlas of the City of Baltimore | 1896 | **0** | Catalogue record only, **no digitised images at JHU** |
| Bromley, Atlas of the City of Baltimore | 1906 | 73 | <https://jscholarship.library.jhu.edu/items/fcecb9cb-1782-46f6-a01c-9d0a0a118f33> |
| Baltimore City Topographical Survey | 1897 | 76 | <https://jscholarship.library.jhu.edu/items/3d6d9905-dcde-4435-9fc5-11fbc52245a4> |
| Hopkins, Atlas of Baltimore County | 1877 | 94 | <https://jscholarship.library.jhu.edu/items/e254045e-b45d-410a-887e-1bceb449dd6e> |

**Maryland State Archives**, the Papenfuse `bc_ba_atlases_1876_1915` PDF series.
Plain curl works, no login, no browser needed:
`https://mdhistory.msa.maryland.gov/msaref07/bc_ba_atlases_1876_1915/pdf/bc_ba_atlases_1876_1915-NNNN.pdf`
Pages 0001 to at least 0800 confirmed to exist. This is the only confirmed source
of page images for the **1896 Bromley** edition. No finding aid or table of
contents was located, so page-to-plate mapping is not indexed. Two sample pages
downloaded.

The 1897 Baltimore City Topographical Survey deserves a note of its own. It is a
municipal topographic survey from 1893-1896 field work, not a property atlas, so
it carries contours rather than building footprints. For a city where the Jones
Falls valley is the whole problem, a contemporaneous municipal topographic survey
is a better witness to the terrain than any commercial plan.

### David Rumsey Map Collection

The Luna search API works without a login
(`https://www.davidrumsey.com/luna/servlet/as/search?q=baltimore&os=<n>&fullData=true`)
and IIIF is served per item
(`https://www.davidrumsey.com/luna/servlet/iiif/<id>/info.json`, verified).

93 Baltimore-titled items were enumerated. Twenty are city plans at 1:15,000 to
1:26,000 dated 1838 to 1877. The standout for this project's period is
**1852, "Baltimore.", 1:15,000, List No. 4742.000, item `RUMSEY~8~1~2830~220063`,
8875 x 6800 px** (detail page verified HTTP 200 at
<https://www.davidrumsey.com/luna/servlet/detail/RUMSEY~8~1~2830~220063>).
At 1:15,000 that is the largest-scale separate city plan found anywhere in the
survey for the 1850s.

Other in-period Rumsey items, all verified present in the search index: 1838
(1:24,000), 1841 (1:25,000), 1855, 1856, 1857 (all about 1:23,500), 1860 "Plan Of
Baltimore" (1:22,600), 1865 and 1866 (several, 1:20,000 to 1:24,000).

**Access:** free to view and to fetch over IIIF. Whether any of these are
georeferenced in Rumsey's own Georeferencer could not be verified, see above.

### Digital Maryland and Enoch Pratt Free Library

Enumerated through the CONTENTdm API
(`https://collections.digitalmaryland.org/digital/bl/dmwebservices/index.php?q=dmGetCollectionList/json`),
195 collections. Relevant ones are `mdmc` (Sachse's 1869 bird's eye view, Enoch
Pratt) and `mcmc` ("Mapping Maryland's Counties," 24 state-level sheets
1650-1862, too coarse for street work). **No additional large-scale Baltimore
atlas or ward-level collection was found here beyond what the project holds.**
Items are served as CONTENTdm compound objects or JP2, scanned images only.

---

## Water, shoreline and the Jones Falls

### NOAA Historical Map and Chart Collection

<https://historicalcharts.noaa.gov> (verified 2026-08-08). Licence quoted from
the site's own about page: "The images are free to download, and may be used for
commercial or educational purposes." US federal, no login.

A search for "Baltimore" returns 187 results. The period-relevant sheets:

| ID | Date | Sheet | Status |
|---|---|---|---|
| `T00217-00-1849` | 1849 | Resurvey of Baltimore City, 1:10,000, J.B. Gluick under A.D. Bache | **Downloaded**, 14835x9031 px, 32 MB |
| `T00217Bis-00-1849` | 1849 | Second sheet of the resurvey | Confirmed present |
| `T00216-00-1845` | 1845 | Baltimore Harbor and City | Confirmed present |
| `T00936-00-1864` | 1864 | Vicinity of Baltimore, N.W. side | **Downloaded**, 16056x9540 px, 25 MB |
| `T03026` / `T03027-00-1865` | 1865 | Approaches to Baltimore, Western and Eastern sheets | Confirmed present |
| `BaltimoreChart-00-1812` | 1812 | Baltimore Harbor, War of 1812 | Confirmed present |
| `384-11-1880` | 1880 | Patapsco River and Baltimore Harbor | Confirmed present |
| `857-00-1887` / `-1901` | 1887, 1901 | Baltimore Harbor Sheet No. 1 | Confirmed present |

**Download recipe:**
`curl "https://historicalcharts.noaa.gov/includes/downloadsingle.php?filename=<ID>&fileExt=.jpg" -o <ID>.jpg`

**Format caveat, tested directly:** requesting `fileExt=.tif` or `.zip` returns
`Content-Length: 0`. Only flat JPEG scans are actually served. **These are not
georeferenced by NOAA.**

### Textual and engineering sources on the Jones Falls

All on Internet Archive, public domain, verified fetchable:

- **Report of the Sewerage Commission of the City of Baltimore, 1897**,
  <https://archive.org/details/reportofsewerage00balt>. Contains fold-out maps
  (sewerage districts, intercepting sewers, main outfall) and text naming dozens
  of drains discharging into the Jones Falls at named cross streets. The best
  systematic ground truth on the Falls' pre-culvert alignment through downtown.
- **Second Report of the Sewerage Commission, 1899** (`secondreportsew00commgoog`)
  and **Annual Report 1912** (`annualreportofse1912balt`), same access pattern.
- **Wilbur A. Street, "The History and Development of Jones' Falls in
  Baltimore," 1926**,
  <https://archive.org/details/TheHistoryAndDevelopmentOfJonesFallsInBaltimoreWilburA.Street>.
  Gives an explicit textual description of the original course: rising north-west
  of the city, entering at North Avenue and Oak Street, south-east to West
  Hoffman Street, south and slightly west to West Biddle Street, then south to
  Hillen Street and into the Basin at the City Dock. The paper's accompanying
  blueprint was **not** digitised, per the item's own note.
- **Report of the Advisory Board Relative to Bulkhead and Pierhead Lines,
  Baltimore Harbor, 1878**, <https://archive.org/details/reportofadvisory1878hump>.
  Text confirms an accompanying five-sheet map fixing the legal harbour edge.

### Historical shoreline GIS: exists, but not for our period

Maryland iMAP "Shoreline Changes" is a real DSAS-format product built from
T-sheets, at
`https://mdgeodata.md.gov/imap/rest/services/Hydrology/MD_ShorelineChanges/MapServer`
(REST queried directly, working). Querying it against a Baltimore Harbor bounding
box returns only 1930, 1970, 1990, 2000 and 2010 vintages. The "Legacy Historical
Shorelines" layer returns **zero features** intersecting Baltimore Harbor. The
programme excludes the already-bulkheaded harbour. The catalogue's static
shapefile download link currently returns HTTP 400. **Not useful for 1819-1868.**

**No 19th-century vector hydrography for Baltimore was found. Not confirmed to
exist.** The honest answer is that the shoreline has to be traced off the 1845
and 1849 Coast Survey sheets by hand.

---

## Institutional GIS: Maryland and Baltimore

### Baltimore City, Street Centerline Native

`https://egis.baltimorecity.gov/egis/rest/services/Address_Points/Street_Centerline_Native/FeatureServer/0`

48,521 segments, of which **150 are named alley segments** (`featype='ALY'`), with
address ranges (`fraddl`, `toaddl`, `fraddr`, `toaddr`) and block numbers. Free,
no login, exportable as GeoJSON. **Downloaded** to
`data/raw/gis/open_baltimore/baltimore_street_centerline_native.geojson` (26 MB,
gitignored).

This is the direct modern comparison layer for the c.1930 HUE file. Differencing
the two shows which alley names and alignments survived and which did not, which
is the cheapest available diagnostic on where HUE can and cannot be trusted. Note
that 150 surviving named alleys is a small fraction of what the 1819-1868
directories name, which is precisely why HUE was chosen in the first place.

### Maryland iMAP, Inventory of Historic Properties

`https://mdgeodata.md.gov/imap/rest/services/Historic/MD_InventoryHistoricProperties/FeatureServer/0`

5,255 Baltimore City features, with `MIHPNO`, `FULLADDR` and `PDFLINK` to the MHT
survey form. Free, no login. Downloaded (gitignored, and the project already
holds `data/raw/mihp_baltimore.geojson`). Useful for spot-checking whether a
directory address still has a period building on the parcel. It will not fix
street geometry.

### Other confirmed but secondary

| Source | URL | Verdict |
|---|---|---|
| Baltimore CHAP historic districts | `https://services1.arcgis.com/43Lm3JYE3nM91DAF/arcgis/rest/services/CHAP/FeatureServer/0` | 38 polygons, free. Downloaded. Modern designations, contextual only |
| Baltimore Wards 1930 with census race data | `https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/BaltimoreWards1930/FeatureServer/0` | 28 wards, free. Downloaded. Out of period but a useful late bookend |
| MD National Register of Historic Places | `https://mdgeodata.md.gov/imap/rest/services/Historic/MD_NationalRegisterHistoricPlaces/FeatureServer/0` | Free, sparser than MIHP, no county field |
| Baltimore parcels | `https://egis.baltimorecity.gov/egis/rest/services/Parcel_Information/Parcel/FeatureServer/0` | 223,652 parcels, free. Too large to carry. Page with `resultOffset` |
| Baltimore modern ward-precincts | `https://services1.arcgis.com/UWYHeuuJISiGmgXx/arcgis/rest/services/Ward_Precinct_2022_final/FeatureServer` | 2022 voting wards, modern only |

### Institutional sources that did not deliver

- **Baltimore City Archives**, BRG12 Map Collection 1730-1964, finding aid at
  <http://guide.msa.maryland.gov/pages/series.aspx?id=BRG12> (verified reachable).
  Holds street opening and closing maps, the Jehu Bouldin atlases (roughly 80
  maps), the 1904 Burnt District map. **Finding aid only, not digitised.** Most
  items are on 35 mm microfilm requiring an in-person visit or a records request
  (msa.bca@maryland.gov). The Poppleton survey is **not** explicitly named in the
  finding aid and is **not confirmed** to be catalogued or digitised there.
- **Maryland State Archives Special Collections and the Huntingfield Map
  Collection**: the `/msa/speccol/` path returns HTTP 403 to both plain clients
  and a headless browser, which is a firewall rule rather than an outage since
  other MSA paths load. **Not confirmed.** Needs a manual browser visit.
- **MDLANDREC / plats.net**: <https://landrec.msa.maryland.gov> confirmed live,
  **login required**, content not accessible without an account.
- **JHU Sheridan Libraries GIS guide** (`guides.library.jhu.edu/gis`): generic
  ArcGIS software support, no Baltimore historical data guide. **Not a source.**
  The useful JHU material is the ArcGIS Online account described above.
- **BNIA**: enumerated all 16 datasets on
  <https://mapping-bniajfi.opendata.arcgis.com/>. Earliest boundary vintage is
  Community Statistical Area 2000. **No historical crosswalk exists.**
- **Baltimore Heritage**: its ArcGIS Online account holds 7 items, all modern.
  **No historical georeferenced layers.**
- **Historic Map Works**: not checked. A commercial vendor, historically low
  resolution behind ads. Deprioritised given verified free coverage elsewhere.

---

## National historical GIS: mostly a dead end for this project

Recording these so they are not re-searched.

- **NHGIS**: boundary files cover state, county, tract, block group, place, PUMA,
  congressional district and school district. **"Ward" does not appear anywhere
  in the GIS Files documentation.** Place polygons begin in 1990. Free account
  needed for extracts. **Positively ruled out** for 19th-century Baltimore wards.
  <https://www.nhgis.org/gis-files>
- **Urban Transition Historical GIS Project** (Logan, Brown), live at
  <https://s4.ad.brown.edu/Projects/UTP2/index.htm> (the `s4.brown.edu` form is
  dead). Baltimore is included, but **only for 1880**, twelve years past our
  cutoff, and its ward polygons are likely redundant with HUE's 1861-1882 and
  1883-1887 files. Download requires submitting an email and agreeing to
  conditions of use at <https://s4.ad.brown.edu/Projects/UTP/Default.aspx>.
  Citation required: Logan, Jindrich, Shin and Zhang 2011, *Historical Methods*
  44(1):49-60. The one thing it has that HUE does not is 1880 building-level
  geocoded occupants. **Low priority.**
- **Mapping Inequality**, University of Richmond. The advertised
  `fullDownload.geojson` link is dead. The working access path is
  `https://services.arcgis.com/ak2bo87wLfUpMrt1/arcgis/rest/services/MappingInequalityRedliningAreas_231211/FeatureServer/0/query?where=city='Baltimore' AND state='MD'&outFields=*&f=geojson&outSR=4326`.
  60 polygons downloaded to `data/raw/gis/mapping_inequality/`. Scans are public
  domain, the georectified spatial data is CC-BY-NC. **1937, seventy years off
  period.** Only value is as an epilogue layer.
- **ICPSR**: a search for Baltimore ward GIS boundaries returns exactly one
  curated result, HUE 35617, which the project already has. Nothing else.
- **Harvard Dataverse, Zenodo, Figshare, GitHub**: searched via each platform's
  API. Nothing on-topic. **Not confirmed** that any other published 19th-century
  Baltimore ward, precinct or street vector dataset exists.
- **Digital Scholarship Lab's other projects**: Renewing Inequality is 1950-1966
  and city-level. No antebellum Baltimore mapping exists in their catalogue.

---

## What is in `data/raw/gis/`

Bulk rasters and the two largest vector files are gitignored. Provenance for
everything is above, and the download recipes are in the per-directory
`manifest.json` files.

| Path | Carried in git | What |
|---|---|---|
| `mapwarper/*.json` | yes | 15 control-point sets for warped Baltimore maps, plus `gcp_index.json` |
| `sanborn/manifest.json` | yes | LOC Sanborn item IDs, URL patterns, bulk recipe |
| `atlases/manifest.json` | yes | JScholarship and MSA atlas items, download recipe |
| `mapping_inequality/baltimore_holc_1937.geojson` | yes | 60 HOLC polygons, CC-BY-NC |
| `open_baltimore/chap_historic_districts_landmarks.geojson` | yes | 38 CHAP districts |
| `open_baltimore/baltimore_wards_1930_census.geojson` | yes | 28 wards with 1930 race and population counts |
| `loc_maps/*.jp2` | no | 1880 precinct map, 1887 Polk directory map |
| `noaa_charts/*.jpg` | no | 1849 T00217 resurvey, 1864 T00936 |
| `sanborn/*.jp2`, `*.jpg` | no | One 1890 sample sheet |
| `atlases/*.pdf`, `*.jpg`, `*.png` | no | Hopkins 1876 and Bromley 1896 samples, Map Warper WMS sample |
| `open_baltimore/baltimore_street_centerline_native.geojson` | no | 48,521 modern segments including 150 named alleys |
| `maryland_imap/md_historic_inventory_baltimore_city.geojson` | no | 5,255 MIHP records, duplicates existing project data |
| `msa/`, `shoreline/` | n/a | Empty. Nothing at MSA proved both accessible and downloadable, and no 19th-century shoreline vector exists |

## ArcGIS Online item IDs for the JHU layers

`https://www.arcgis.com/home/item.html?id=<id>`

| Map | Item ID |
|---|---|
| Griffith 1784 | `3610eccc2c964efaa31145171e069dc7` |
| Baltimore 1833 | `a31175dbaa9942e09e8779a56bee94ee` |
| Lucas 1836 | `2afecf1556e74b43b651d8133a337378` |
| Sidney & Neff 1851 | `920fcb128e1948758b442497676d2a1f` |
| Poppleton 1852 JHMI | `00a60a3549c34b25970c46926efdd0b6` |
| Sachse 1869 City Hall | `2d3c361150904c598650e2dd7c3f9b7c` |
| Sachse 1869 Philpot St | `01c25d3134854a36af13d01ea0671613` |
| Sachse 1869 Upper Fells Point | `fe1084c6a4a14a93b43f690e84054bd0` |
| Sachse 1869 Douglas Fells Point | `b83282a0af924f32b6d2dbf31138d457` |
| Hopkins 1876 City Atlas | `c6e71bfa7cb84449938f09fc4e7cdb0b` |
| 1914 Atlas, Fulton to Jones Falls | `66ca5e3152964417aca227472e76154c` |
| 1914 Atlas, Harbor W to Patterson Pk | `6f072a4ae395406ba47886131e8cdfef` |
| Baltimore 1928 | `439c94944f0b452db688b8184f132dd2` |
| Residential Security 1937 | `880b0b3b30394024870fa66bec2a141b` |
| Baltimore Wards 1930 census | `23524eedb0c54976b7f67224c568de70` |

The Library of Congress also publishes Sanborn volume-extent polygons for
Baltimore as public feature services, one per edition, which give a spatial index
of which sheet covers which blocks. The 1890 edition is
`0c6cc5faed94447584a87e41c5ec51d2` at
`https://services5.arcgis.com/ohAFyIFvXFRGcC67/arcgis/rest/services/Balt_1890/FeatureServer`.
Editions for 1901-1902, 1914-1915, 1928-1936, 1950-1951 and 1952-1953 exist under
the `GMD_LOC` account.

---

## Method and honest limits

Searches were run against collection APIs directly rather than through a web
search engine, because the session's web search budget was exhausted early. That
turned out to be an advantage for verification, since every result quoted here
came from a live API response or a fetched page rather than a search snippet, but
it means discovery was bounded by which APIs were reachable. Three things were
blocked and are recorded as unverified rather than absent: the David Rumsey
Georeferencer, OldMapsOnline's search API, and the Maryland State Archives
Special Collections path. Map Warper's holdings were enumerated by title search
across nine terms plus a 400-item bbox sample, which is thorough but not
exhaustive.

Nothing in this document was inferred from a source that was not fetched.
