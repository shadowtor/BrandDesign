#!/usr/bin/env python3
"""Merchandise mockups built from the brand's real logo files (flat vector scenes, no stock photos).

Each scene is an SVG (1200x900) with a soft shadow, a garment/object in a brand-derived colour and the logo version
that has enough contrast on that colour (white on dark objects, colour-light on light ones). They are mockups to judge
the logo in use, not production artwork: say so when you present them.

Items: tee, hoodie, tote, mug, cap, notebook, sticker, bottle, apron, poster
Sector -> items (override with brand.json "merch": [...]):
  coffee/food/bakery: mug, tote, apron, tee, cap, sticker       software/saas: tee, hoodie, sticker, mug, notebook, cap
  fashion/retail: tote, tee, hoodie, cap, notebook, poster       services/finance/legal: notebook, mug, tote, poster, tee, bottle
  health/wellness: tote, bottle, tee, mug, notebook, cap          event/education: tee, tote, cap, bottle, sticker, poster
Usage (normally called by build_kit.py):
  python3 scripts/merch.py brand.json --out-dir deliver/mockups [--items tee tote mug]
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib  # noqa: E402
import export_variants as ev  # noqa: E402

import merch_catalog  # noqa: E402


def items_for(brand):
    """Items for this brand's business type (merch_catalog.py) or its explicit brand['merch'] list."""
    return merch_catalog.items_for(brand)


def shade(h, f):
    """f<0 darker, f>0 lighter (towards white)."""
    return kitlib.mix(h, "#000000", -f) if f < 0 else kitlib.mix(h, "#ffffff", f)


def logo_for(variants, ground):
    """Pick the logo version with enough contrast on `ground` (see kitlib.pick_variant)."""
    raw, name = kitlib.pick_variant(variants, ground)
    return raw, name, 0


def place(raw, cx, cy, w, h=None):
    """<g> that fits the logo's ink box inside w x h centred on (cx, cy)."""
    g = kitlib.geometry(raw)
    h = h or w
    s = min(w / g["w"], h / g["h"])
    x = cx - g["w"] * s / 2
    y = cy - g["h"] * s / 2
    body = ev.inner_markup(raw)
    root = re.search(r"<svg\b[^>]*>", raw).group(0)
    carried = "".join(f' {a}="{m.group(1)}"' for a in ("fill", "stroke", "fill-rule", "stroke-width", "stroke-linecap",
                                                         "stroke-linejoin") for m in [re.search(r'\s%s\s*=\s*"([^"]*)"' % a, root)] if m)
    return (f'<g transform="translate({x - g["bbox"][0] * s:.2f} {y - g["bbox"][1] * s:.2f}) scale({s:.4f})"{carried}>'
            f'{body}</g>')


def frame(inner, bg, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" role="img"><title>{label}</title>'
            f'<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="24" stdDeviation="22" flood-color="#000" flood-opacity=".22"/></filter>'
            f'<linearGradient id="fold" x1="0" x2="1"><stop offset="0" stop-color="#000" stop-opacity=".10"/><stop offset=".35" stop-color="#fff" stop-opacity=".05"/>'
            f'<stop offset=".7" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".14"/></linearGradient>'
            f'<linearGradient id="cyl" x1="0" x2="1"><stop offset="0" stop-color="#000" stop-opacity=".22"/><stop offset=".22" stop-color="#fff" stop-opacity=".22"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".30"/></linearGradient></defs>'
            f'<rect width="1200" height="900" fill="{bg}"/>'
            f'<g transform="translate(100 0)">{inner}</g></svg>')


# ------------------------------------------------------------------ garments & objects (1000 x 900 local space)

def tee(c, v, brand):
    body = c["ink"] if kitlib.luminance(c["ink"]) < 0.35 else shade(c["primary"], -0.35)
    lg, _, _ = logo_for(v, body)
    d = ("M330 90 L120 215 L200 385 L290 340 L290 835 L710 835 L710 340 L800 385 L880 215 L670 90 "
         "C640 150 585 182 500 182 C415 182 360 150 330 90 Z")
    return (f'<g filter="url(#sh)"><path d="{d}" fill="{body}"/></g><path d="{d}" fill="url(#fold)"/>'
            f'<path d="M330 90 C360 150 415 182 500 182 C585 182 640 150 670 90 C650 130 590 150 500 150 C410 150 350 130 330 90Z" fill="{shade(body, -0.35)}"/>'
            f'<path d="M290 340 L290 835 M710 340 L710 835" stroke="#000" stroke-opacity=".12" stroke-width="2"/>'
            f'{place(lg, 500, 365, 230, 150)}')


