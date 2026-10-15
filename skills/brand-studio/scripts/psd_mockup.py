#!/usr/bin/env python3
"""OPTIONAL: put the brand's logo into a real photographic PSD mockup (smart-object 'Design' layer) without Photoshop.

For private PREVIEWS of how the logo looks on an item (not for publication). The user approved on-demand downloads from
mockups-design.com (licence: free incl. commercial, no attribution, do not redistribute the PSD files). Files are cached in
~/.cache/brand-studio/mockups and never copied into the skill or the deliverables; only the rendered preview PNG is kept.

  python3 scripts/psd_mockup.py brand.json --page https://mockups-design.com/round-bellied-mug-mockup/ --out deliver/mockups/mug-photo.png
  python3 scripts/psd_mockup.py brand.json --psd local.psd --out out.png [--variant 1] [--cylinder 70] [--scale 0.55]
  python3 scripts/psd_mockup.py --list-presets

How it works: find the smart-object layer named Design inside the mockup group, build a transparent artboard of the
smart object's size with the logo centred (colour version chosen for contrast against the item colour), place it in the
object's transform box, optionally bend it round a cylinder (mugs/bottles), clip it to the original layer's silhouette,
insert it as a pixel layer at the same stack position, and composite the PSD (shadows, colour, highlights stay).
Limits: Photoshop's custom warp meshes are approximated (flat or cylinder); a few adjustment layers may not render
exactly like Photoshop - always look at the result next to the mockup's own JPG preview. Not every PSD has the same layer
structure: if no Design smart object is found the script lists the layers and stops.
Optional: --catalog-search "mug" lists page links from mockups-design.com categories (needs network).
"""
import argparse
import io
import math
import os
import re
import shutil
import sys
import tempfile
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib  # noqa: E402

CACHE = os.path.join(os.path.expanduser("~"), ".cache", "brand-studio", "mockups")
UA = "Mozilla/5.0 (brand-studio preview helper)"
import merch_catalog  # noqa: E402

PRESETS = {"default": {"cylinder": 0, "scale": 0.6}}  # per-item values live in merch_catalog.ITEMS


def http(url, referer=None, jar=None):
    import http.cookiejar
    jar = jar if jar is not None else http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(url, headers={"User-Agent": UA, **({"Referer": referer} if referer else {})})
    return op.open(req, timeout=300), jar


def fetch_mockup(page_url):
    """mockups-design.com page URL -> folder with the extracted PSD(s) (cached). Uses the site's own free download flow."""
    if "mockups-design.com" not in page_url:
        raise SystemExit("error: automatic download is implemented for mockups-design.com pages; give a local file with --psd for other sites")
    slug = re.sub(r"[^a-z0-9]+", "-", page_url.rstrip("/").split("/")[-1].lower())
    dest = os.path.join(CACHE, slug)
    if os.path.isdir(dest) and any(f.lower().endswith(".psd") for _, _, fs in os.walk(dest) for f in fs):
        return dest
    os.makedirs(CACHE, exist_ok=True)
    r, jar = http(page_url)
    page = r.read().decode("utf-8", "replace")
    m = re.search(r'href="(https://mockups-design\.com/download/\d+/[^"]*)"', page)
    if not m:
        raise SystemExit("error: no download link on the page (the site layout may have changed)")
    dl = m.group(1).replace("&#038;", "&").replace("&amp;", "&")
    r, jar = http(dl, page_url, jar)
    html = r.read().decode("utf-8", "replace")
    n = re.search(r'href="(https://mockups-design\.com/download/\d+/\?[^"]*dlm-dp-dl-nonce=[^"]+)"', html)
    if not n:
        raise SystemExit("error: download step 2 link not found")
    url = n.group(1).replace("&#038;", "&").replace("&amp;", "&")
    r, jar = http(url, dl, jar)
    data = r.read()
    if data[:2] != b"PK":
        raise SystemExit("error: the site did not return a zip file")
    tmp = dest + ".zip"
    open(tmp, "wb").write(data)
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(tmp) as z:  # untrusted archive: refuse path traversal
        for i in z.infolist():
            target = os.path.normpath(os.path.join(dest, i.filename))
            if not target.startswith(os.path.abspath(dest)):
                raise SystemExit("error: unsafe path in archive")
        z.extractall(dest)
    os.remove(tmp)
    return dest


def find_psds(folder):
    return sorted(os.path.join(d, f) for d, _, fs in os.walk(folder) for f in fs if f.lower().endswith(".psd"))


DESIGN_NAMES = re.compile(r"design|project|logo|artwork|print|mouse ?pad|your|label|cover|front|place", re.I)
# whole words only: "lace" (shoe-lace layers) must not match inside "Place your design here"
SKIP_NAMES = re.compile(r"\b(laces?|colou?rs?|shadows?|backgrounds?|highlights?|textures?|masks?|base|delete)\b", re.I)


