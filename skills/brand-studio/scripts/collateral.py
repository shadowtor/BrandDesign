#!/usr/bin/env python3
"""Social avatars/banners and stationery (letterhead, footer, business card, email signature) from the brand's logos.

Social (PNG + JPG; sizes are the platforms' published recommendations at the time of writing, they change: confirm
before uploading):
  avatar 1080 / 800 / 400 (square master, mark kept inside a circle-safe 70% zone), three grounds (primary, ink, paper)
  linkedin-personal 1584x396 · linkedin-company 2256x382 (2x of 1128x191) · x-header 1500x500 · facebook-cover 1640x624 (2x)
  youtube-banner 2560x1440 (content kept in the 1546x423 TV-safe centre) · og-image 1200x630 · instagram-post 1080 · story 1080x1920
  Profile pictures overlap the lower-left of most banners, so the content sits right of centre / inside each safe box.
Stationery: letterhead A4 (PDF + PNG, with and without sample text) · header and footer bands (PNG, transparent) ·
  business card 85x55 mm front/back (PDF with 3 mm bleed + PNG) · email signature (HTML + PNG logo)
Fonts are embedded from the Google Fonts files (OFL/Apache) so pages render in the brand's type.
"""
import argparse
import base64
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib  # noqa: E402

MM = 96 / 25.4


def font_css(brand):
    """@font-face rules embedding the display and text fonts (weights 400/700 text, display weight from brand)."""
    import outline_text
    fonts = brand.get("fonts") or {}
    css, used = [], {}
    for role, default_w in (("display", 700), ("text", 400)):
        fam = fonts.get(role)
        if not fam:
            continue
        weights = {default_w} | ({700} if role == "text" else set())
        if fonts.get(role + "_weight"):
            weights = {int(fonts[role + "_weight"])} | ({700} if role == "text" else set())
        for w in sorted(weights):
            try:
                p = outline_text.fetch_google_font(fam, w)
                b64 = base64.b64encode(open(p, "rb").read()).decode("ascii")
                css.append(f"@font-face{{font-family:'{fam}';font-weight:{w};src:url(data:font/ttf;base64,{b64}) format('truetype')}}")
                used[role] = fam
            except Exception as exc:
                print(f"warning: could not fetch {fam} {w} ({exc}); falling back to system fonts", file=sys.stderr)
    stack = {
        "display": f"'{fonts.get('display')}',Georgia,serif" if fonts.get("display") else "Georgia,serif",
        "text": f"'{fonts.get('text')}','Segoe UI',Arial,sans-serif" if fonts.get("text") else "'Segoe UI',Arial,sans-serif",
    }
    return "".join(css), stack, used


def img(raw, style=""):
    return f'<img src="{kitlib.data_uri(kitlib.fit_attrs(raw))}" style="display:block;{style}">'


def logo_variants(brand):
    out = {}
    for form in ("horizontal", "vertical", "symbol", "wordmark", "square"):
        p = kitlib.logo_path(brand, form)
        if p and os.path.exists(p):
            raw = kitlib.read(p)
            out[form] = kitlib.variants_of(kitlib.tight_viewbox(raw) if form != "square" else raw, {**brand["logo"], **brand["colors"]})
    return out


def pick(vs, ground):
    """Logo variant with enough contrast on `ground` (kitlib.pick_variant)."""
    return kitlib.pick_variant(vs, ground)[0]


# ----------------------------------------------------------------------------------------------- social

BANNERS = {
    # name: (w, h, safe box as fractions x0,y0,x1,y1)
    "linkedin-personal": (1584, 396, (0.34, 0.12, 0.97, 0.88)),
    "linkedin-company": (2256, 382, (0.22, 0.12, 0.92, 0.88)),
    "x-header": (1500, 500, (0.30, 0.14, 0.95, 0.86)),
    "facebook-cover": (1640, 624, (0.24, 0.14, 0.88, 0.80)),
    "youtube-banner": (2560, 1440, (0.2, 0.4, 0.8, 0.6)),
    "og-image": (1200, 630, (0.08, 0.14, 0.92, 0.86)),
    "instagram-post": (1080, 1080, (0.12, 0.12, 0.88, 0.88)),
    "instagram-story": (1080, 1920, (0.10, 0.30, 0.90, 0.70)),
}