def hoodie(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.5 else c["ink"]
    lg, _, _ = logo_for(v, body)
    d = ("M320 150 L110 300 L150 600 L255 590 L265 840 L735 840 L745 590 L850 600 L890 300 L680 150 "
         "C650 210 580 240 500 240 C420 240 350 210 320 150 Z")
    hood = "M330 150 C340 70 420 40 500 40 C580 40 660 70 670 150 C640 215 580 245 500 245 C420 245 360 215 330 150 Z"
    return (f'<g filter="url(#sh)"><path d="{d}" fill="{body}"/></g><path d="{d}" fill="url(#fold)"/>'
            f'<path d="{hood}" fill="{shade(body, -0.22)}"/><path d="M430 235 C440 330 445 390 440 420 M570 235 C560 330 555 390 560 420" '
            f'stroke="{shade(body, 0.55)}" stroke-width="7" fill="none" stroke-linecap="round"/>'
            f'<path d="M330 640 L670 640 L720 800 L280 800 Z" fill="{shade(body, -0.12)}" stroke="#000" stroke-opacity=".12"/>'
            f'{place(lg, 500, 500, 200, 110)}')


def tote(c, v, brand):
    body = "#efe6d4"
    lg, _, _ = logo_for(v, body)
    return (f'<path d="M330 330 C330 130 400 90 500 90 C600 90 670 130 670 330" fill="none" stroke="{shade(body, -0.18)}" stroke-width="26" stroke-linecap="round"/>'
            f'<g filter="url(#sh)"><path d="M190 300 L810 300 L840 840 L160 840 Z" fill="{body}"/></g>'
            f'<path d="M190 300 L810 300 L840 840 L160 840 Z" fill="url(#fold)"/>'
            f'<path d="M200 330 L800 330" stroke="#000" stroke-opacity=".08" stroke-width="3"/>'
            f'{place(lg, 500, 580, 360, 260)}')


def mug(c, v, brand):
    body = "#fbfaf7"
    lg, _, _ = logo_for(v, body)
    return (f'<path d="M705 340 C860 330 880 560 700 590" fill="none" stroke="{body}" stroke-width="58" stroke-linecap="round"/>'
            f'<path d="M705 340 C860 330 880 560 700 590" fill="none" stroke="#000" stroke-opacity=".10" stroke-width="58" stroke-linecap="round"/>'
            f'<g filter="url(#sh)"><rect x="270" y="250" width="440" height="520" rx="34" fill="{body}"/></g>'
            f'<ellipse cx="490" cy="256" rx="220" ry="34" fill="{shade(body, -0.10)}"/><ellipse cx="490" cy="262" rx="200" ry="26" fill="{c["ink"]}" opacity=".85"/>'
            f'{place(lg, 490, 520, 280, 200)}<rect x="270" y="250" width="440" height="520" rx="34" fill="url(#cyl)"/>')


def cap(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.55 else c["ink"]
    lg, _, _ = logo_for(v, body)
    return (f'<g filter="url(#sh)"><path d="M180 560 C170 250 330 140 500 140 C670 140 830 250 820 560 Z" fill="{body}"/></g>'
            f'<path d="M180 560 C170 250 330 140 500 140 C670 140 830 250 820 560 Z" fill="url(#fold)"/>'
            f'<path d="M500 140 L500 560" stroke="#000" stroke-opacity=".12" stroke-width="3"/>'
            f'<path d="M150 560 C300 520 700 520 850 560 C900 660 700 720 500 720 C300 720 100 660 150 560 Z" fill="{shade(body, -0.25)}"/>'
            f'<ellipse cx="500" cy="152" rx="26" ry="12" fill="{shade(body, -0.3)}"/>'
            f'{place(lg, 500, 370, 250, 150)}')


def notebook(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.6 else c["ink"]
    lg, _, _ = logo_for(v, body)
    return (f'<g transform="rotate(-5 500 450)"><g filter="url(#sh)"><rect x="260" y="70" width="480" height="720" rx="26" fill="{body}"/></g>'
            f'<rect x="260" y="70" width="64" height="720" rx="26" fill="{shade(body, -0.22)}"/>'
            f'<rect x="640" y="70" width="26" height="720" fill="{shade(c["accent"] if "accent" in c else c["primary"], 0.0)}" opacity=".9"/>'
            f'<rect x="260" y="70" width="480" height="720" rx="26" fill="url(#fold)"/>'
            f'{place(lg, 500, 300, 260, 160)}<rect x="400" y="640" width="200" height="4" fill="#fff" opacity=".35"/></g>')


def sticker(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.6 else c["ink"]
    lg, _, _ = logo_for(v, body)
    return (f'<g filter="url(#sh)"><circle cx="500" cy="440" r="330" fill="#ffffff"/></g><circle cx="500" cy="440" r="300" fill="{body}"/>'
            f'<path d="M260 250 C420 150 640 150 760 250 L760 200 C600 80 400 80 240 200Z" fill="#fff" opacity=".10"/>'
            f'{place(lg, 500, 440, 400, 240)}')


def bottle(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.6 else c["ink"]
    lg, _, _ = logo_for(v, body)
    return (f'<g filter="url(#sh)"><rect x="415" y="40" width="170" height="110" rx="22" fill="{shade(body, -0.35)}"/>'
            f'<path d="M430 150 L570 150 C650 190 660 260 660 330 L660 800 C660 830 640 845 610 845 L390 845 C360 845 340 830 340 800 L340 330 C340 260 350 190 430 150 Z" fill="{body}"/></g>'
            f'<path d="M430 150 L570 150 C650 190 660 260 660 330 L660 800 C660 830 640 845 610 845 L390 845 C360 845 340 830 340 800 L340 330 C340 260 350 190 430 150 Z" fill="url(#cyl)"/>'
            f'{place(lg, 500, 560, 200, 220)}')


def apron(c, v, brand):
    body = c["ink"] if kitlib.luminance(c["ink"]) < 0.4 else c["primary"]
    lg, _, _ = logo_for(v, body)
    d = "M360 90 C400 140 600 140 640 90 L690 380 C700 440 760 470 790 880 L210 880 C240 470 300 440 310 380 Z"
    return (f'<path d="M360 90 C380 20 620 20 640 90" fill="none" stroke="{shade(body, -0.2)}" stroke-width="22"/>'
            f'<g filter="url(#sh)"><path d="{d}" fill="{body}"/></g><path d="{d}" fill="url(#fold)"/>'
            f'<rect x="395" y="620" width="210" height="150" rx="10" fill="{shade(body, -0.15)}" stroke="#000" stroke-opacity=".15"/>'
            f'{place(lg, 500, 340, 200, 130)}')


def poster(c, v, brand):
    body = c["paper"]
    lg, _, _ = logo_for(v, body)
    return (f'<g filter="url(#sh)"><rect x="250" y="40" width="500" height="760" fill="#2b2b2b"/></g><rect x="270" y="60" width="460" height="720" fill="{body}"/>'
            f'<rect x="270" y="520" width="460" height="260" fill="{c["primary"]}"/>'
            f'{place(lg, 500, 290, 280, 200)}'
            f'<text x="500" y="640" text-anchor="middle" font-family="Georgia,serif" font-size="34" fill="{kitlib.best_text_on(c["primary"])}">{(brand.get("tagline") or brand["name"])[:38]}</text>')


def travel_mug(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.55 else c["ink"]
    lg, _, _ = logo_for(v, body)
    return (f'<g filter="url(#sh)"><path d="M350 230 L650 230 L615 790 Q500 815 385 790 Z" fill="{body}"/></g>'
            f'<path d="M350 230 L650 230 L615 790 Q500 815 385 790 Z" fill="url(#cyl)"/>'
            f'<rect x="330" y="150" width="340" height="86" rx="30" fill="{shade(body, -0.3)}"/><rect x="420" y="112" width="160" height="46" rx="20" fill="{shade(body, -0.45)}"/>'
            f'{place(lg, 500, 450, 170, 190)}')


def coffee_bag(c, v, brand):
    body = c["ink"] if kitlib.luminance(c["ink"]) < 0.4 else c["primary"]
    lab = "#efe6d4"
    lg, _, _ = logo_for(v, lab)
    return (f'<g filter="url(#sh)"><path d="M290 150 H710 L735 820 H265 Z" fill="{body}"/></g><path d="M290 150 H710 L735 820 H265 Z" fill="url(#fold)"/>'
            f'<rect x="290" y="150" width="420" height="52" fill="{shade(body, -0.25)}"/><path d="M290 176 H710" stroke="#fff" stroke-opacity=".25" stroke-width="3" stroke-dasharray="6 8"/>'
            f'<circle cx="500" cy="262" r="20" fill="{shade(body, -0.4)}"/><rect x="345" y="340" width="310" height="380" rx="16" fill="{lab}"/>{place(lg, 500, 530, 230, 250)}')


def jersey(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.55 else c["ink"]
    trim = c.get("secondary") or c["paper"]
    lg, _, _ = logo_for(v, body)
    d = "M360 90 L130 210 L190 380 L290 335 L290 850 L710 850 L710 335 L810 380 L870 210 L640 90 L500 205 Z"
    return (f'<g filter="url(#sh)"><path d="{d}" fill="{body}"/></g><path d="{d}" fill="url(#fold)"/>'
            f'<path d="M360 90 L500 205 L640 90" fill="none" stroke="{trim}" stroke-width="22" stroke-linejoin="round"/>'
            f'<path d="M150 260 L205 352 M850 260 L795 352" stroke="{trim}" stroke-width="22"/>'
            f'<rect x="290" y="800" width="420" height="22" fill="{trim}"/><path d="M345 340 V800 M655 340 V800" stroke="{trim}" stroke-opacity=".5" stroke-width="8"/>'
            f'{place(lg, 500, 430, 210, 120)}')


def mousemat(c, v, brand):
    body = c["ink"] if kitlib.luminance(c["ink"]) < 0.4 else c["primary"]
    lg, _, _ = logo_for(v, body)
    return (f'<g filter="url(#sh)"><rect x="90" y="250" width="820" height="440" rx="36" fill="{body}"/></g>'
            f'<rect x="108" y="268" width="784" height="404" rx="26" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="3" stroke-dasharray="10 9"/>'
            f'{place(lg, 500, 470, 420, 190)}<ellipse cx="760" cy="580" rx="55" ry="34" fill="#e9e9ee"/>')


def usb(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.6 else c["ink"]
    lg, _, _ = logo_for(v, body)
    return (f'<g transform="rotate(-8 500 450)"><g filter="url(#sh)"><rect x="120" y="395" width="230" height="110" rx="8" fill="#c9ccd2"/>'
            f'<rect x="330" y="360" width="520" height="180" rx="48" fill="{body}"/></g><rect x="150" y="425" width="48" height="26" fill="#6b6f78"/><rect x="215" y="425" width="48" height="26" fill="#6b6f78"/>'
            f'<rect x="330" y="360" width="520" height="180" rx="48" fill="url(#fold)"/><circle cx="790" cy="450" r="22" fill="#fff" opacity=".8"/>'
            f'{place(lg, 560, 450, 150, 110)}</g>')


def lanyard(c, v, brand):
    strap = c["primary"] if kitlib.luminance(c["primary"]) < 0.6 else c["ink"]
    lg, _, _ = logo_for(v, strap)
    lc, _, _ = logo_for(v, "#ffffff")
    return (f'<path d="M300 -20 L470 500 M700 -20 L530 500" stroke="{strap}" stroke-width="64" fill="none"/>'
            f'<g transform="rotate(-19 330 90)">{place(lg, 340, 100, 60, 60)}</g><g transform="rotate(19 670 90)">{place(lg, 660, 100, 60, 60)}</g>'
            f'<rect x="455" y="470" width="90" height="70" rx="12" fill="#b7bbc4"/>'
            f'<g filter="url(#sh)"><rect x="360" y="530" width="280" height="330" rx="26" fill="#ffffff"/></g><rect x="460" y="552" width="80" height="14" rx="7" fill="#d3d6dc"/>'
            f'{place(lc, 500, 690, 200, 150)}<rect x="400" y="790" width="200" height="12" rx="6" fill="{strap}" opacity=".8"/>')


def phone_case(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.6 else c["ink"]
    lg, _, _ = logo_for(v, body)
    return (f'<g filter="url(#sh)"><rect x="320" y="70" width="360" height="760" rx="64" fill="{body}"/></g>'
            f'<rect x="320" y="70" width="360" height="760" rx="64" fill="url(#fold)"/>'
            f'<rect x="352" y="102" width="150" height="150" rx="34" fill="{shade(body, -0.45)}"/><circle cx="400" cy="150" r="28" fill="#15151b"/><circle cx="458" cy="208" r="28" fill="#15151b"/>'
            f'{place(lg, 500, 560, 200, 200)}')


def laptop_sleeve(c, v, brand):
    body = c["ink"] if kitlib.luminance(c["ink"]) < 0.4 else c["primary"]
    lg, _, _ = logo_for(v, body)
    return (f'<g filter="url(#sh)"><rect x="120" y="230" width="760" height="520" rx="40" fill="{body}"/></g><rect x="120" y="230" width="760" height="520" rx="40" fill="url(#fold)"/>'
            f'<path d="M150 300 H850" stroke="#fff" stroke-opacity=".35" stroke-width="5" stroke-dasharray="3 9"/><rect x="800" y="288" width="40" height="26" rx="13" fill="#c9ccd2"/>'
            f'{place(lg, 500, 530, 340, 190)}')


def cable(c, v, brand):
    body = c["primary"] if kitlib.luminance(c["primary"]) < 0.6 else c["ink"]
    lg, _, _ = logo_for(v, "#f4f4f6")
    return (f'<path d="M180 600 C320 760 420 380 560 520 C680 640 700 300 830 380" stroke="#d9dce2" stroke-width="22" fill="none" stroke-linecap="round" filter="url(#sh)"/>'
            f'<rect x="90" y="560" width="120" height="76" rx="14" fill="{body}" transform="rotate(-10 150 600)"/><rect x="40" y="580" width="62" height="36" rx="8" fill="#b7bbc4" transform="rotate(-10 70 600)"/>'
            f'<rect x="800" y="330" width="110" height="76" rx="14" fill="{body}" transform="rotate(-24 855 368)"/><rect x="895" y="318" width="60" height="30" rx="8" fill="#b7bbc4" transform="rotate(-24 925 333)"/>'
            f'<g filter="url(#sh)"><rect x="470" y="540" width="170" height="86" rx="12" fill="#f4f4f6" transform="rotate(6 555 583)"/></g><g transform="rotate(6 555 583)">{place(lg, 555, 583, 130, 56)}</g>')


def sticker_sheet(c, v, brand):
    cols = [c["primary"], c["ink"], c.get("secondary") or c["primary"], c["paper"], c["primary"], c["ink"]]
    out = '<g filter="url(#sh)"><rect x="120" y="90" width="760" height="720" rx="22" fill="#ffffff"/></g>'
    pos = [(290, 250), (500, 250), (710, 250), (290, 470), (500, 470), (710, 470)]
    for i, ((x, y), col) in enumerate(zip(pos, cols)):
        lg, _, _ = logo_for(v, col)
        if i % 2 == 0:
            shape = f'<circle cx="{x}" cy="{y}" r="86" fill="{col}" stroke="#e6e6ea" stroke-width="6"/>'
        else:
            shape = f'<rect x="{x - 86}" y="{y - 78}" width="172" height="156" rx="34" fill="{col}" stroke="#e6e6ea" stroke-width="6"/>'
        out += shape + place(lg, x, y, 118, 90)
    lgw, _, _ = logo_for(v, c["paper"])
    out += f'<rect x="170" y="590" width="660" height="150" rx="75" fill="{c["paper"]}" stroke="#e6e6ea" stroke-width="6"/>{place(lgw, 500, 665, 420, 90)}'
    return out


def business_card(c, v, brand):
    f1 = c["primary"] if kitlib.luminance(c["primary"]) < 0.6 else c["ink"]
    lg1, _, _ = logo_for(v, f1)
    lg2, _, _ = logo_for(v, c["paper"])
    return (f'<g transform="rotate(-8 400 420)" filter="url(#sh)"><rect x="150" y="280" width="560" height="340" rx="14" fill="{c["paper"]}"/></g>'
            f'<g transform="rotate(-8 400 420)">{place(lg2, 270, 380, 90, 90)}<rect x="170" y="520" width="280" height="10" fill="{c["ink"]}" opacity=".5"/><rect x="170" y="545" width="200" height="10" fill="{c["ink"]}" opacity=".3"/></g>'
            f'<g transform="rotate(6 560 520)" filter="url(#sh)"><rect x="330" y="380" width="560" height="340" rx="14" fill="{f1}"/></g><g transform="rotate(6 560 520)">{place(lg1, 610, 550, 340, 190)}</g>')


SCENES = {"tee": tee, "hoodie": hoodie, "tote": tote, "mug": mug, "cap": cap, "notebook": notebook, "sticker": sticker,
          "bottle": bottle, "apron": apron, "poster": poster, "travel-mug": travel_mug, "coffee-bag": coffee_bag,
          "jersey": jersey, "mousemat": mousemat, "usb": usb, "lanyard": lanyard, "phone-case": phone_case,
          "laptop-sleeve": laptop_sleeve, "cable": cable, "sticker-sheet": sticker_sheet, "business-card": business_card}


def build(brand, out_dir, items=None, variants=None, skip=()):
    """Write illustration mockups (.svg + .png) for items without a photo mockup. Returns the item list."""
    c = brand["colors"]
    items = [i for i in (items or items_for(brand)) if i not in skip]
    if variants is None:
        raw = kitlib.read(kitlib.logo_path(brand, "horizontal") or kitlib.logo_path(brand, "symbol"))
        variants = kitlib.variants_of(raw, {**brand["logo"], **c})
    bg = shade(c["paper"], 0.0) if kitlib.luminance(c["paper"]) > 0.7 else "#efefef"
    bgs = kitlib.mix(c["primary"], "#ffffff", 0.9)
    jobs, written = [], []
    for it in items:
        if it not in SCENES:
            continue
        svg = frame(SCENES[it](c, variants, brand), bgs, f"{brand['name']} {it} mockup")
        kitlib.write(os.path.join(out_dir, f"{brand['slug']}-mockup-{it}.svg"), svg)
        jobs.append({"svg": svg, "w": 1200, "h": 900, "out": os.path.join(out_dir, f"{brand['slug']}-mockup-{it}.png")})
        written.append(it)
    if not jobs:
        return written
    kitlib.batch_render(jobs)
    # overview contact sheet (3 x 2)
    from PIL import Image
    cols = 3
    rows = (len(written) + cols - 1) // cols
    tw, th = 600, 450
    sheet = Image.new("RGB", (cols * tw, rows * th), kitlib.rgb(bgs))
    for i, it in enumerate(written):
        im = Image.open(os.path.join(out_dir, f"{brand['slug']}-mockup-{it}.png")).convert("RGB").resize((tw, th), Image.LANCZOS)
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(os.path.join(out_dir, f"{brand['slug']}-merch-overview.png"))
    return written


def write_manifest(brand, mockups_dir):
    """mockups/manifest.json: every real mockup file for this brand, in catalogue order, photo first.
    kind = photo (third-party PSD, preview only) or illustration (drawn by this skill)."""
    import json
    rows = []
    for it in items_for(brand):
        label = merch_catalog.ITEMS[it][0] if it in merch_catalog.ITEMS else it
        photo = os.path.join(mockups_dir, "photo", f"{brand['slug']}-photo-{it}.png")
        flat = os.path.join(mockups_dir, f"{brand['slug']}-mockup-{it}.png")
        if os.path.exists(photo):
            rows.append({"item": it, "label": label, "kind": "photo", "file": os.path.relpath(photo, mockups_dir).replace(os.sep, "/")})
        elif os.path.exists(flat):
            rows.append({"item": it, "label": label, "kind": "illustration", "file": os.path.relpath(flat, mockups_dir).replace(os.sep, "/")})
    kitlib.write(os.path.join(mockups_dir, "manifest.json"), json.dumps(rows, indent=1))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brand_json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--items", nargs="*")
    a = ap.parse_args()
    kitlib.ensure_deps()
    brand = kitlib.load_brand(a.brand_json)
    done = build(brand, a.out_dir, a.items)
    print("mockups:", ", ".join(done), "->", a.out_dir)


if __name__ == "__main__":
    main()
