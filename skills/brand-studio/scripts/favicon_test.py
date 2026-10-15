#!/usr/bin/env python3
"""Build the favicon / app-icon set for a mark and TEST it. Exit code 1 if a hard check fails.

Builds (through export_variants.py --web-icons): favicon.svg, favicon.ico (16/32/48), favicon-16/32/48.png,
apple-touch-icon.png (180), icon-192.png, icon-512.png, maskable-512.png, site.webmanifest, head-snippet.html.
Then checks the files themselves and the way the mark looks at tab size:

  hard checks (fail the run)
    files exist · ICO header + embedded PNG sizes (16/32/48) · PNG dimensions · manifest is valid JSON and lists
    192 + 512 (+ a maskable icon) with files that exist · SVG favicon has a square viewBox and no <text>/<image> ·
    maskable icon keeps all artwork inside the central 80% circle (the platform safe zone) · 16 px mark is not blank
  warnings (heuristic, say so when you report them)
    ink coverage at 16 px outside 8–80% · mark/tab contrast < 3:1 on a light or dark tab · parts merging at 16 px
    (fewer ink blobs at 16 px than at 64 px) · tiny favicon source difference

It also writes favicon-test.png: every size at 1x and enlarged 8x (nearest neighbour, so you see the real pixels) on
a light tab, a dark tab, the apple-touch tile and the maskable tile with its safe-zone circle.
A real browser is still the last word: open the site once in Chrome/Safari after deploying (the report says so).

Usage:
  python3 scripts/favicon_test.py symbol.svg --out-dir deliver/favicons --icon-bg "#0F7C80" \
      [--icon-fg "#ffffff"|keep] [--favicon-source symbol-small.svg] [--dark-svg symbol-dark.svg]
"""
import argparse
import json
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib  # noqa: E402

LIGHT_TAB = "#dee1e6"   # Chrome light tab strip
DARK_TAB = "#35363a"    # Chrome dark tab strip
FONT_PATHS = ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]


