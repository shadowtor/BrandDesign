#!/usr/bin/env python3
"""Query established public sources instead of inventing type, colour or symbol ideas from memory.

  fonts   Fontsource API (Google Fonts mirror, OFL/Apache licence field, subsets, weights, variable axes)
          live_sources.py fonts --category serif --subset latin-ext --limit 25
          live_sources.py fonts --info Fraunces                     (licence, weights, subsets, is-variable)
  palette TheColorAPI scheme from a seed + Colormind model suggestions (both free, no key)
          live_sources.py palette "#0F7C80" --mode analogic --count 5
  icons   Iconify search across open icon sets: INSPIRATION for what a subject looks like when simplified,
          never artwork to trace (each set has its own licence; check before any reuse)
          live_sources.py icons anchor --limit 12
  fontshare  Fontshare catalogue (link-only licence: do not outline or redistribute; see references/bi-type.md)

All output is data for you to judge. Sources, limits and what each is good for: references/live-sources.md.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

UA = "brand-studio/1.0 (design research; +local)"


def get(url, data=None, timeout=25):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def cmd_fonts(a):
    if a.info:
        f = get("https://api.fontsource.org/v1/fonts/" + urllib.parse.quote(a.info.lower().replace(" ", "-")))
        keys = ("family", "category", "license", "variable", "weights", "styles", "subsets", "version", "lastModified", "source")
        print(json.dumps({k: f.get(k) for k in keys}, indent=1))
        print("Google Fonts page: https://fonts.google.com/specimen/" + urllib.parse.quote(f["family"]))
        return
    q = "https://api.fontsource.org/v1/fonts?"
    if a.category:
        q += "category=" + a.category
    rows = get(q)
    rows = [r for r in rows if r.get("type") == "google"]
    if a.subset:
        rows = [r for r in rows if a.subset in r.get("subsets", [])]
    if a.variable:
        rows = [r for r in rows if r.get("variable")]
    if a.min_weights:
        rows = [r for r in rows if len(r.get("weights", [])) >= a.min_weights]
    if a.query:
        rows = [r for r in rows if a.query.lower() in r["family"].lower()]
    for r in rows[: a.limit]:
        print(f'{r["family"]:<28} {r["category"]:<12} {r["license"]:<8} weights {len(r["weights"])}  {"variable" if r.get("variable") else "static"}')
    print(f"({len(rows)} match; showing {min(len(rows), a.limit)}. Apply the reflex test in references/bi-ai-defaults.md before picking.)")


def cmd_palette(a):
    hx = a.seed.lstrip("#")
    d = get(f"https://www.thecolorapi.com/scheme?hex={hx}&mode={a.mode}&count={a.count}&format=json")
    print(f"TheColorAPI {a.mode} scheme from #{hx}:")
    for c in d["colors"]:
        print(f'  {c["hex"]["value"]}  {c["name"]["value"]}')
    try:
        r, g, b = (int(hx[i:i + 2], 16) for i in (0, 2, 4))
        m = get("http://colormind.io/api/", json.dumps({"model": "default", "input": [[r, g, b], "N", "N", "N", "N"]}).encode())
        print("Colormind (ML suggestion):", "  ".join("#%02x%02x%02x" % tuple(c) for c in m["result"]))
    except Exception as exc:
        print("Colormind unavailable:", exc)
    print("Next: scripts/palette/palette_build.py then palette_audit.py: suggestions are seeds, not decisions.")


def cmd_icons(a):
    d = get("https://api.iconify.design/search?query=" + urllib.parse.quote(a.query) + f"&limit={a.limit}")
    for i in d.get("icons", [])[: a.limit]:
        pfx, name = i.split(":", 1)
        print(f"{i:<40} https://api.iconify.design/{pfx}/{name}.svg")
    print("Inspiration only. Draw your own from primitives (references/bi-logo.md); icon sets have their own licences.")


def cmd_fontshare(a):
    d = get("https://api.fontshare.com/v2/fonts?limit=100")
    for f in d["fonts"]:
        if a.query and a.query.lower() not in f["name"].lower():
            continue
        print(f'{f["name"]:<22} {", ".join(c["name"] if isinstance(c, dict) else str(c) for c in f.get("categories", []))}')
    print("Fontshare licence: link and use via their CDN; no outlining into logos or handing files to clients without checking their licence.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fonts")
    f.add_argument("--category", choices=["serif", "sans-serif", "display", "handwriting", "monospace"])
    f.add_argument("--subset")
    f.add_argument("--variable", action="store_true")
    f.add_argument("--min-weights", type=int)
    f.add_argument("--query")
    f.add_argument("--info")
    f.add_argument("--limit", type=int, default=30)
    f.set_defaults(fn=cmd_fonts)
    p = sub.add_parser("palette")
    p.add_argument("seed")
    p.add_argument("--mode", default="analogic", choices=["monochrome", "monochrome-dark", "monochrome-light", "analogic", "complement", "analogic-complement", "triad", "quad"])
    p.add_argument("--count", type=int, default=5)
    p.set_defaults(fn=cmd_palette)
    i = sub.add_parser("icons")
    i.add_argument("query")
    i.add_argument("--limit", type=int, default=12)
    i.set_defaults(fn=cmd_icons)
    s = sub.add_parser("fontshare")
    s.add_argument("--query")
    s.set_defaults(fn=cmd_fontshare)
    a = ap.parse_args()
    try:
        a.fn(a)
    except Exception as exc:
        sys.exit(f"error: {exc} (offline, or the service changed; see references/live-sources.md for the manual links)")


if __name__ == "__main__":
    main()