def find_design_layers(psd):
    """Every visible smart object that carries the printed design (a cup PSD has one per cup; a desk scene may also have a laptop screen).
    A layer whose name says design/logo/artwork wins over the skip list."""
    strong = re.compile(r"design|logo|artwork|project|mouse ?pad|your", re.I)
    cand = [l for l in psd.descendants() if l.kind == "smartobject" and l.visible and (strong.search(l.name) or not SKIP_NAMES.search(l.name))]
    named = [l for l in cand if DESIGN_NAMES.search(l.name)]
    return named or cand[:1]


def cylinder_map(img, deg):
    """Wrap a flat RGBA image around a vertical cylinder seen over +-deg (horizontal compression toward the edges)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img)
    h, w = a.shape[:2]
    tm = math.radians(deg)
    t = (np.arange(w) + 0.5) / w
    theta = (t - 0.5) * 2 * tm
    u = 0.5 + np.sin(theta) / (2 * math.sin(tm))
    src = np.clip((u * w).astype(int), 0, w - 1)
    return Image.fromarray(a[:, src, :])


def build(brand, psd_path, out, variant=None, cylinder=None, scale=None, preset=None, show_ref=True, form=None):
    from PIL import Image, ImageChops
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer
    import numpy as np
    import render_png

    psd = PSDImage.open(psd_path)
    for l in psd.descendants():  # optimisation slides the authors ask you to delete
        if re.search(r"delete|read me|instruction", l.name, re.I) and l.kind in ("pixel", "type", "smartobject"):
            l.visible = False
    layers = find_design_layers(psd)
    if not layers:
        print("No smart-object design layer found. Layers:")
        for l in psd.descendants():
            print(f"  {l.kind:12} {l.name!r} visible={l.visible}")
        raise SystemExit(2)
    sp = merch_catalog.spec(preset) if preset in merch_catalog.ITEMS else {"cylinder": 0, "scale": 0.6, "form": None, "dx": 0.0, "dy": 0.0}
    form = form or sp["form"]
    cyl = sp["cylinder"] if cylinder is None else cylinder
    sc = sp["scale"] if scale is None else scale

    for l in layers:
        l.visible = False
    base = psd.composite(force=True).convert("RGB")   # the item without any design: used to pick the logo version

    vs = None
    for form_ in ([form] if form else []) + ["horizontal", "vertical", "symbol"]:
        pth = kitlib.logo_path(brand, form_)
        if pth and os.path.exists(pth):
            vs = kitlib.variants_of(kitlib.tight_viewbox(kitlib.read(pth)), {**brand["logo"], **brand["colors"]})
            break
    if vs is None:
        raise SystemExit("error: no logo files in brand.json")

    notes = []
    for layer in layers:
        so = layer.smart_object
        tb = so.transform_box
        bounds = so.warp.get(b"bounds", {})
        xs, ys = tb[0::2], tb[1::2]
        sw = int(bounds.get(b"Rght", max(xs) - min(xs)))
        sh = int(bounds.get(b"Btom", max(ys) - min(ys)))
        x0, y0, x1, y1 = (max(0, layer.bbox[0]), max(0, layer.bbox[1]), min(psd.size[0], layer.bbox[2]), min(psd.size[1], layer.bbox[3]))
        if x1 - x0 < 4 or y1 - y0 < 4:
            x0, y0, x1, y1 = 0, 0, psd.size[0], psd.size[1]
        reg = base.crop((x0, y0, x1, y1)).resize((24, 24))
        arr = np.asarray(reg).reshape(-1, 3)
        px = arr[np.argsort(arr.sum(axis=1))]   # median of the area: shadows and creases do not decide the logo colour
        r, g, b = (int(v) for v in px[len(px) // 2])
        ground = kitlib.to_hex(r, g, b)
        raw, vname = kitlib.pick_variant(vs, ground)
        g_ = kitlib.geometry(raw)
        # the smart object is stretched into a box of another shape than its own canvas: pre-compensate so the logo keeps
        # its proportions on the item (size measured in the box, converted back to canvas units)
        qd = lambda i, j: math.hypot(tb[2 * j] - tb[2 * i], tb[2 * j + 1] - tb[2 * i + 1])
        bwq, bhq = max(1.0, (qd(0, 1) + qd(3, 2)) / 2), max(1.0, (qd(0, 3) + qd(1, 2)) / 2)
        fx, fy = sw / bwq, sh / bhq
        wd = sc * bwq
        hd = wd * g_["h"] / g_["w"]
        if hd > bhq * 0.7:
            hd = bhq * 0.7
            wd = hd * g_["w"] / g_["h"]
        lw, lh = max(2, int(wd * fx)), max(2, int(hd * fy))
        with tempfile.TemporaryDirectory() as tmp:
            svgp = os.path.join(tmp, "l.svg")
            open(svgp, "w", encoding="utf-8").write(kitlib.fit_attrs(raw))
            lp = os.path.join(tmp, "l.png")
            render_png.render(svgp, lp, lw, max(2, int(lw * g_["h"] / g_["w"])))
            logo = Image.open(lp).convert("RGBA").resize((lw, lh), Image.LANCZOS)  # deliberate stretch (see above)
        art = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        art.alpha_composite(logo, (int((sw - lw) / 2 + sp["dx"] * sw), int((sh - lh) / 2 + sp["dy"] * sh)))
        if cyl:
            art = cylinder_map(art, cyl)
        q = [(tb[0], tb[1]), (tb[2], tb[3]), (tb[4], tb[5]), (tb[6], tb[7])]
        src = [(0, 0), (sw, 0), (sw, sh), (0, sh)]
        A, B = [], []
        for (x, y), (u, v) in zip(q, src):
            A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
            A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
        coef = np.linalg.solve(np.array(A, float), np.array(B, float))
        canvas = art.transform(psd.size, Image.PERSPECTIVE, coef.tolist(), Image.BICUBIC)
        try:  # clip with the smart object's own mask when it has one (not its placeholder pixels, which can be sparse)
            if layer.has_mask():
                m_ = layer.mask.topil()
                full = Image.new("L", psd.size, 0)
                full.paste(m_, (layer.mask.left, layer.mask.top))
                canvas.putalpha(ImageChops.multiply(canvas.split()[3], full))
        except Exception:
            pass
        parent = layer.parent
        idx = list(parent).index(layer)
        newl = PixelLayer.frompil(canvas, psd, name="Brand design", top=0, left=0)
        parent.insert(idx + 1, newl) if hasattr(parent, "insert") else parent.append(newl)
        notes.append(f"{layer.name}: {vname} on {ground}")
    result = psd.composite(force=True).convert("RGB")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    result.save(out)
    return out, "; ".join(notes) + f"; cylinder {cyl} deg, width {sc:.2f}"


def build_set(brand, out_dir, items=None):
    """Photo mockups for the brand's merch items that have a mockups-design.com page. Returns [(item, path or reason)]."""
    done = []
    for it in (items or merch_catalog.items_for(brand)):
        sp = merch_catalog.spec(it) if it in merch_catalog.ITEMS else None
        if not sp or not sp["page"]:
            done.append((it, "no photo mockup page: illustration used"))
            continue
        try:
            folder = fetch_mockup(sp["page"])
            psds = find_psds(folder)
            if not psds:
                raise RuntimeError("no PSD in the download")
            out = os.path.join(out_dir, f"{brand['slug']}-photo-{it}.png")
            build(brand, psds[0], out, preset=it)
            done.append((it, out))
        except SystemExit as exc:
            done.append((it, f"skipped: {exc}"))
        except Exception as exc:
            done.append((it, f"failed: {exc}"))
    return done


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brand_json", nargs="?")
    ap.add_argument("--page", help="mockups-design.com mockup page (downloads on demand, cached)")
    ap.add_argument("--psd", help="local PSD file (any source you are licensed to use)")
    ap.add_argument("--variant", type=int, default=1, help="which PSD in a multi-file mockup (1-based)")
    ap.add_argument("--out")
    ap.add_argument("--item", help="merch_catalog item key (tee, mug, hoodie...): page and preset come from the catalogue")
    ap.add_argument("--cylinder", type=float, help="degrees of visible arc (0 = flat)")
    ap.add_argument("--scale", type=float, help="logo width as a fraction of the design area")
    ap.add_argument("--list-presets", action="store_true")
    ap.add_argument("--set", action="store_true", help="build every sector merch item that has a known page into --out (a folder)")
    a = ap.parse_args()
    if a.list_presets:
        for k in merch_catalog.ITEMS:
            print(k, merch_catalog.spec(k))
        return
    if a.item and not a.page and not a.psd:
        a.page = merch_catalog.page_url(a.item)
    if a.set:
        kitlib.ensure_deps({"psd_tools": "psd-tools[composite]", "numpy": "numpy", "scipy": "scipy", "skimage": "scikit-image"})
        for it, r in build_set(kitlib.load_brand(a.brand_json), a.out):
            print(it, r)
        return
    if not (a.brand_json and a.out and (a.page or a.psd)):
        ap.error("need brand.json, --out and --page or --psd")
    kitlib.ensure_deps({"psd_tools": "psd-tools[composite]", "numpy": "numpy", "scipy": "scipy", "skimage": "scikit-image"})
    brand = kitlib.load_brand(a.brand_json)
    if a.psd:
        path = a.psd
    else:
        folder = fetch_mockup(a.page)
        psds = find_psds(folder)
        if not psds:
            raise SystemExit("error: no PSD in the download")
        path = psds[min(a.variant, len(psds)) - 1]
    preset = a.item or next((k for k, v in merch_catalog.ITEMS.items() if v[1] and a.page and v[1] in a.page), None)
    out, note = build(brand, path, a.out, a.variant, a.cylinder, a.scale, preset)
    print("wrote", out, "-", note)
    print("Preview only. Compare with the mockup's own JPG; PSD files stay in", CACHE, "(do not redistribute).")


if __name__ == "__main__":
    main()
