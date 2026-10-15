"""Shared helpers for the brand-studio kit builders.

Rendering is done with headless Chrome/Edge (found by render_png.py). Launching a browser per file is slow, so
files are packed onto big sheets, screenshotted once, and cropped with Pillow. PDFs are made by printing one HTML
document with a named @page per file and splitting it with pypdf (vector output stays vector).

Optional packages (Pillow, pypdf, fonttools, uharfbuzz) are installed on demand through uv:
  python3 scripts/build_kit.py ...   -> re-runs itself under `uv run --with ...` if something is missing.
"""
import base64
import colorsys
import importlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import render_png  # noqa: E402
import svglib  # noqa: E402
import export_variants as ev  # noqa: E402

DEP_MODULES = {"PIL": "pillow", "pypdf": "pypdf"}


def ensure_deps(extra=None):
    """Make sure Pillow/pypdf (+ extra {module: package}) import; otherwise re-run this process under uv."""
    need = dict(DEP_MODULES)
    need.update(extra or {})
    missing = [pkg for mod, pkg in need.items() if importlib.util.find_spec(mod) is None]
    if not missing:
        return
    if os.environ.get("BRAND_STUDIO_UV") == "1":
        raise SystemExit(f"error: could not provide {', '.join(missing)} even through uv")
    uv = shutil.which("uv")
    if not uv:
        raise SystemExit("missing python packages: " + ", ".join(missing) +
                         "\nfix: pip install " + " ".join(missing) + "   (or install uv: https://docs.astral.sh/uv/)")
    cmd = [uv, "run", "--no-project", "--quiet"]
    for pkg in need.values():
        cmd += ["--with", pkg]
    cmd += ["python", *sys.argv]
    env = dict(os.environ, BRAND_STUDIO_UV="1")
    raise SystemExit(subprocess.call(cmd, env=env))


# ----------------------------------------------------------------------------------------------- colour

def hex_norm(h):
    h = (h or "").strip().lower()
    if re.fullmatch(r"#[0-9a-f]{3}", h):
        h = "#" + "".join(c * 2 for c in h[1:])
    return h


def rgb(h):
    h = hex_norm(h)
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def to_hex(r, g, b):
    return "#%02x%02x%02x" % (max(0, min(255, round(r))), max(0, min(255, round(g))), max(0, min(255, round(b))))


def luminance(h):
    return svglib.relative_luminance(hex_norm(h))


def contrast(a, b):
    return svglib.contrast_ratio(hex_norm(a), hex_norm(b))


def grey_of(h):
    """Greyscale by CIE lightness (not HSL), so the grey version shows what a one-ink print will really look like."""
    y = luminance(h)
    l_star = 116 * (y ** (1 / 3)) - 16 if y > 0.008856 else 903.3 * y
    v = ((l_star + 16) / 116) ** 3 if l_star > 8 else l_star / 903.3  # back to linear Y (same value)
    s = 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055
    g = round(255 * s)
    return to_hex(g, g, g)


def best_text_on(bg, light="#ffffff", dark="#111111"):
    return light if contrast(bg, light) >= contrast(bg, dark) else dark


def mix(a, b, t):
    ra, rb = rgb(a), rgb(b)
    return to_hex(*(ra[i] + (rb[i] - ra[i]) * t for i in range(3)))


def naive_cmyk(h):
    """Screen-derived CMYK, for reference only. Real CMYK needs the printer's ICC profile (references/bi-reproduction.md)."""
    r, g, b = (x / 255 for x in rgb(h))
    k = 1 - max(r, g, b)
    if k >= 1:
        return (0, 0, 0, 100)
    c, m, y = ((1 - v - k) / (1 - k) for v in (r, g, b))
    return tuple(round(100 * v) for v in (c, m, y, k))


# ----------------------------------------------------------------------------------------------- svg

PAINT_ATTR = ev.PAINT_ATTR
PAINT_CSS = ev.PAINT_CSS


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text, binary=False):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as fh:
        fh.write(text)


