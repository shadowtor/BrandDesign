#!/usr/bin/env python3
"""End-to-end smoke test of the skill's scripts (needs Python, a Chromium browser and internet for Google Fonts).

  python tools/smoke_test.py

Runs, in a temp folder: svg_audit, export_variants, palette build/audit/export, merch catalogue selection, and
build_kit on the Kiln example with the slow/optional stages skipped. Exits 1 on the first failure.
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "skills", "brand-studio", "scripts")
EX = os.path.join(ROOT, "examples", "kiln")
PY = sys.executable


def run(*args, ok=(0,)):
    r = subprocess.run([PY, *args], capture_output=True, text=True)
    status = "ok  " if r.returncode in ok else "FAIL"
    print(status, os.path.basename(args[0]), " ".join(a for a in args[1:3]))
    if r.returncode not in ok:
        print(r.stdout[-1500:], r.stderr[-1500:])
        sys.exit(1)
    return r.stdout


def main():
    with tempfile.TemporaryDirectory() as tmp:
        svg = os.path.join(tmp, "m.svg")
        open(svg, "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><title>t</title>'
                             '<path fill="#C2491D" fill-rule="evenodd" d="M128 16 A112 112 0 1 1 127.9 16 Z M128 80 A48 48 0 1 0 128.1 80 Z"/></svg>')
        run(os.path.join(S, "check_setup.py"), "--offline")
        run(os.path.join(S, "svg_audit.py"), svg)
        run(os.path.join(S, "export_variants.py"), svg, "--out-dir", os.path.join(tmp, "v"), "--only", "black", "white")
        pal = os.path.join(tmp, "p.json")
        run(os.path.join(S, "palette", "palette_build.py"), "#1f5f7a", "#ea8a28", "--name", "T", "-o", pal, "-q")
        run(os.path.join(S, "palette", "palette_audit.py"), pal)
        run(os.path.join(S, "palette", "export_tokens.py"), pal, "--out", os.path.join(tmp, "tok"))
        sys.path.insert(0, S)
        import merch_catalog as mc
        for b, want in (({"business_type": "coffee"}, "coffee-bag"), ({"industry": "esports"}, "jersey"), ({"industry": "illustrator"}, "sticker-sheet"),
                        ({"industry": "saas"}, "business-card"), ({"industry": "unknown-thing"}, "tee")):
            assert want in mc.items_for(b), (b, mc.items_for(b))
        print("ok   merch_catalog selection")
        out = os.path.join(tmp, "kit")
        run(os.path.join(S, "build_kit.py"), os.path.join(EX, "brand.json"), "--out", out,
            "--skip", "social", "stationery", "guidelines", "favicons", "tokens", "photo")
        assert os.path.exists(os.path.join(out, "logo", "svg", "kiln-horizontal-colour-light.svg"))
        assert os.path.exists(os.path.join(out, "logo", "pdf", "kiln-symbol-black.pdf"))
        assert json.load(open(os.path.join(out, "mockups", "manifest.json")))
        print("ok   build_kit outputs exist")
    print("smoke test passed")


if __name__ == "__main__":
    main()
