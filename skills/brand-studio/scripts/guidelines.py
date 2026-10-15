#!/usr/bin/env python3
"""Brand guidelines PDF (A4 landscape) built from brand.json and the real logo/collateral files.

Pages: cover · idea · logo family · clear space + minimum size · versions on grounds · colour · typography · misuse
(generic ones drawn from the real mark + any mark-specific ones in brand.json "misuse_extra") · favicon + app icon ·
social · stationery · merchandise · files + contact.
Honesty rules (references/bi-reproduction.md, bi-kit.md): no invented mission statements or stats; CMYK is labelled
"screen-derived, indicative"; Pantone is left blank for a physical book; clear space is labelled derived;
mock data is labelled as such. Pages whose inputs do not exist are skipped.

  python3 scripts/guidelines.py brand.json --deliver-dir deliver [--png]
"""
import argparse
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "palette"))
import kitlib  # noqa: E402
import collateral as col  # noqa: E402

PW, PH = 1123, 794  # A4 landscape at 96 dpi


def esc(s):
    return html.escape(str(s or ""))


def oklch(h):
    try:
        import colorlib
        L, C, hue = colorlib.hex_to_oklch(h)
        return f"{L:.2f} {C:.2f} {hue:.0f}"
    except Exception:
        return ""


def hsl(h):
    import colorsys
    r, g, b = (v / 255 for v in kitlib.rgb(h))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return f"{hh * 360:.0f}° {s * 100:.0f}% {l * 100:.0f}%"


def page(n, title, body, brand, ground=None, fg=None, kicker=""):
    c = brand["colors"]
    ground = ground or c["paper"]
    fg = fg or c["ink"]
    return (f'<section class="pg" style="background:{ground};color:{fg}">'
            f'<div class="meta"><span>{esc(brand["name"])} · Brand guidelines</span><span>{kicker}</span><span>{n:02d}</span></div>'
            f'<h2>{esc(title)}</h2>{body}</section>')