def map_colors(raw, fn):
    """Replace every solid fill/stroke/stop colour with fn(hex) (gradients stay but their stops are mapped)."""
    def swap(value):
        v = value.strip()
        low = v.lower()
        if low in ("none", "transparent") or low.startswith("url("):
            return v
        norm = svglib.normalize_color(v)
        if norm is None:
            return v
        return fn(norm)
    raw = PAINT_ATTR.sub(lambda m: f'{m.group(1)}="{swap(m.group(2))}"', raw)
    raw = PAINT_CSS.sub(lambda m: f"{m.group(1)}:{swap(m.group(2))}", raw)
    return raw


def used_colors(raw):
    cols = []
    for _, v in PAINT_ATTR.findall(raw) + PAINT_CSS.findall(raw):
        n = svglib.normalize_color(v.strip())
        if n and n not in cols:
            cols.append(n)
    return cols


def variants_of(raw, spec):
    """Return {variant: svg_text} for one logo form. spec = brand['logo'] + palette ('paper', 'ink')."""
    paper = hex_norm(spec.get("paper", "#ffffff"))
    out = {"colour-light": raw}
    # dark version: explicit map wins; otherwise lift colours that would vanish on a dark ground
    dmap = {hex_norm(k): hex_norm(v) for k, v in (spec.get("dark_map") or {}).items()}
    ground = hex_norm(spec.get("dark_ground", spec.get("ink", "#111111")))

    def to_dark(c):
        c = hex_norm(c)
        if c in dmap:
            return dmap[c]
        if contrast(c, ground) >= 3.0:
            return c
        return paper if luminance(c) < luminance(ground) + 0.2 else c
    out["colour-dark"] = map_colors(raw, to_dark)
    out["black"] = ev.recolor(raw, "#000000", keep_white=False)
    out["white"] = ev.recolor(raw, "#ffffff", keep_white=False)
    out["greyscale"] = map_colors(raw, grey_of)
    return out


def svg_size(raw):
    root = svglib.ET.fromstring(raw.encode("utf-8")) if hasattr(svglib, "ET") else None
    vb = svglib.view_box(root) if root is not None else (0, 0, 256, 256)
    return vb[2], vb[3]


def data_uri(raw):
    return "data:image/svg+xml;base64," + base64.b64encode(raw.encode("utf-8")).decode("ascii")


def tight_viewbox(raw, pad=0.0):
    """Crop an SVG's viewBox to its painted bounding box (+ pad fraction of the longer side)."""
    root = svglib.load_svg_text(raw) if hasattr(svglib, "load_svg_text") else None
    if root is None:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(raw.encode("utf-8"))
    geo = svglib.document_geometry(root)
    bb = geo.get("bbox")
    if not bb:
        return raw
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    p = max(w, h) * pad
    vb = f"{bb[0] - p:.2f} {bb[1] - p:.2f} {w + 2 * p:.2f} {h + 2 * p:.2f}"
    raw = re.sub(r'viewBox\s*=\s*"[^"]*"', f'viewBox="{vb}"', raw, count=1)
    raw = re.sub(r'(<svg\b[^>]*?)\swidth\s*=\s*"[^"]*"', r"\1", raw, count=1)
    raw = re.sub(r'(<svg\b[^>]*?)\sheight\s*=\s*"[^"]*"', r"\1", raw, count=1)
    return raw


def geometry(raw):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(raw.encode("utf-8"))
    g = svglib.document_geometry(root)
    vb = svglib.view_box(root)
    bb = g.get("bbox") or (vb[0], vb[1], vb[0] + vb[2], vb[1] + vb[3])
    return {"viewbox": vb, "bbox": bb, "w": bb[2] - bb[0], "h": bb[3] - bb[1]}


def fit_attrs(raw):
    """Remove fixed width/height so an <img>/CSS box can scale the SVG."""
    raw = re.sub(r'(<svg\b[^>]*?)\swidth\s*=\s*"[^"]*"', r"\1", raw, count=1)
    raw = re.sub(r'(<svg\b[^>]*?)\sheight\s*=\s*"[^"]*"', r"\1", raw, count=1)
    return raw


