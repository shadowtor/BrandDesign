#!/usr/bin/env python3
"""Render the 1280x640 social card (GitHub repo social preview, link previews) to site/social-card.png.

  python tools/make_social_card.py

All content sits inside a 80 px safe area (GitHub's template asks for a border so nothing is cropped). Uses the skill's own
renderer (headless Chromium) and fetches Schibsted Grotesk (SIL OFL) from Google Fonts. Re-run after changing the marks.
"""
import base64
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, "skills", "brand-studio", "scripts")
sys.path.insert(0, SK)
import kitlib  # noqa: E402

kitlib.ensure_deps({"fontTools": "fonttools", "uharfbuzz": "uharfbuzz"})
import outline_text  # noqa: E402

W, H, SAFE = 1280, 640, 80
OUT = os.path.join(ROOT, "site", "social-card.png")


def font_face(weight):
    p = outline_text.fetch_google_font("Schibsted Grotesk", weight)
    b64 = base64.b64encode(open(p, "rb").read()).decode("ascii")
    return f"@font-face{{font-family:'SG';font-weight:{weight};src:url(data:font/ttf;base64,{b64}) format('truetype')}}"


def mark(slug):
    svg = open(os.path.join(ROOT, "examples", slug, "final", "symbol.svg"), encoding="utf-8").read()
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def tile(slug, label, chosen):
    cls = "tile chosen" if chosen else "tile"
    return (f'<div class="{cls}"><img src="{mark(slug)}"><span class="lab">{label}</span>'
            f'<span class="st">{"chosen" if chosen else "sketch"}</span></div>')


html = f"""<!doctype html><meta charset="utf-8"><style>
{font_face(400)}{font_face(600)}{font_face(800)}
*{{box-sizing:border-box}}html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{background:#eef1f4;color:#14181f;font:400 24px/1.4 'SG',sans-serif;position:relative;
background-image:linear-gradient(rgba(20,24,31,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(20,24,31,.06) 1px,transparent 1px);background-size:32px 32px}}
.safe{{position:absolute;left:{SAFE}px;top:{SAFE}px;right:{SAFE}px;bottom:{SAFE}px;display:grid;grid-template-columns:560px 1fr;gap:48px;align-items:center}}
.name{{font-weight:800;font-size:30px;letter-spacing:-.01em;margin-bottom:22px}}
h1{{margin:0;font-weight:800;font-size:56px;line-height:1.04;letter-spacing:-.02em}}
p{{margin:24px 0 0;color:#4f5966;font-size:25px;line-height:1.35}}
.row{{display:flex;gap:18px;justify-content:flex-end}}
.tile{{width:148px;height:148px;background:#fff;position:relative;display:grid;place-items:center;box-shadow:0 1px 0 rgba(20,24,31,.2)}}
.tile img{{width:56%;filter:grayscale(1)}}
.tile.chosen img{{filter:none}}
.tile.chosen{{outline:4px solid #1f5fd6;outline-offset:4px}}
.lab{{position:absolute;left:10px;bottom:8px;font-size:15px;font-weight:600}}
.st{{position:absolute;right:10px;top:7px;font-size:14px;color:#4f5966}}
.chosen .st{{color:#1f5fd6;font-weight:600}}
.tile::before{{content:"";position:absolute;top:8px;left:8px;width:12px;height:12px;border-top:1px solid #14181f;border-left:1px solid #14181f;opacity:.5}}
.foot{{margin-top:22px;text-align:right;color:#4f5966;font-size:20px}}
</style><body><div class="safe"><div>
<div class="name">brand-studio</div>
<h1>Three logo sketches first. The whole brand after you pick one.</h1>
<p>A skill for Claude Code, Codex and Gemini CLI.</p></div>
<div><div class="row">{tile("kiln", "Kiln", False)}{tile("rookery", "Rookery", False)}{tile("marigold", "Marigold", True)}</div>
<div class="foot">Then the full kit and guidelines</div></div></div></body>"""

kitlib.screenshot(html, W, H, OUT)
print(f"wrote {OUT}  {os.path.getsize(OUT) / 1024:.0f} KB")
