"""Build data/ciqual.json from the ANSES-CIQUAL XML tables.

CIQUAL is the French food composition table published by ANSES
(https://ciqual.anses.fr), under the Etalab Open Licence 2.0.

Usage:
    python tools/build_ciqual.py [path/to/XML_2020_07_07.zip]

Without an argument the 2020 zip is downloaded from ciqual.anses.fr.
The output keeps only the nutrients the app shows, per 100 g, so the file
stays small enough to ship with the app and search offline.
"""
import io
import json
import sys
import urllib.request
import re
import zipfile
from pathlib import Path

ZIP_URL = "https://ciqual.anses.fr/cms/sites/default/files/inline-files/XML_2020_07_07.zip"
OUT = Path(__file__).resolve().parent.parent / "data" / "ciqual.json"

# CIQUAL constituent code -> app nutrient key (same keys as the rest of the app)
CONSTITUENTS = {
    "328": "kcal",       # Énergie, Règlement UE 1169/2011 (kcal/100 g)
    "25000": "protein",  # Protéines, N x facteur de Jones
    "40000": "fat",
    "31000": "carbs",
    "34100": "fiber",
    "32000": "sugar",
    "40302": "satfat",
    "10110": "sodium",   # mg
    "75100": "chol",     # mg
    "10200": "calcium",  # mg
    "10260": "iron",     # mg
    "10190": "potassium",  # mg
    "333": "kcal_jones",  # older energy method, used when the EU value is missing
    "60000": "alcohol",
}
HELPERS = {"kcal_jones", "alcohol"}
FIELDS = [k for k in dict.fromkeys(CONSTITUENTS.values()) if k not in HELPERS]


def parse_value(raw):
    """CIQUAL values use decimal commas, '-' for missing, 'traces' and '< x' for tiny amounts."""
    s = (raw or "").strip().replace(",", ".")
    if s in ("", "-"):
        return None
    if s == "traces":
        return 0.0
    if s.startswith("<"):
        return round(float(s[1:].strip()) / 2, 4)  # below the detection limit: use half the limit
    return float(s)


def records(z, prefix, tag):
    """Yield each <tag> record as a dict of field -> text.

    The ANSES files are not well-formed XML (names such as "(<1% alc.)" contain
    raw '<' and '&'), so fields are read with a tolerant pattern, not an XML parser.
    """
    name = next(n for n in z.namelist() if n.startswith(prefix))
    doc = z.read(name).decode("cp1252")
    field = re.compile(r"<(\w+)>(.*?)</(\w+)>", re.S)
    for block in re.findall(rf"<{tag}>(.*?)</{tag}>", doc, re.S):
        yield {k: v.strip() for k, v, end in field.findall(block) if k == end}


def main():
    if len(sys.argv) > 1:
        data = Path(sys.argv[1]).read_bytes()
    else:
        print("Downloading", ZIP_URL)
        data = urllib.request.urlopen(ZIP_URL, timeout=60).read()
    z = zipfile.ZipFile(io.BytesIO(data))

    groups = {}
    for g in records(z, "alim_grp_", "ALIM_GRP"):
        groups[g["alim_ssgrp_code"]] = [g["alim_ssgrp_nom_fr"], g["alim_ssgrp_nom_eng"]]

    foods = {}
    for a in records(z, "alim_2", "ALIM"):
        foods[a["alim_code"]] = {"fr": a["alim_nom_fr"], "en": a["alim_nom_eng"],
                                 "grp": a["alim_ssgrp_code"], "n": {}}

    for c in records(z, "compo_", "COMPO"):
        key = CONSTITUENTS.get(c.get("const_code"))
        food = foods.get(c.get("alim_code"))
        if key and food is not None:
            food["n"][key] = parse_value(c.get("teneur"))

    rows = []
    for code, f in sorted(foods.items(), key=lambda kv: kv[1]["fr"].lower()):
        n = f["n"]
        estimated = 0
        if n.get("kcal") is None:
            n["kcal"] = n.get("kcal_jones")
        if n.get("kcal") is None and None not in (n.get("protein"), n.get("fat"), n.get("carbs")):
            # EU 1169/2011 energy factors: 4 kcal/g protein & carbs, 9 fat, 2 fibre, 7 alcohol
            n["kcal"] = round(4 * n["protein"] + 4 * n["carbs"] + 9 * n["fat"]
                              + 2 * (n.get("fiber") or 0) + 7 * (n.get("alcohol") or 0), 1)
            estimated = 1
        if n.get("kcal") is None:
            continue
        rows.append([int(code), f["fr"], f["en"], f["grp"], estimated] + [n.get(k) for k in FIELDS])

    OUT.parent.mkdir(exist_ok=True)
    payload = {
        "source": "ANSES-CIQUAL 2020, Etalab Open Licence 2.0 — https://ciqual.anses.fr",
        "columns": ["code", "name_fr", "name_en", "group", "kcal_estimated"] + FIELDS,
        "groups": groups,
        "foods": rows,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(rows)} foods to {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