def banner_html(brand, vs, css, stack, name, w, h, safe, ground, motif=True):
    c = brand["colors"]
    tag = brand.get("tagline") or ""
    form = "horizontal" if "horizontal" in vs else "symbol"
    lg = pick(vs[form], ground)
    sx0, sy0, sx1, sy1 = (safe[0] * w, safe[1] * h, safe[2] * w, safe[3] * h)
    sw, sh = sx1 - sx0, sy1 - sy0
    fg = kitlib.best_text_on(ground, "#ffffff", c["ink"])
    tall = h > w
    logo_h = sh * (0.42 if tag else 0.6)
    sym = ""
    if motif and "symbol" in vs:
        sraw = vs["symbol"]["white" if kitlib.luminance(ground) < 0.4 else "black"]
        s_h = h * (1.15 if not tall else 0.8)
        sym = (f'<div style="position:absolute;right:{w * 0.03:.0f}px;top:{(h - s_h) / 2:.0f}px;opacity:.10">'
               f'{img(sraw, f"height:{s_h:.0f}px")}</div>')
    tagline = (f'<div style="font:400 {max(18, sh * 0.13):.0f}px/1.2 {stack["text"]};color:{fg};margin-top:{sh * 0.08:.0f}px;opacity:.92">{tag}</div>'
               if tag else "")
    return (f'<!doctype html><meta charset=utf-8><style>{css}html,body{{margin:0;width:{w}px;height:{h}px;overflow:hidden;background:{ground}}}</style>'
            f'<body><div style="position:absolute;inset:0;overflow:hidden">{sym}</div>'
            f'<div style="position:absolute;left:{sx0:.0f}px;top:{sy0:.0f}px;width:{sw:.0f}px;height:{sh:.0f}px;display:flex;flex-direction:column;justify-content:center;align-items:{"center" if tall or name in ("og-image",) else "flex-start"};">'
            f'{img(lg, f"height:{logo_h:.0f}px;max-width:{sw:.0f}px")}{tagline}</div></body>')


def build_social(brand, out_dir, vs, css, stack):
    c = brand["colors"]
    jobs = []
    # avatars
    sym_forms = vs.get("symbol") or vs.get("square") or vs.get("horizontal")
    for gname, ground in (("primary", c["primary"]), ("ink", c["ink"]), ("paper", c["paper"])):
        raw = pick(sym_forms, ground)
        for size in (1080, 800, 400):
            inner = size * 0.58
            html = (f'<!doctype html><meta charset=utf-8><style>html,body{{margin:0;width:{size}px;height:{size}px;background:{ground}}}'
                    f'body{{display:flex;align-items:center;justify-content:center}}</style><body>{img(raw, f"width:{inner:.0f}px;height:{inner:.0f}px;object-fit:contain")}</body>')
            jobs.append((html, size, size, os.path.join(out_dir, "avatars", f"{brand['slug']}-avatar-{gname}-{size}.png")))
    for name, (w, h, safe) in BANNERS.items():
        ground = c["primary"] if kitlib.luminance(c["primary"]) < 0.55 else c["ink"]
        jobs.append((banner_html(brand, vs, css, stack, name, w, h, safe, ground), w, h,
                     os.path.join(out_dir, "banners", f"{brand['slug']}-{name}.png")))
        if name in ("og-image", "linkedin-personal", "x-header"):
            g2 = c["paper"]
            jobs.append((banner_html(brand, vs, css, stack, name, w, h, safe, g2), w, h,
                         os.path.join(out_dir, "banners", f"{brand['slug']}-{name}-light.png")))
    render_pages(jobs)
    for _, _, _, p in jobs:
        kitlib.png_to_jpg(p, p[:-4] + ".jpg", bg="#ffffff")
    return [os.path.relpath(j[3], out_dir) for j in jobs]


def render_pages(jobs):
    """HTML pages -> PNGs, one Chrome run each (pages need real layout and fonts, so they are not sheet-packed)."""
    from concurrent.futures import ThreadPoolExecutor

    def one(j):
        html, w, h, out = j
        os.makedirs(os.path.dirname(out), exist_ok=True)
        kitlib.screenshot(html, w, h, out)
        return out
    with ThreadPoolExecutor(max_workers=3) as ex:
        list(ex.map(one, jobs))


# ----------------------------------------------------------------------------------------------- stationery

def contact_lines(brand):
    ct = brand.get("contact") or {}
    return [v for k, v in ct.items() if v and k in ("address", "phone", "email", "web", "abn")] or [brand["name"]]