def font(size):
    from PIL import ImageFont
    for p in FONT_PATHS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def png_dims(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def parse_ico(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < 6:
        return None
    rsv, typ, n = struct.unpack("<HHH", data[:6])
    if rsv != 0 or typ != 1:
        return None
    out = []
    for i in range(n):
        w, h, _, _, _, bpp, size, off = struct.unpack("<BBBBHHII", data[6 + 16 * i:22 + 16 * i])
        blob = data[off:off + size]
        out.append({"w": w or 256, "h": h or 256, "png": blob[:8] == b"\x89PNG\r\n\x1a\n", "bytes": size})
    return out


def composite(png, bg, size=None):
    from PIL import Image
    im = Image.open(png).convert("RGBA")
    if size and im.size != (size, size):
        im = im.resize((size, size), Image.LANCZOS)
    base = Image.new("RGBA", im.size, kitlib.rgb(bg) + (255,))
    base.alpha_composite(im)
    return base


def ink_stats(png):
    """(coverage, mean ink colour hex, blob count) of the opaque artwork in a PNG."""
    from PIL import Image
    im = Image.open(png).convert("RGBA")
    px = im.load()
    w, h = im.size
    n = 0
    rs = gs = bs = 0
    mask = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, al = px[x, y]
            if al > 128:
                n += 1
                rs, gs, bs = rs + r, gs + g, bs + b
                mask[y][x] = True
    mean = kitlib.to_hex(rs / n, gs / n, bs / n) if n else "#000000"
    seen = [[False] * w for _ in range(h)]
    blobs = 0
    for y in range(h):
        for x in range(w):
            if mask[y][x] and not seen[y][x]:
                blobs += 1
                stack = [(x, y)]
                seen[y][x] = True
                while stack:
                    cx, cy = stack.pop()
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < w and 0 <= ny < h and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            stack.append((nx, ny))
    return n / (w * h), mean, blobs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--icon-bg", default="#111111")
    ap.add_argument("--icon-fg", default="#ffffff")
    ap.add_argument("--favicon-source")
    ap.add_argument("--dark-svg", help="mark recoloured for dark tabs; written into favicon.svg as a dark-mode variant")
    ap.add_argument("--title", default="Favicon")
    ap.add_argument("--skip-build", action="store_true", help="only test files already in --out-dir")
    a = ap.parse_args()
    kitlib.ensure_deps()
    from PIL import Image, ImageDraw
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)

    if not a.skip_build:
        cmd = [sys.executable, os.path.join(HERE, "export_variants.py"), a.symbol, "--out-dir", out, "--name", "symbol",
               "--title", a.title, "--icon-bg", a.icon_bg, "--icon-fg", a.icon_fg, "--web-icons"]
        if a.favicon_source:
            cmd += ["--favicon-source", a.favicon_source]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout + r.stderr)
            raise SystemExit("error: export_variants failed")

    results = []  # (level, name, detail)

    def hard(ok, name, detail=""):
        results.append(("PASS" if ok else "FAIL", name, detail))

    def warn(ok, name, detail=""):
        results.append(("ok" if ok else "WARN", name, detail))

    need = ["favicon.svg", "favicon.ico", "favicon-16.png", "favicon-32.png", "favicon-48.png", "apple-touch-icon.png",
            "icon-192.png", "icon-512.png", "maskable-512.png", "site.webmanifest", "head-snippet.html"]
    for f in need:
        hard(os.path.exists(os.path.join(out, f)), f"file {f}")
    if any(r[0] == "FAIL" for r in results):
        report(results, out)
        raise SystemExit(1)

    # optional dark-mode variant inside favicon.svg
    svg_path = os.path.join(out, "favicon.svg")
    raw = kitlib.read(svg_path)
    if a.dark_svg:
        import re
        dark = kitlib.read(a.dark_svg)
        light_body = re.sub(r"</?svg\b[^>]*>", "", raw, flags=re.S)
        dark_body = re.sub(r"</?svg\b[^>]*>", "", kitlib.fit_attrs(dark), flags=re.S)
        vb = re.search(r'viewBox="([^"]+)"', raw).group(1)
        raw = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}"><title>{a.title}</title>'
               f'<style>.d{{display:none}}@media (prefers-color-scheme:dark){{.l{{display:none}}.d{{display:inline}}}}</style>'
               f'<g class="l">{re.sub(r"<title>.*?</title>", "", light_body, flags=re.S)}</g>'
               f'<g class="d">{re.sub(r"<title>.*?</title>", "", dark_body, flags=re.S)}</g></svg>')
        kitlib.write(svg_path, raw)

    # ---- structure checks
    ico = parse_ico(os.path.join(out, "favicon.ico"))
    hard(bool(ico), "favicon.ico header")
    if ico:
        sizes = sorted((e["w"], e["h"]) for e in ico)
        hard({(16, 16), (32, 32), (48, 48)} <= set(sizes), "favicon.ico holds 16, 32 and 48 px", str(sizes))
        hard(all(e["png"] for e in ico), "favicon.ico entries are PNG data")
    for f, want in [("favicon-16.png", 16), ("favicon-32.png", 32), ("favicon-48.png", 48), ("apple-touch-icon.png", 180),
                    ("icon-192.png", 192), ("icon-512.png", 512), ("maskable-512.png", 512)]:
        d = png_dims(os.path.join(out, f))
        hard(d == (want, want), f"{f} is {want}x{want}", str(d))
    try:
        man = json.loads(kitlib.read(os.path.join(out, "site.webmanifest")))
        icons = man.get("icons", [])
        have = {i.get("sizes") for i in icons}
        hard({"192x192", "512x512"} <= have, "manifest lists 192 and 512 icons", str(sorted(h for h in have if h)))
        hard(any("maskable" in (i.get("purpose") or "") for i in icons), "manifest has a maskable icon")
        hard(all(os.path.exists(os.path.join(out, os.path.basename(i["src"]))) for i in icons), "manifest icon files exist")
    except Exception as exc:
        hard(False, "site.webmanifest is valid JSON", str(exc))
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(raw.encode("utf-8"))
        vb = [float(v) for v in root.get("viewBox").split()]
        hard(abs(vb[2] - vb[3]) < 0.01, "favicon.svg viewBox is square", root.get("viewBox"))
        tags = {e.tag.split("}")[-1] for e in root.iter()}
        hard(not ({"text", "image", "foreignObject"} & tags), "favicon.svg has no <text>/<image>/<foreignObject>")
    except Exception as exc:
        hard(False, "favicon.svg parses", str(exc))
    snippet = kitlib.read(os.path.join(out, "head-snippet.html"))
    hard("rel=\"icon\"" in snippet.replace("'", '"'), "head snippet links the icons")

    # ---- maskable safe zone
    mk = Image.open(os.path.join(out, "maskable-512.png")).convert("RGBA")
    bgc = mk.getpixel((2, 2))
    px = mk.load()
    outside = 0
    cx = cy = 256
    for y in range(0, 512, 2):
        for x in range(0, 512, 2):
            if ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 > 0.4 * 512:
                p = px[x, y]
                if sum(abs(p[i] - bgc[i]) for i in range(3)) > 30:
                    outside += 1
    hard(outside == 0, "maskable artwork stays inside the 80% safe-zone circle", f"{outside} stray samples")

    # ---- pixel checks at tab size
    cov16, mean16, blobs16 = ink_stats(os.path.join(out, "favicon-16.png"))
    cov48, mean48, blobs48 = ink_stats(os.path.join(out, "favicon-48.png"))
    hard(cov16 > 0.02, "16 px favicon is not blank", f"{cov16 * 100:.0f}% covered")
    warn(0.08 <= cov16 <= 0.85, "16 px ink coverage between 8% and 85%", f"{cov16 * 100:.0f}%")
    warn(blobs16 >= blobs48 or blobs48 <= 1, "no parts merge at 16 px", f"{blobs16} blobs at 16 px vs {blobs48} at 48 px")
    for name, tab in (("light tab", LIGHT_TAB), ("dark tab", DARK_TAB)):
        c = kitlib.contrast(mean16, tab)
        warn(c >= 3.0, f"mark vs {name} contrast >= 3:1", f"{c:.2f}:1 (mean mark colour {mean16})")

    # ---- the visual test sheet
    pad = 18
    cell = 60 + 8 * 48 + 2 * pad
    cols = [("16 px", "favicon-16.png", 16), ("32 px", "favicon-32.png", 32), ("48 px", "favicon-48.png", 48)]
    W = cell * 3 + pad
    H = (8 * 48 + 2 * pad + 60) * 2 + 330
    sheet = Image.new("RGB", (W, H), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    f_small, f_big = font(15), font(20)
    d.text((pad, 10), f"Favicon test: {a.title}  (left of each pair: true size, right: enlarged 8x, nearest neighbour)", fill=(20, 20, 20), font=f_big)
    y = 50
    for label, tab in (("light tab", LIGHT_TAB), ("dark tab", DARK_TAB)):
        d.rectangle([0, y, W, y + 8 * 48 + 2 * pad + 40], fill=kitlib.rgb(tab))
        tcol = (20, 20, 20) if label == "light tab" else (235, 235, 235)
        d.text((pad, y + 6), label, fill=tcol, font=f_small)
        for i, (lab, f, s) in enumerate(cols):
            im = composite(os.path.join(out, f), tab)
            big = im.resize((s * 8, s * 8), Image.NEAREST)
            x0 = pad + i * cell
            sheet.paste(im.convert("RGB"), (x0, y + 30))
            sheet.paste(big.convert("RGB"), (x0 + 60, y + 30))
            d.text((x0, y + 30 + 8 * 48 + 6), lab, fill=tcol, font=f_small)
        y += 8 * 48 + 2 * pad + 60
    # apple touch + maskable with safe zone
    ty = y + 10
    apple = Image.open(os.path.join(out, "apple-touch-icon.png")).convert("RGB")
    sheet.paste(apple, (pad, ty))
    d.text((pad, ty + 186), "apple-touch 180", fill=(20, 20, 20), font=f_small)
    m2 = mk.resize((180, 180), Image.LANCZOS)
    mk_rgb = Image.new("RGB", (180, 180), (255, 255, 255))
    mk_rgb.paste(m2, mask=m2.split()[3])
    md = ImageDraw.Draw(mk_rgb)
    md.ellipse([90 - 72, 90 - 72, 90 + 72, 90 + 72], outline=(255, 0, 90), width=2)
    sheet.paste(mk_rgb, (pad + 220, ty))
    d.text((pad + 220, ty + 186), "maskable + 80% safe zone", fill=(20, 20, 20), font=f_small)
    i192 = Image.open(os.path.join(out, "icon-192.png")).convert("RGBA")
    ib = Image.new("RGB", (192, 192), (255, 255, 255))
    ib.paste(i192, mask=i192.split()[3])
    sheet.paste(ib, (pad + 440, ty))
    d.text((pad + 440, ty + 196), "icon-192", fill=(20, 20, 20), font=f_small)
    sheet.crop((0, 0, W, ty + 230)).save(os.path.join(out, "favicon-test.png"))

    report(results, out)
    raise SystemExit(1 if any(r[0] == "FAIL" for r in results) else 0)


def report(results, out):
    lines = ["# Favicon test report", ""]
    for lvl, name, detail in results:
        lines.append(f"- **{lvl}** {name}" + (f" — {detail}" if detail else ""))
    fails = sum(1 for r in results if r[0] == "FAIL")
    warns = sum(1 for r in results if r[0] == "WARN")
    lines += ["", f"{fails} failed, {warns} warnings. Warnings are heuristics (uncalibrated).",
              "Not covered: how a real browser tab renders it. After deploying, open the site in Chrome and Safari once "
              "and check the tab, the bookmark and (iOS) the home-screen icon."]
    text = "\n".join(lines)
    kitlib.write(os.path.join(out, "favicon-test-report.md"), text)
    print(text)


if __name__ == "__main__":
    main()
