#!/usr/bin/env python3
"""Inline the map payload into the exhibit-preview page.

The published page must be self-contained (no external fetches are permitted),
so the geometry is injected into a <script type="application/json"> block
rather than loaded at runtime.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "web" / "template.html"
PAYLOAD = ROOT / "data" / "work" / "map_payload.json"
OUT = ROOT / "web" / "black_baltimore_1860.html"

tpl = TPL.read_text(encoding="utf8")
if "__PAYLOAD__" not in tpl:
    raise SystemExit("template has no __PAYLOAD__ placeholder")

# The payload sits inside a script element, so it must not contain a literal
# "</script>"; JSON escaping of "/" keeps any such run from closing the tag.
payload = PAYLOAD.read_text(encoding="utf8").replace("</", "<\\/")

OUT.parent.mkdir(parents=True, exist_ok=True)
body = tpl.replace("__PAYLOAD__", payload)

# Artifact build: a fragment, because the publisher supplies the document
# skeleton itself and rejects a second <html>/<head>/<body>.
OUT.write_text(body, encoding="utf8")
print(f"wrote {OUT} ({OUT.stat().st_size/1_000_000:.2f} MB)")

# GitHub Pages build: the same body inside a complete standalone document.
PAGE = ROOT / "docs" / "index.html"
DESC = ("A working geocode of the 2,868 Black Baltimoreans listed in the "
        "separate 'Colored Persons' section of Wood's 1860 city directory.")
doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{DESC}">
<meta property="og:title" content="Black Baltimore, 1860">
<meta property="og:description" content="{DESC}">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'><text y='14' font-size='14'>&#x1F5FA;</text></svg>">
{body}
</head>
</html>"""
# the template opens with <title> and <style>, which belong in <head>; the
# markup that follows is body content, so close head before it.
doc = doc.replace("<div class=\"wrap\">", "</head>\n<body>\n<div class=\"wrap\">", 1)
doc = doc.replace("</head>\n</html>", "</body>\n</html>")
PAGE.parent.mkdir(parents=True, exist_ok=True)
PAGE.write_text(doc, encoding="utf8")
print(f"wrote {PAGE} ({PAGE.stat().st_size/1_000_000:.2f} MB)")