# ----------------------------------------------------------------------------------------------- raster

def _chrome_args(tmp, w, h):
    return ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
            "--use-mock-keychain", "--password-store=basic", "--disable-extensions", "--allow-file-access-from-files",
            "--default-background-color=00000000", f"--window-size={w},{h}",
            f"--user-data-dir={os.path.join(tmp, 'profile')}"]


def screenshot(html_text, w, h, out_png):
    """HTML string -> PNG (transparent where the page is)."""
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "p.html")
        write(page, html_text)
        render_png.screenshot_html(page, out_png, w, h)


def print_pdf(html_text, out_pdf, timeout=60):
    chrome = render_png.find_chrome()
    if not chrome:
        raise RuntimeError("no Chromium-based browser found")
    with tempfile.TemporaryDirectory() as tmp:
        page = os.path.join(tmp, "p.html")
        write(page, html_text)
        shot = os.path.join(tmp, "o.pdf")
        cmd = [chrome, *_chrome_args(tmp, 1200, 900), "--no-pdf-header-footer", f"--print-to-pdf={shot}",
               "file://" + page]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        end = time.time() + timeout
        last = -1
        while time.time() < end:
            if os.path.exists(shot):
                s = os.path.getsize(shot)
                if s > 0 and s == last:
                    break
                last = s
            time.sleep(0.4)
        render_png._stop(proc)
        if not os.path.exists(shot):
            raise RuntimeError("chrome produced no PDF")
        os.makedirs(os.path.dirname(os.path.abspath(out_pdf)), exist_ok=True)
        shutil.move(shot, out_pdf)


MAX_SHEET = 7000


def batch_render(jobs, bg=None):
    """jobs: [{'svg': text, 'w': px, 'h': px, 'out': path.png, 'bg': optional css colour}] -> writes every PNG.

    Packs the jobs onto sheets, screenshots each sheet once, crops with Pillow."""
    from PIL import Image
    pending = sorted(jobs, key=lambda j: -j["h"])
    sheets = []
    for j in pending:
        placed = False
        for s in sheets:
            if s["x"] + j["w"] <= MAX_SHEET and s["row_y"] + j["h"] <= MAX_SHEET:
                j["pos"] = (s["x"], s["row_y"])
                s["x"] += j["w"]
                s["row_h"] = max(s["row_h"], j["h"])
                s["jobs"].append(j)
                placed = True
                break
            if s["row_y"] + s["row_h"] + j["h"] <= MAX_SHEET and j["w"] <= MAX_SHEET:
                s["row_y"] += s["row_h"]
                s["x"], s["row_h"] = 0, 0
                j["pos"] = (0, s["row_y"])
                s["x"] = j["w"]
                s["row_h"] = j["h"]
                s["jobs"].append(j)
                placed = True
                break
        if not placed:
            sheets.append({"x": j["w"], "row_y": 0, "row_h": j["h"], "jobs": [j]})
            j["pos"] = (0, 0)
    for s in sheets:
        sw = max(j["pos"][0] + j["w"] for j in s["jobs"])
        sh = max(j["pos"][1] + j["h"] for j in s["jobs"])
        items = []
        for j in s["jobs"]:
            x, y = j["pos"]
            fill = f"background:{j['bg']};" if j.get("bg") else ""
            items.append(f'<img style="position:absolute;left:{x}px;top:{y}px;width:{j["w"]}px;height:{j["h"]}px;{fill}" '
                         f'src="{data_uri(j["svg"])}">')
        html = (f"<!doctype html><meta charset=utf-8><style>html,body{{margin:0;background:transparent;width:{sw}px;"
                f"height:{sh}px;overflow:hidden}}img{{display:block}}</style><body>{''.join(items)}</body>")
        with tempfile.TemporaryDirectory() as tmp:
            sheet_png = os.path.join(tmp, "sheet.png")
            last_err = None
            for _ in range(2):
                try:
                    screenshot(html, sw, sh, sheet_png)
                    break
                except Exception as exc:  # one retry: a browser can fail once on a busy machine
                    last_err = exc
            else:
                raise RuntimeError(f"sheet render failed: {last_err}")
            im = Image.open(sheet_png).convert("RGBA")
            for j in s["jobs"]:
                x, y = j["pos"]
                crop = im.crop((x, y, x + j["w"], y + j["h"]))
                os.makedirs(os.path.dirname(os.path.abspath(j["out"])), exist_ok=True)
                crop.save(j["out"])
    return len(jobs)