def letterhead_html(brand, vs, css, stack, sample=True):
    c = brand["colors"]
    W, H = 210 * MM, 297 * MM
    lg = pick(vs.get("horizontal") or vs["symbol"], c["paper"])
    ct = brand.get("contact") or {}
    cols = [("Address", ct.get("address")), ("Phone", ct.get("phone")), ("Email", ct.get("email")), ("Web", ct.get("web"))]
    cols = [(k, v) for k, v in cols if v]
    foot = "".join(f'<div style="flex:1"><div style="font:700 {7.5}pt {stack["text"]};letter-spacing:.08em;text-transform:uppercase;color:{c["primary"]};margin-bottom:1mm">{k}</div>'
                   f'<div style="font:400 8.5pt/1.35 {stack["text"]};color:{c["ink"]}">{v}</div></div>' for k, v in cols)
    if not foot:
        foot = f'<div style="font:400 8.5pt {stack["text"]};color:{c["ink"]}">{brand["name"]}</div>'
    body = ""
    if sample:
        body = (f'<div style="font:400 10.5pt/1.55 {stack["text"]};color:{c["ink"]}">'
                f'<div style="color:#888;font-size:8pt;margin-bottom:8mm">SAMPLE TEXT (layout preview only)</div>'
                f'<p>12 March 2026</p><p>Alex Example<br>Example Pty Ltd<br>1 Sample Street</p>'
                f'<p style="margin-top:8mm"><b>Re: Sample letter</b></p><p>Dear Alex,</p>'
                f'<p>This paragraph only shows how body text sits under the header and above the footer. Replace it with the real letter.</p>'
                f'<p>Kind regards,<br><br>Name Surname<br>Title</p></div>')
    return (f'<!doctype html><meta charset=utf-8><style>{css}@page{{size:210mm 297mm;margin:0}}html,body{{margin:0;background:#fff}}'
            f'.page{{position:relative;width:210mm;height:297mm;overflow:hidden;background:{c["paper"]}}}</style>'
            f'<body><div class="page"><div style="position:absolute;left:20mm;top:16mm;right:20mm;display:flex;justify-content:space-between;align-items:flex-start">'
            f'{img(lg, "height:15mm")}<div style="width:14mm;height:2mm;background:{c["primary"]};margin-top:3mm"></div></div>'
            f'<div style="position:absolute;left:20mm;right:20mm;top:52mm;bottom:48mm">{body}</div>'
            f'<div style="position:absolute;left:20mm;right:20mm;bottom:14mm;border-top:0.6mm solid {c["primary"]};padding-top:4mm;display:flex;gap:6mm">{foot}</div>'
            f'</div></body>')


def card_html(brand, vs, css, stack, side, bleed=3):
    c = brand["colors"]
    w, h = 85 + 2 * bleed, 55 + 2 * bleed
    ct = brand.get("contact") or {}
    if side == "front":
        ground = c["primary"] if kitlib.luminance(c["primary"]) < 0.55 else c["ink"]
        lg = pick(vs.get("vertical") or vs.get("symbol") or vs["horizontal"], ground)
        inner = f'<div style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">{img(lg, "height:24mm;max-width:60mm")}</div>'
    else:
        ground = c["paper"]
        name = brand.get("contact_name", "Name Surname")
        role = brand.get("contact_role", "Role title")
        lines = "<br>".join(v for k, v in ct.items() if v and k in ("phone", "email", "web"))
        sym = pick(vs.get("symbol") or vs["horizontal"], ground)
        inner = (f'<div style="position:absolute;left:{bleed + 6}mm;top:{bleed + 6}mm">{img(sym, "height:9mm")}</div>'
                 f'<div style="position:absolute;left:{bleed + 6}mm;bottom:{bleed + 6}mm;font:400 7.5pt/1.45 {stack["text"]};color:{c["ink"]}">'
                 f'<div style="font:700 10pt {stack["display"]};margin-bottom:.5mm">{name}</div><div style="color:{c["primary"]};margin-bottom:2.5mm">{role}</div>{lines}</div>')
    return (f'<!doctype html><meta charset=utf-8><style>{css}@page{{size:{w}mm {h}mm;margin:0}}html,body{{margin:0}}'
            f'.card{{position:relative;width:{w}mm;height:{h}mm;background:{ground};overflow:hidden}}</style><body><div class="card">{inner}</div></body>')


