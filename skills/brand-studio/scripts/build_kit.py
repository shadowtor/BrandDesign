#!/usr/bin/env python3
"""Build the complete brand deliverables folder from approved artwork + brand.json (template: templates/brand.example.json).

  python3 scripts/build_kit.py brand.json --out deliver [--skip social stationery mockups guidelines tokens favicons]

Output tree
  logo/{svg,png,jpg,pdf}/<slug>-<form>-<variant>.<ext>
        forms:    horizontal · vertical · square · symbol · wordmark   (those present in brand.json "logo")
        variants: colour-light · colour-dark · black · white · greyscale
        png: 256/512/1024/2048 px on the long side, transparent · jpg: 2000 px on white (or the brand ink for the
        dark/white versions) · pdf: vector, one per file
  favicons/  favicon.svg/.ico, 16/32/48, apple-touch, 192/512, maskable, manifest, head snippet, favicon-test.png + report
  social/    avatars (3 grounds x 3 sizes), banners (LinkedIn, X, Facebook, YouTube, OG, Instagram) PNG+JPG
  stationery/ letterhead (sample + blank, PDF+PNG), header/footer bands, business card (print PDF with bleed), signature
  mockups/   merchandise relevant to the sector + overview
  tokens/    palette.json, CSS/SCSS/Tailwind/DTCG tokens, fonts.md
  guidelines/ <slug>-brand-guidelines.pdf (+ html, page PNGs)
  README.md  file map and what to check before use
Stages are independent; a failed stage is reported and the rest continue. Exit code 1 if any stage failed.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib  # noqa: E402

FORMS = ("horizontal", "vertical", "square", "symbol", "wordmark")
DARK_JPG = {"colour-dark", "white"}
STAGES = ("logos", "favicons", "social", "stationery", "photo", "mockups", "tokens", "guidelines")
OPTIONAL = ("photo",)  # needs downloads + heavy deps: only with --photo-mockups


def stage_logos(brand, out):
    c = brand["colors"]
    svg_dir, png_dir, jpg_dir, pdf_dir = (os.path.join(out, "logo", d) for d in ("svg", "png", "jpg", "pdf"))
    jobs, pdfs, jpgs, count = [], [], [], 0
    for form in FORMS:
        p = kitlib.logo_path(brand, form)
        if not p or not os.path.exists(p):
            continue
        raw = kitlib.read(p)
        for variant, svg in kitlib.variants_of(raw, {**brand["logo"], **c}).items():
            base = f"{brand['slug']}-{form}-{variant}"
            kitlib.write(os.path.join(svg_dir, base + ".svg"), svg)
            g = kitlib.geometry(svg)
            ar = g["viewbox"][2] / g["viewbox"][3]
            for long_side in (256, 512, 1024, 2048):
                w, h = (long_side, round(long_side / ar)) if ar >= 1 else (round(long_side * ar), long_side)
                jobs.append({"svg": svg, "w": w, "h": h, "out": os.path.join(png_dir, f"{base}-{long_side}.png")})
            pdfs.append((svg, os.path.join(pdf_dir, base + ".pdf")))
            jpgs.append((os.path.join(png_dir, f"{base}-2048.png"), os.path.join(jpg_dir, base + ".jpg"),
                         c["ink"] if variant in DARK_JPG else "#ffffff"))
            count += 1
    if not count:
        raise RuntimeError("brand.json logo has no existing files")
    kitlib.batch_render(jobs)
    for png, jpg, bg in jpgs:
        kitlib.png_to_jpg(png, jpg, bg=bg)
    kitlib.svgs_to_pdfs(pdfs)
    return f"{count} logo files x svg/png/jpg/pdf"


def stage_favicons(brand, out):
    sym = kitlib.logo_path(brand, "symbol") or kitlib.logo_path(brand, "square") or kitlib.logo_path(brand, "horizontal")
    L = brand["logo"]
    ai = L.get("app_icon") or {}
    cmd = [sys.executable, os.path.join(HERE, "favicon_test.py"), sym, "--out-dir", os.path.join(out, "favicons"),
           "--icon-bg", ai.get("bg", brand["colors"]["primary"]), "--title", brand["name"]]
    if ai.get("fg"):
        cmd += ["--icon-fg", ai["fg"]]
    elif kitlib.luminance(brand["colors"]["primary"]) > 0.6:
        cmd += ["--icon-fg", brand["colors"]["ink"]]
    # favicon_source: a small-size drawing, ideally with its own backing disc so it reads on light AND dark browser tabs
    small = kitlib.logo_path(brand, "favicon_source") or kitlib.logo_path(brand, "symbol_small")
    if small and os.path.exists(small):
        cmd += ["--favicon-source", small]
    dark = os.path.join(out, "logo", "svg", f"{brand['slug']}-symbol-colour-dark.svg")
    if os.path.exists(dark) and not L.get("favicon_source"):
        cmd += ["--dark-svg", dark]
    r = subprocess.run(cmd, capture_output=True, text=True)
    tail = [l for l in r.stdout.splitlines() if "FAIL" in l or "WARN" in l or "failed" in l]
    if r.returncode not in (0, 1):
        raise RuntimeError((r.stderr or r.stdout)[-400:])
    return "; ".join(tail) or "favicon test ran"


def stage_social(brand, out):
    import collateral as col
    css, stack, _ = col.font_css(brand)
    vs = col.logo_variants(brand)
    return f"{len(col.build_social(brand, os.path.join(out, 'social'), vs, css, stack))} images"


def stage_stationery(brand, out):
    import collateral as col
    css, stack, _ = col.font_css(brand)
    vs = col.logo_variants(brand)
    return f"{len(col.build_stationery(brand, os.path.join(out, 'stationery'), vs, css, stack))} PDFs + PNG/JPG"


def stage_mockups(brand, out):
    import merch
    mdir = os.path.join(out, "mockups")
    have_photo = {i for i in merch.items_for(brand) if os.path.exists(os.path.join(mdir, "photo", f"{brand['slug']}-photo-{i}.png"))}
    drawn = merch.build(brand, mdir, skip=have_photo)
    rows = merch.write_manifest(brand, mdir)
    ph = sum(r["kind"] == "photo" for r in rows)
    return f"{ph} photographic + {len(rows) - ph} illustrated mockups ({', '.join(r['item'] for r in rows)})"


def stage_photo(brand, out):
    import psd_mockup
    res = psd_mockup.build_set(brand, os.path.join(out, "mockups", "photo"))
    return "; ".join(f"{i}: {'ok' if os.path.exists(str(r)) else r}" for i, r in res) or "no sector item has a photo mockup page"


def stage_tokens(brand, out):
    c = brand["colors"]
    tdir = os.path.join(out, "tokens")
    os.makedirs(tdir, exist_ok=True)
    pal = os.path.join(tdir, "palette.json")
    pb = os.path.join(HERE, "palette")
    seeds = [c["primary"]] + ([c["accent"]] if c.get("accent") and c["accent"] != c["primary"] else [])
    cmd = [sys.executable, os.path.join(pb, "palette_build.py"), *seeds, "--name", brand["name"], "-o", pal, "-q"]
    if c.get("paper") and kitlib.luminance(c["paper"]) > 0.5 and c["paper"].lower() != "#ffffff":
        cmd += ["--light-bg", c["paper"]]
    if c.get("ink") and kitlib.luminance(c["ink"]) < 0.1:
        cmd += ["--dark-bg", c["ink"]]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[-300:])
    a = subprocess.run([sys.executable, os.path.join(pb, "palette_audit.py"), pal], capture_output=True, text=True)
    kitlib.write(os.path.join(tdir, "palette-audit.txt"), a.stdout)
    e = subprocess.run([sys.executable, os.path.join(pb, "export_tokens.py"), pal, "--out", tdir], capture_output=True, text=True)
    if e.returncode != 0:
        raise RuntimeError((e.stderr or e.stdout)[-300:])
    f = brand.get("fonts") or {}
    fam = [v for v in dict.fromkeys([f.get("display"), f.get("text")]) if v]
    link = "https://fonts.googleapis.com/css2?" + "&".join(f"family={x.replace(' ', '+')}:wght@400;700" for x in fam)
    kitlib.write(os.path.join(tdir, "fonts.md"),
                 f"# Fonts\n\n" + "".join(f"- **{k}**: {v}\n" for k, v in f.items() if k in ("display", "text")) +
                 f"\nBoth are Google Fonts under open licences (check each family's licence file before commercial redistribution; "
                 f"outlining into the logo is permitted for OFL/Apache families).\n\nEmbed:\n\n```html\n<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">\n"
                 f"<link href=\"{link}&display=swap\" rel=\"stylesheet\">\n```\n\nFont files are not shipped here; self-host from Google Fonts if you need offline use.\n")
    first = next((l for l in a.stdout.splitlines() if l.startswith("palette audit")), "audit ran")
    return first


def stage_guidelines(brand, out):
    import guidelines
    pdf, n, pngs = guidelines.build(brand, out, png=True)
    return f"{n} pages -> {os.path.relpath(pdf, out)}"


def write_readme(brand, out, report):
    lines = [f"# {brand['name']} brand kit", "", f"Built {time.strftime('%Y-%m-%d')}. Start with `guidelines/{brand['slug']}-brand-guidelines.pdf`.", "",
             "| Folder | Contents |", "|---|---|"]
    for d, t in (("logo/", "svg · png · jpg · pdf of every logo form in colour-light, colour-dark, black, white, greyscale"),
                 ("favicons/", "tested favicon + app-icon set, head snippet, favicon-test.png"),
                 ("social/", "avatars and banners"), ("stationery/", "letterhead, header/footer, business card, email signature"),
                 ("mockups/", "merchandise mockups (judging aids, not production files)"), ("tokens/", "colour + font tokens for developers"),
                 ("guidelines/", "brand guidelines PDF")):
        if os.path.isdir(os.path.join(out, d.rstrip("/"))):
            lines.append(f"| `{d}` | {t} |")
    lines += ["", "## Build report", ""] + [f"- **{k}**: {v}" for k, v in report.items()]
    lines += ["", "## Before this goes into use", "",
              "- Trademark and domain/handle clearance has **not** been done (IP Australia / WIPO / EUIPO databases; you or a professional).",
              "- CMYK values are screen-derived; Pantone is unassigned. Proof with the printer.",
              "- Social/platform sizes change; re-check before uploading. Open the deployed site once in Chrome and Safari to confirm the favicon.",
              "- Mockups and sample letter text are illustrations only.",
              "- Fonts are open-licence Google Fonts; confirm licences for any font you swap in."]
    kitlib.write(os.path.join(out, "README.md"), "\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brand_json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip", nargs="*", default=[], choices=STAGES)
    ap.add_argument("--photo-mockups", action="store_true", help="also build photographic PSD mockups (downloads from mockups-design.com on demand, cached; slow)")
    a = ap.parse_args()
    kitlib.ensure_deps({"fitz": "pymupdf", "fontTools": "fonttools", **({"psd_tools": "psd-tools[composite]", "numpy": "numpy", "scipy": "scipy", "skimage": "scikit-image"} if a.photo_mockups else {})})
    brand = kitlib.load_brand(a.brand_json)
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    report, failed = {}, False
    for name in STAGES:
        if name in a.skip or (name in OPTIONAL and not a.photo_mockups):
            continue
        t = time.time()
        try:
            report[name] = globals()["stage_" + name](brand, out) + f" ({time.time() - t:.0f}s)"
        except Exception as exc:
            failed = True
            report[name] = f"FAILED: {exc}"
        print(f"[{name}] {report[name]}", flush=True)
    write_readme(brand, out, report)
    print(f"\nkit written to {out}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
