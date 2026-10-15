#!/usr/bin/env python3
"""Compose horizontal, vertical and square lockups from a symbol SVG and a wordmark SVG.

This gives the first, rule-based version of each lockup (relative sizes and gap derived from the artwork, not
eyeballed). Look at the render and tune --sym-scale / --gap / --word-width, then keep the numbers: they go into the
guidelines (clear space and minimum size are derived from them). Optical alignment is still a designer's job.

  horizontal: symbol height = sym_scale x wordmark cap height (default 2.4), vertically centred on the cap band
              (--align cap) or on the wordmark's ink box (--align ink); gap = gap x symbol height (default 0.30)
  vertical:   symbol on top, centred; wordmark width = word_width x symbol width (default 1.55); gap as above
  square:     the vertical lockup centred on a 1:1 canvas with --pad padding (default 0.14)

Usage:
  python3 scripts/compose_lockup.py symbol.svg wordmark.svg --out-dir work/lockups [--tagline-svg tag.svg]
Outputs: horizontal.svg, vertical.svg, square.svg and lockup.json (the numbers used).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib  # noqa: E402
import export_variants as ev  # noqa: E402


def part(path):
    raw = kitlib.read(path)
    g = kitlib.geometry(raw)
    return raw, g


def embed(raw, g, x, y, scale):
    """<g> placing the SVG's content so its ink bbox top-left lands on (x, y) at the given scale."""
    body = ev.inner_markup(raw)
    tx = x - g["bbox"][0] * scale
    ty = y - g["bbox"][1] * scale
    root = re.search(r"<svg\b[^>]*>", raw).group(0)
    carried = ""
    for attr in ("fill", "stroke", "fill-rule", "clip-rule", "stroke-width", "stroke-linecap", "stroke-linejoin"):
        m = re.search(r'\s%s\s*=\s*"([^"]*)"' % attr, root)
        if m:
            carried += f' {attr}="{m.group(1)}"'
    return f'<g transform="translate({tx:.3f} {ty:.3f}) scale({scale:.5f})"{carried}>{body}</g>'


def svg_doc(inner, w, h, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" role="img">'
            f'<title>{title}</title>{inner}</svg>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol")
    ap.add_argument("wordmark")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--title", default="Logo")
    ap.add_argument("--sym-scale", type=float, default=2.4, help="symbol height / wordmark cap height (horizontal)")
    ap.add_argument("--gap", type=float, default=0.30, help="gap / symbol height")
    ap.add_argument("--word-width", type=float, default=1.55, help="wordmark width / symbol width (vertical)")
    ap.add_argument("--align", choices=["cap", "ink"], default="ink")
    ap.add_argument("--cap-height", type=float, help="wordmark cap height in its own units (from outline_text meta)")
    ap.add_argument("--pad", type=float, default=0.14)
    a = ap.parse_args()

    sraw, sg = part(a.symbol)
    wraw, wg = part(a.wordmark)
    cap = a.cap_height or wg["h"] * 0.82  # fallback guess; the outline_text meta file is exact
    meta = os.path.splitext(a.wordmark)[0] + ".meta.json"
    if not a.cap_height and os.path.exists(meta):
        cap = json.load(open(meta, encoding="utf-8")).get("cap_height", cap)

    # horizontal: scale the wordmark to 1 and the symbol to sym_scale x cap
    sym_h = a.sym_scale * cap
    s_s = sym_h / sg["h"]
    sym_w = sg["w"] * s_s
    gap = a.gap * sym_h
    word_h = wg["h"]
    if a.align == "cap":
        wy = (sym_h - cap) / 2
    else:
        wy = (sym_h - word_h) / 2
    total_w = sym_w + gap + wg["w"]
    total_h = max(sym_h, wy + word_h)
    inner = embed(sraw, sg, 0, 0, s_s) + embed(wraw, wg, sym_w + gap, wy, 1.0)
    kitlib.write(os.path.join(a.out_dir, "horizontal.svg"), svg_doc(inner, total_w, total_h, a.title + " horizontal"))

    # vertical
    word_w = a.word_width * sg["w"] * 1.0
    s_w = word_w / wg["w"]
    s_v = 1.0
    v_gap = a.gap * sg["h"]
    vw = max(sg["w"], word_w)
    inner = (embed(sraw, sg, (vw - sg["w"]) / 2, 0, s_v)
             + embed(wraw, wg, (vw - word_w) / 2, sg["h"] + v_gap, s_w))
    vh = sg["h"] + v_gap + wg["h"] * s_w
    kitlib.write(os.path.join(a.out_dir, "vertical.svg"), svg_doc(inner, vw, vh, a.title + " vertical"))

    # square: vertical lockup centred in a 1:1 canvas
    side = max(vw, vh) / (1 - 2 * a.pad)
    ox, oy = (side - vw) / 2, (side - vh) / 2
    inner = f'<g transform="translate({ox:.2f} {oy:.2f})">{inner}</g>'
    kitlib.write(os.path.join(a.out_dir, "square.svg"), svg_doc(inner, side, side, a.title + " square"))

    nums = {"sym_scale": a.sym_scale, "gap": a.gap, "word_width": a.word_width, "align": a.align, "pad": a.pad,
            "cap_height": round(cap, 3), "horizontal_size": [round(total_w, 2), round(total_h, 2)],
            "vertical_size": [round(vw, 2), round(vh, 2)]}
    kitlib.write(os.path.join(a.out_dir, "lockup.json"), json.dumps(nums, indent=1))
    print(f"wrote horizontal.svg vertical.svg square.svg lockup.json in {a.out_dir}")


if __name__ == "__main__":
    main()
