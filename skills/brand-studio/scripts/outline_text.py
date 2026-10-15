#!/usr/bin/env python3
"""Outline a wordmark: set text in a real font (kerning and ligatures applied) and write it as SVG paths.

Why: finished logos must not contain live <text> (it falls back to another font on other machines). Hand-drawn
letters misread; real glyph outlines plus one ownable detail drawn on top are far more reliable
(references/bi-logo.md, references/typography.md).

Fonts: pass --font-file, or --font "Family" to fetch the OFL/Apache family from Google Fonts (cached in
~/.cache/brand-studio/fonts). Only fonts whose licence allows outlining into a logo may be used: Google Fonts
OFL/Apache families are fine; Fontshare and commercial faces need their own licence (references/bi-type.md).

Output: <out>.svg  (viewBox tight around the ink, cap-top at y=0 when --units cap, baseline at y=100)
        <out>.meta.json  (baseline, cap height, x-height, per-glyph x positions, so a detail can be placed on a letter)

Usage:
  python3 scripts/outline_text.py --font "Fraunces" --weight 700 --text "Kiln" -o work/wordmark.svg
  python3 scripts/outline_text.py --font-file MyFont.ttf --text "HARBOR" --tracking 40 --color "#0F7C80" -o w.svg
Needs fonttools + uharfbuzz (installed on demand through uv).
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib  # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "brand-studio", "fonts")
UA_TTF = "curl/8.5.0"  # Google serves plain TTF files to non-browser agents


def fetch_google_font(family, weight=400, italic=False):
    os.makedirs(CACHE, exist_ok=True)
    key = re.sub(r"[^a-z0-9]+", "-", family.lower()) + f"-{weight}{'i' if italic else ''}.ttf"
    path = os.path.join(CACHE, key)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    axis = f"ital,wght@{1 if italic else 0},{weight}"
    url = "https://fonts.googleapis.com/css2?family=" + urllib.parse.quote(family) + ":" + axis
    req = urllib.request.Request(url, headers={"User-Agent": UA_TTF})
    css = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    m = re.search(r"url\((https://[^)]+\.ttf)\)", css)
    if not m:
        raise SystemExit(f"error: Google Fonts has no TTF for {family} {weight} (check the family name and weight)")
    data = urllib.request.urlopen(urllib.request.Request(m.group(1), headers={"User-Agent": UA_TTF}), timeout=60).read()
    with open(path, "wb") as fh:
        fh.write(data)
    return path


def outline(font_path, text, tracking=0, case="as-is", features=None, variations=None):
    import uharfbuzz as hb
    from fontTools.ttLib import TTFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.pens.boundsPen import BoundsPen

    if case == "upper":
        text = text.upper()
    elif case == "lower":
        text = text.lower()
    tt = TTFont(font_path)
    upm = tt["head"].unitsPerEm
    os2 = tt["OS/2"] if "OS/2" in tt else None
    cap = getattr(os2, "sCapHeight", 0) or int(upm * 0.7)
    xh = getattr(os2, "sxHeight", 0) or int(upm * 0.5)
    gs = tt.getGlyphSet(location=variations) if variations else tt.getGlyphSet()
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    hbfont = hb.Font(face)
    if variations:
        hbfont.set_variations(variations)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hbfont, buf, features or {"kern": True, "liga": True})
    order = tt.getGlyphOrder()
    scale = 100.0 / cap  # cap height -> 100 units
    x = 0.0
    paths, glyphs = [], []
    ink = [1e9, 1e9, -1e9, -1e9]
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        pen = SVGPathPen(gs)
        tp = TransformPen(pen, (scale, 0, 0, -scale, (x + pos.x_offset) * scale, 100 - pos.y_offset * scale))
        gs[name].draw(tp)
        d = pen.getCommands()
        bp = BoundsPen(gs)
        gs[name].draw(TransformPen(bp, (scale, 0, 0, -scale, (x + pos.x_offset) * scale, 100 - pos.y_offset * scale)))
        if bp.bounds:
            b = bp.bounds
            ink = [min(ink[0], b[0]), min(ink[1], b[1]), max(ink[2], b[2]), max(ink[3], b[3])]
        if d:
            paths.append(d)
        glyphs.append({"char": text[info.cluster] if info.cluster < len(text) else "", "glyph": name,
                       "x": round(x * scale, 2), "advance": round(pos.x_advance * scale, 2)})
        x += pos.x_advance + tracking * upm / 1000.0
    return {"paths": paths, "glyphs": glyphs, "ink": ink, "cap": cap * scale, "xheight": xh * scale,
            "scale": scale, "upm": upm}


def to_svg(res, color="#111111", pad=2.0, title="Wordmark"):
    x0, y0, x1, y1 = res["ink"]
    x0 -= pad
    y0 -= pad
    x1 += pad
    y1 += pad
    w, h = x1 - x0, y1 - y0
    d = "".join(res["paths"])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.2f} {y0:.2f} {w:.2f} {h:.2f}" '
            f'role="img"><title>{title}</title><path fill="{color}" fill-rule="nonzero" d="{d}"/></svg>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--text", required=True)
    ap.add_argument("--font", help="Google Fonts family name")
    ap.add_argument("--font-file", help="path to a .ttf/.otf the user is licensed to use in a logo")
    ap.add_argument("--weight", type=int, default=400)
    ap.add_argument("--italic", action="store_true")
    ap.add_argument("--tracking", type=float, default=0, help="letter-spacing in 1/1000 em")
    ap.add_argument("--case", choices=["as-is", "upper", "lower"], default="as-is")
    ap.add_argument("--color", default="#111111")
    ap.add_argument("--title")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    kitlib.ensure_deps({"fontTools": "fonttools", "uharfbuzz": "uharfbuzz"})
    if not (a.font or a.font_file):
        ap.error("give --font or --font-file")
    path = a.font_file or fetch_google_font(a.font, a.weight, a.italic)
    res = outline(path, a.text, a.tracking, a.case)
    svg = to_svg(res, a.color, title=a.title or f"{a.text} wordmark")
    kitlib.write(a.out, svg)
    meta = {"text": a.text, "font": a.font or os.path.basename(a.font_file), "weight": a.weight,
            "cap_height": round(res["cap"], 2), "x_height": round(res["xheight"], 2), "baseline_y": 100,
            "cap_top_y": 0, "glyphs": res["glyphs"], "ink_bbox": [round(v, 2) for v in res["ink"]]}
    kitlib.write(os.path.splitext(a.out)[0] + ".meta.json", json.dumps(meta, indent=1))
    print(f"wrote {a.out}  ({len(res['paths'])} glyph paths, cap height 100, baseline y=100)")


if __name__ == "__main__":
    main()