def build_stationery(brand, out_dir, vs, css, stack):
    from pypdf import PdfWriter, PdfReader
    outs = []
    for sample, tag in ((True, "sample"), (False, "blank")):
        html = letterhead_html(brand, vs, css, stack, sample)
        pdf = os.path.join(out_dir, f"{brand['slug']}-letterhead-{tag}.pdf")
        kitlib.print_pdf(html, pdf)
        outs.append(pdf)
    jobs = [(letterhead_html(brand, vs, css, stack, True), int(210 * MM * 2 / 2), int(297 * MM), os.path.join(out_dir, f"{brand['slug']}-letterhead-sample.png")),
            (letterhead_html(brand, vs, css, stack, False), int(210 * MM), int(297 * MM), os.path.join(out_dir, f"{brand['slug']}-letterhead-blank.png"))]
    # header / footer bands as transparent artwork for Word/Docs templates
    c = brand["colors"]
    hdr = pick(vs.get("horizontal") or vs["symbol"], c["paper"])
    jobs.append((f'<!doctype html><meta charset=utf-8><style>html,body{{margin:0;background:transparent;width:794px;height:90px}}</style><body style="padding:14px 76px;box-sizing:border-box">{img(hdr, "height:52px")}</body>',
                 794, 90, os.path.join(out_dir, f"{brand['slug']}-letter-header.png")))
    ct = brand.get("contact") or {}
    items = " · ".join(v for k, v in ct.items() if v and k in ("address", "phone", "email", "web"))
    jobs.append((f'<!doctype html><meta charset=utf-8><style>{css}html,body{{margin:0;background:transparent;width:794px;height:84px}}</style>'
                 f'<body style="padding:12px 76px;box-sizing:border-box"><div style="border-top:3px solid {c["primary"]};padding-top:10px;font:400 11px/1.5 {stack["text"]};color:{c["ink"]}">{items or brand["name"]}</div></body>',
                 794, 84, os.path.join(out_dir, f"{brand['slug']}-letter-footer.png")))
    for side in ("front", "back"):
        bl = 3
        html = card_html(brand, vs, css, stack, side, bl)
        pdf = os.path.join(out_dir, f"{brand['slug']}-business-card-{side}-print-bleed.pdf")
        kitlib.print_pdf(html, pdf)
        outs.append(pdf)
        jobs.append((html, int((85 + 2 * bl) * MM), int((55 + 2 * bl) * MM), os.path.join(out_dir, f"{brand['slug']}-business-card-{side}.png")))
    render_pages(jobs)
    for _, _, _, p in jobs:
        kitlib.png_to_jpg(p, p[:-4] + ".jpg", bg="#ffffff")
    # email signature
    ct = brand.get("contact") or {}
    sig_logo = os.path.join(out_dir, f"{brand['slug']}-email-signature-logo.png")
    kitlib.batch_render([{"svg": kitlib.fit_attrs(pick(vs.get("horizontal") or vs["symbol"], "#ffffff")), "w": 480,
                          "h": int(480 / max(0.2, kitlib.geometry(vs.get("horizontal", vs["symbol"])["colour-light"])["w"] / kitlib.geometry(vs.get("horizontal", vs["symbol"])["colour-light"])["h"])), "out": sig_logo}])
    kitlib.write(os.path.join(out_dir, f"{brand['slug']}-email-signature.html"),
                 f'<!-- Host {os.path.basename(sig_logo)} on your site and replace SRC; most mail clients block embedded images. -->\n'
                 f'<div style="font-family:Arial,sans-serif;font-size:13px;color:{c["ink"]};line-height:1.45">'
                 f'<div style="font-weight:700">{brand.get("contact_name", "Name Surname")}</div>'
                 f'<div style="color:{c["primary"]}">{brand.get("contact_role", "Role title")}</div>'
                 f'<div style="margin:8px 0"><img src="SRC/{os.path.basename(sig_logo)}" width="160" alt="{brand["name"]}"></div>'
                 f'<div>{" · ".join(v for k, v in ct.items() if v and k in ("phone", "email", "web"))}</div></div>')
    return [os.path.relpath(p, out_dir) for p in outs]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brand_json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--only", choices=["social", "stationery"])
    a = ap.parse_args()
    kitlib.ensure_deps()
    brand = kitlib.load_brand(a.brand_json)
    css, stack, used = font_css(brand)
    vs = logo_variants(brand)
    if not vs:
        raise SystemExit("error: brand.json has no logo files")
    if a.only in (None, "social"):
        print("social:", len(build_social(brand, os.path.join(a.out_dir, "social"), vs, css, stack)), "images")
    if a.only in (None, "stationery"):
        print("stationery:", build_stationery(brand, os.path.join(a.out_dir, "stationery"), vs, css, stack))


if __name__ == "__main__":
    main()