def png_to_jpg(png, jpg, bg="#ffffff", quality=92):
    from PIL import Image
    im = Image.open(png).convert("RGBA")
    base = Image.new("RGB", im.size, rgb(bg))
    base.paste(im, mask=im.split()[3])
    os.makedirs(os.path.dirname(os.path.abspath(jpg)), exist_ok=True)
    base.save(jpg, "JPEG", quality=quality, subsampling=0, optimize=True)


def svgs_to_pdfs(items):
    """items: [(svg_text, out_pdf)] -> one vector PDF per svg, page = the svg's own aspect (pt-ish units)."""
    from pypdf import PdfReader, PdfWriter
    if not items:
        return
    pages, css = [], []
    for i, (raw, _) in enumerate(items):
        g = geometry(raw)
        vb = g["viewbox"]
        w = 600.0
        h = round(w * vb[3] / vb[2], 2)
        css.append(f"@page p{i}{{size:{w}px {h}px;margin:0}}.p{i}{{page:p{i};width:{w}px;height:{h}px}}")
        pages.append(f'<div class="pg p{i}"><img src="{data_uri(raw)}" style="display:block;width:{w}px;height:{h}px"></div>')
    html = ("<!doctype html><meta charset=utf-8><style>html,body{margin:0;padding:0}.pg{break-after:page;overflow:hidden}"
            + "".join(css) + "</style><body>" + "".join(pages) + "</body>")
    with tempfile.TemporaryDirectory() as tmp:
        combined = os.path.join(tmp, "all.pdf")
        print_pdf(html, combined)
        reader = PdfReader(combined)
        n = len(reader.pages)
        for i, (_, out) in enumerate(items):
            if i >= n:
                break
            w = PdfWriter()
            w.add_page(reader.pages[i])
            os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
            with open(out, "wb") as fh:
                w.write(fh)
        if n != len(items):
            print(f"warning: expected {len(items)} PDF pages, Chrome printed {n} (blank trailing pages are dropped)",
                  file=sys.stderr)


def split_pages(html_text, outs, page_css):
    """Print an HTML doc whose top-level .pg elements are pages; write one PDF with all pages."""
    print_pdf(html_text, outs)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "brand"


def load_brand(path):
    with open(path, encoding="utf-8") as fh:
        b = json.load(fh)
    base = os.path.dirname(os.path.abspath(path))
    b["_base"] = base
    b.setdefault("slug", slugify(b["name"]))
    c = b.setdefault("colors", {})
    c.setdefault("ink", "#111111")
    c.setdefault("paper", "#ffffff")
    c.setdefault("primary", c["ink"])
    for k in list(c):
        c[k] = hex_norm(c[k])
    return b


def logo_path(brand, key):
    p = (brand.get("logo") or {}).get(key)
    if not p:
        return None
    return p if os.path.isabs(p) else os.path.join(brand["_base"], p)


def pick_variant(variants, ground):
    """Choose the logo version for a ground: the first of colour-light, colour-dark, black, white whose colours all
    reach 2:1 and at least one reaches 3:1 against it (accents may be lighter than the main colour); else the best."""
    for n in ("colour-light", "colour-dark"):
        cs = [contrast(c, ground) for c in (used_colors(variants[n]) or ["#000000"])]
        if min(cs) >= 1.2 and max(cs) >= 3.0:
            return variants[n], n
    n = "white" if contrast("#ffffff", ground) >= contrast("#000000", ground) else "black"
    return variants[n], n