def build(brand, deliver, png=False):
    c = brand["colors"]
    css_fonts, stack, used = col.font_css(brand)
    vs = col.logo_variants(brand)
    if not vs:
        raise SystemExit("error: no logo files in brand.json")
    main = vs.get("horizontal") or vs.get("vertical") or vs["symbol"]
    pages = []
    n = 0

    def add(*a, **k):
        nonlocal n
        n += 1
        pages.append(page(n, *a, **k))

    def exists(*parts):
        return os.path.exists(os.path.join(deliver, *parts))

    # 1 cover (custom)
    ground = c["primary"] if kitlib.luminance(c["primary"]) < 0.55 else c["ink"]
    fg = kitlib.best_text_on(ground, "#ffffff", c["ink"])
    cover_logo = col.pick(vs.get("vertical") or main, ground)
    pages.append(f'<section class="pg" style="background:{ground};color:{fg}"><div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">'
                 f'{col.img(cover_logo, "height:300px;max-width:700px")}</div>'
                 f'<div class="meta" style="color:{fg}"><span>Brand guidelines</span><span>{esc(brand.get("tagline"))}</span><span>Version 1.0</span></div></section>')
    n = 1

    # 2 idea
    if brand.get("rationale") or brand.get("mechanism"):
        words = brand.get("adjectives") or []
        add("The idea", f'<div class="two"><div><p class="lead">{esc(brand.get("mechanism") or "")}</p><p>{esc(brand.get("rationale") or "")}</p></div>'
            f'<div>{"".join(f"<div class=chip>{esc(w)}</div>" for w in words)}'
            f'<p class="small" style="margin-top:24px">{esc(brand.get("positioning") or "")}</p></div></div>', brand, kicker="Why it looks like this")

    # 3 logo family
    cells = []
    for form, label in (("horizontal", "Horizontal"), ("vertical", "Vertical"), ("square", "Square"), ("symbol", "Symbol"), ("wordmark", "Wordmark")):
        if form in vs:
            cells.append(f'<div class="cell"><div class="stage" style="background:{c["paper"]}">{col.img(vs[form]["colour-light"], "max-width:88%;max-height:150px")}</div><b>{label}</b></div>')
    add("The logo family", f'<div class="grid3">{"".join(cells)}</div><p class="small">Use the horizontal logo by default; the vertical where the space is tall or square; the symbol alone only where the name already appears or the space is under 120 px; the wordmark where a symbol would be redundant.</p>', brand)

    # 4 clear space + min size
    g = kitlib.geometry(kitlib.fit_attrs(main["colour-light"]))
    unit_pct = 25
    lh = 150
    lw = lh * g["w"] / g["h"]
    pad = lh * unit_pct / 100
    body = (f'<div style="display:grid;gap:26px"><div><div style="position:relative;display:inline-block;padding:{pad}px;border:2px dashed {c["primary"]}">'
            f'{col.img(main["colour-light"], f"height:{lh}px")}'
            f'<span class="x" style="top:0;left:0;width:{pad}px;height:{pad}px"></span></div>'
            f'<p class="small">Clear space = <b>x</b> = {unit_pct}% of the logo height on every side. Derived from the artwork, adjust after use.</p></div>'
            f'<div><table><tr><th>Version</th><th>Min. on screen</th><th>Min. in print</th></tr>'
            f'<tr><td>Horizontal</td><td>96 px wide</td><td>25 mm wide</td></tr>'
            f'<tr><td>Vertical</td><td>48 px wide</td><td>14 mm wide</td></tr>'
            f'<tr><td>Symbol</td><td>16 px (use the favicon cut)</td><td>6 mm</td></tr></table>'
            f'<p class="small">Starting values. Confirm for this mark with the 16 px / 32 px renders in the favicon test and one real print proof, then update this table.</p></div></div>')
    add("Clear space and minimum size", body, brand)

    # 5 versions
    grounds = [("Colour, light ground", "colour-light", c["paper"]), ("Colour, dark ground", "colour-dark", c["ink"]),
               ("Black", "black", "#ffffff"), ("White", "white", c["primary"] if kitlib.luminance(c["primary"]) < 0.55 else c["ink"]),
               ("Greyscale", "greyscale", "#ffffff")]
    cells = "".join(f'<div class="cell"><div class="stage" style="background:{gr}">{col.img(main[k], "max-width:84%;max-height:90px")}</div><b>{lab}</b></div>' for lab, k, gr in grounds)
    add("Versions", f'<div class="grid3">{cells}</div><p class="small">Full colour is the default. Use the dark-ground version on {esc(c["ink"])} and photographs; one-colour versions for single-ink print, engraving, embroidery and stamps. Greyscale is for black-and-white print and checking value contrast.</p>', brand)

    # 6 colour
    names = brand.get("color_names") or {}
    sw = []
    roles = [k for k in ("primary", "secondary", "accent", "ink", "paper") if k in c and not (k == "accent" and c.get("accent") == c.get("secondary"))]
    for k in roles:
        h = c[k]
        tc = kitlib.best_text_on(h, "#ffffff", "#111111")
        cm = kitlib.naive_cmyk(h)
        sw.append(f'<div class="sw" style="background:{h};color:{tc}"><b>{esc(names.get(k, k.title()))}</b><span>{h.upper()}</span>'
                  f'<span>RGB {" ".join(map(str, kitlib.rgb(h)))}</span><span>HSL {hsl(h)}</span><span>OKLCH {oklch(h)}</span>'
                  f'<span>CMYK ≈ {" ".join(map(str, cm))} *</span><span>Pantone: assign from a physical book</span></div>')
    pairs = []
    for a_, b_ in (("ink", "paper"), ("paper", "ink"), ("paper", "primary"), ("ink", "primary"), ("primary", "paper"), ("primary", "ink")):
        if a_ in c and b_ in c:
            r = kitlib.contrast(c[a_], c[b_])
            pairs.append(f'<span class="pair" style="background:{c[b_]};color:{c[a_]}">Aa {r:.1f}:1 {"AA" if r >= 4.5 else ("large only" if r >= 3 else "no")}</span>')
    add("Colour", f'<div class="sws">{"".join(sw)}</div><div style="margin-top:14px">{"".join(pairs)}</div>'
        f'<p class="small">* CMYK is derived from the screen colour for reference only. A printer must supply values from the paper profile (FOGRA/GRACoL) and proof them. Contrast chips are WCAG 2.2 ratios for text on that ground.</p>', brand)

    # 7 type
    f = brand.get("fonts") or {}
    add("Typography", f'<div class="two"><div><div class="aa" style="font-family:{stack["display"]}">Aa</div><b>{esc(f.get("display", "Display"))}</b> — headlines, display, the voice'
        f'<p style="font:700 34px/1.15 {stack["display"]};margin:14px 0">{esc(brand.get("tagline") or brand["name"])}</p></div>'
        f'<div><div class="aa" style="font-family:{stack["text"]}">Aa</div><b>{esc(f.get("text", "Text"))}</b> — body copy, interface, small print'
        f'<p style="font:400 15px/1.55 {stack["text"]};margin:14px 0">Body text is set at 16 px on screen with 1.5 line height, or 10 pt in print. Keep line length near 60 characters.</p></div></div>'
        f'<p class="small">Fonts: {", ".join(esc(v) for v in {f.get("display"), f.get("text")} if v)} (Google Fonts, open licence). Fallbacks: Georgia / Arial. Embed code in tokens/fonts.md.</p>', brand)

    # 8 misuse
    mis = []
    L = main["colour-light"]
    items = [("Don't stretch or squash", f'transform:scaleX(1.5)'), ("Don't rotate", "transform:rotate(-14deg)"),
             ("Don't recolour outside the palette", "filter:hue-rotate(140deg) saturate(1.4)"),
             ("Don't add shadows or effects", "filter:drop-shadow(6px 8px 3px rgba(0,0,0,.55))"),
             ("Don't place on low-contrast grounds", "opacity:.9"), ("Don't mirror or rearrange", "transform:scaleX(-1)")]
    for lab, st in items:
        bg = c["primary"] if "low-contrast" in lab else c["paper"]
        lg = L
        mis.append(f'<div class="cell"><div class="stage" style="background:{bg}">{col.img(lg, "max-width:70%;max-height:70px;" + st)}<i class="no">✕</i></div><b>{lab}</b></div>')
    for ex in brand.get("misuse_extra", []):
        p = ex["svg"] if os.path.isabs(ex["svg"]) else os.path.join(brand["_base"], ex["svg"])
        if os.path.exists(p):
            mis.append(f'<div class="cell"><div class="stage" style="background:{c["paper"]}">{col.img(kitlib.read(p), "max-width:70%;max-height:70px")}<i class="no">✕</i></div><b>{esc(ex.get("label"))}</b></div>')
    add("Misuse", f'<div class="grid4">{"".join(mis)}</div><p class="small">Never rebuild the logo by typing the name. Always use the supplied files.</p>', brand)

    # 9 favicon
    if exists("favicons", "favicon-test.png"):
        add("Favicon and app icon", f'<img src="{img_uri(os.path.join(deliver, "favicons", "favicon-test.png"))}" style="max-height:560px;max-width:100%">'
            f'<p class="small">Tested at 16, 32 and 48 px on light and dark tabs; see favicons/favicon-test-report.md.</p>', brand)

    # 10 social
    soc = [p for p in ("kiln",) if False]
    sdir = os.path.join(deliver, "social", "banners")
    shots = [f for f in ("-linkedin-personal.png", "-x-header.png", "-og-image.png") if os.path.exists(os.path.join(sdir, brand["slug"] + f))]
    if shots:
        imgs = "".join(f'<img src="{img_uri(os.path.join(sdir, brand["slug"] + f))}" style="width:100%;margin-bottom:12px;border:1px solid #0002">' for f in shots[:2])
        av = os.path.join(deliver, "social", "avatars", f'{brand["slug"]}-avatar-primary-400.png')
        avimg = f'<img src="{img_uri(av)}" style="width:120px;border-radius:50%;margin-right:16px">' if os.path.exists(av) else ""
        add("Social media", f'<div style="display:flex;align-items:flex-start">{avimg}<div style="flex:1">{imgs}</div></div><p class="small">Avatars keep the mark inside a circle-safe zone. Banners keep content right of the avatar overlap. Re-check platform sizes before uploading.</p>', brand)

    # 11 stationery
    lh = os.path.join(deliver, "stationery", f'{brand["slug"]}-letterhead-sample.png')
    bc = os.path.join(deliver, "stationery", f'{brand["slug"]}-business-card-front.png')
    bb = os.path.join(deliver, "stationery", f'{brand["slug"]}-business-card-back.png')
    if os.path.exists(lh):
        cards = "".join(f'<img src="{img_uri(p)}" style="width:300px;display:block;margin-bottom:12px;box-shadow:0 3px 12px #0003">' for p in (bc, bb) if os.path.exists(p))
        add("Stationery", f'<div style="display:flex;gap:28px"><img src="{img_uri(lh)}" style="height:560px;box-shadow:0 3px 14px #0003"><div>{cards}</div></div>', brand)

    # 12 merchandise: the real mockup files (photographic where we have them, illustrations otherwise), 6 per page
    mdir = os.path.join(deliver, "mockups")
    mf = os.path.join(mdir, "manifest.json")
    if os.path.exists(mf):
        import json as _json
        rows = _json.load(open(mf, encoding="utf-8"))
        per = 6
        for pi in range(0, len(rows), per):
            chunk = rows[pi:pi + per]
            cells = "".join(
                f'<div class="cell"><img src="{img_uri(os.path.join(mdir, r["file"]))}" style="width:100%;height:215px;object-fit:cover;border:1px solid #0002">'
                f'<b>{esc(r["label"])} <span style="font-weight:400;opacity:.65">· {"photographic mockup" if r["kind"] == "photo" else "illustration"}</span></b></div>'
                for r in chunk)
            add("In use: merchandise" + (f" ({pi // per + 1})" if len(rows) > per else ""),
                f'<div class="grid3">{cells}</div><p class="small">Mockups are previews of the logo in use, not production artwork. Items are chosen for what this kind of business would actually make.</p>', brand)

    # 13 files
    ct = brand.get("contact") or {}
    contact_line = ('<p class="small">Questions about usage: ' + esc(ct.get("email")) + '</p>') if ct.get("email") else ""
    add("Files and contact", '<table><tr><th>Folder</th><th>Use</th></tr>'
        '<tr><td>logo/svg</td><td>Web, apps, editing. Preferred.</td></tr><tr><td>logo/pdf</td><td>Print and signage (vector)</td></tr>'
        '<tr><td>logo/png</td><td>Documents, slides, social (transparent)</td></tr><tr><td>logo/jpg</td><td>Places that reject transparency</td></tr>'
        '<tr><td>favicons</td><td>Website tab, home-screen and app icons</td></tr><tr><td>social</td><td>Avatars and banners</td></tr>'
        '<tr><td>stationery</td><td>Letterhead, header/footer, business card, email signature</td></tr><tr><td>tokens</td><td>Colour and font code for developers</td></tr></table>' + contact_line, brand)

    css = (f'{css_fonts}@page{{size:297mm 210mm;margin:0}}*{{box-sizing:border-box}}html,body{{margin:0}}'
           f'.pg{{position:relative;width:{PW}px;height:{PH}px;padding:70px 64px 40px;overflow:hidden;break-after:page;font:400 15px/1.5 {stack["text"]}}}'
           f'.pg h2{{font:700 44px/1.1 {stack["display"]};margin:30px 0 26px}}'
           f'.meta{{position:absolute;top:26px;left:64px;right:64px;display:flex;justify-content:space-between;font:600 11px {stack["text"]};letter-spacing:.08em;text-transform:uppercase;opacity:.7}}'
           f'.two{{display:grid;grid-template-columns:1fr 1fr;gap:48px}}.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.grid4 .stage{{height:130px}}td,th{{white-space:nowrap}}'
           f'.cell b{{display:block;margin-top:8px;font-size:13px}}.stage{{height:180px;display:flex;align-items:center;justify-content:center;border:1px solid #0002;position:relative}}'
           f'.small{{font-size:12px;opacity:.78;max-width:760px}}.lead{{font:600 24px/1.35 {stack["display"]}}}'
           f'.chip{{display:inline-block;margin:0 8px 8px 0;padding:8px 16px;border:1.5px solid currentColor;border-radius:99px;font-weight:600}}'
           f'table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{text-align:left;padding:9px 10px;border-bottom:1px solid #0002}}'
           f'.sws{{display:grid;grid-template-columns:repeat({max(1, len(roles))},1fr);gap:10px}}'
           f'.sw{{border:1px solid #0002;height:360px;padding:14px;display:flex;flex-direction:column;gap:4px;font-size:11.5px;justify-content:flex-end;border-radius:6px}}.sw b{{font-size:17px;margin-bottom:6px}}'
           f'.pair{{display:inline-block;padding:10px 16px;margin:0 8px 8px 0;border:1px solid #0002;font-weight:600;border-radius:4px}}'
           f'.aa{{font-size:150px;line-height:1}}.no{{position:absolute;top:8px;right:10px;color:#d6002a;font-style:normal;font-weight:700}}'
           f'.x{{position:absolute;background:{c["primary"]};opacity:.25}}')
    doc = f'<!doctype html><meta charset=utf-8><title>{esc(brand["name"])} brand guidelines</title><style>{css}</style><body>{"".join(pages)}</body>'
    out = os.path.join(deliver, "guidelines", f'{brand["slug"]}-brand-guidelines.pdf')
    kitlib.print_pdf(doc, out, timeout=120)
    kitlib.write(os.path.join(deliver, "guidelines", f'{brand["slug"]}-brand-guidelines.html'), doc)
    pngs = []
    if png:
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
            d = fitz.open(out)
            for i, pg in enumerate(d):
                p = os.path.join(deliver, "guidelines", "pages", f"page-{i + 1:02d}.png")
                os.makedirs(os.path.dirname(p), exist_ok=True)
                pg.get_pixmap(dpi=110).save(p)
                pngs.append(p)
        except Exception as exc:
            print("page PNGs skipped:", exc)
    return out, len(pages), pngs


def img_uri(path):
    """data: URI for a raster file. Large images (mockup photos, banners) are re-encoded as JPEG <= 1600 px so the PDF stays small."""
    import base64
    import io
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext in ("png", "jpg", "jpeg") and os.path.getsize(path) > 300_000:
        from PIL import Image
        im = Image.open(path)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, "white")
            bg.paste(im, mask=im.split()[3])
            im = bg
        else:
            im = im.convert("RGB")
        im.thumbnail((1600, 1600))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82, optimize=True)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    mime = {"jpg": "jpeg", "svg": "svg+xml"}.get(ext, ext)
    return f"data:image/{mime};base64," + base64.b64encode(open(path, "rb").read()).decode("ascii")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brand_json")
    ap.add_argument("--deliver-dir", required=True)
    ap.add_argument("--png", action="store_true", help="also write page PNGs (needs pymupdf)")
    a = ap.parse_args()
    kitlib.ensure_deps({"fitz": "pymupdf"} if a.png else None)
    brand = kitlib.load_brand(a.brand_json)
    out, n, pngs = build(brand, a.deliver_dir, a.png)
    print(f"guidelines: {out} ({n} pages, {len(pngs)} page PNGs)")


if __name__ == "__main__":
    main()
