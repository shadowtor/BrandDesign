#!/usr/bin/env python3
"""Check that this machine can run brand-studio: Python, uv, a Chromium-based browser, optional packages, network.

  python scripts/check_setup.py          # prints PASS / WARN / FAIL lines; exit code 1 only on a FAIL
  python scripts/check_setup.py --offline

FAIL = the skill cannot work. WARN = a feature is limited (the line says which and how to fix it).
"""
import argparse
import importlib.util
import os
import shutil
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def line(level, msg, fix=""):
    print(f"{level:<5} {msg}" + (f"\n      fix: {fix}" if fix and level != "PASS" else ""))
    return level == "FAIL"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    bad = False
    v = sys.version_info
    bad |= line("PASS" if v >= (3, 9) else "FAIL", f"Python {v.major}.{v.minor}.{v.micro}", "install Python 3.9 or newer")
    uv = shutil.which("uv")
    line("PASS" if uv else "WARN", "uv " + ("found" if uv else "not found (needed to auto-install Pillow, pypdf, fonttools, psd-tools)"),
         "" if uv else "Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"   macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh   (or pip install pillow pypdf fonttools uharfbuzz)")
    try:
        import render_png
        chrome = render_png.find_chrome()
    except Exception:
        chrome = None
    bad |= line("PASS" if chrome else "FAIL", "Chromium-based browser " + (chrome if chrome else "not found (renders every PNG/PDF)"),
                "" if chrome else "install Chrome, Edge, Brave or Chromium")
    for mod, pkg, why in (("PIL", "pillow", "PNG/JPG output"), ("pypdf", "pypdf", "PDF output"), ("fontTools", "fonttools", "wordmark outlining"),
                          ("uharfbuzz", "uharfbuzz", "wordmark kerning"), ("psd_tools", "psd-tools[composite]", "optional photographic mockups"),
                          ("fitz", "pymupdf", "guideline page PNGs")):
        have = importlib.util.find_spec(mod) is not None or (mod == "fitz" and importlib.util.find_spec("pymupdf") is not None)
        line("PASS" if have else "INFO", f"{pkg} {'installed' if have else 'not installed (' + why + '; installed on demand through uv)'}")
    if not a.offline:
        for name, url in (("Google Fonts", "https://fonts.googleapis.com/css2?family=Figtree"), ("Fontsource API", "https://api.fontsource.org/v1/fonts/figtree"),
                          ("mockups-design.com (optional photo mockups)", "https://mockups-design.com/")):
            try:
                urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8"}), timeout=15).read(100)
                line("PASS", f"network: {name}")
            except Exception as exc:
                line("WARN", f"network: {name} unreachable ({exc})", "outlining fonts and photo mockups need internet; the rest works offline")
    print("\n" + ("Setup has a blocking problem." if bad else "Ready."))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
