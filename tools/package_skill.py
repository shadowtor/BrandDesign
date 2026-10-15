#!/usr/bin/env python3
"""Package the skill as zip files (e.g. claude.ai -> Settings -> Capabilities -> Skills, or a release asset).

  python tools/package_skill.py     # dist/brand-studio.zip (full) + dist/brand-studio-lite.zip

The lite package leaves out the 1,400+ reference SVG files and gallery.html (catalogue metadata, all scripts and all
references are kept) for platforms with upload size limits.
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "brand-studio")
DIST = os.path.join(ROOT, "dist")
SKIP = {"__pycache__", ".DS_Store"}


def build(name, lite):
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, name)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(SKILL):
            dirnames[:] = [d for d in dirnames if d not in SKIP]
            rel = os.path.relpath(dirpath, SKILL).replace(os.sep, "/")
            if lite and (rel.startswith("assets/logo-library/svg") or rel.startswith("assets/examples")):
                continue
            for fn in filenames:
                if fn in SKIP or fn.endswith(".pyc") or (lite and fn == "gallery.html"):
                    continue
                full = os.path.join(dirpath, fn)
                z.write(full, os.path.join("brand-studio", os.path.relpath(full, SKILL)))
    print(f"{out}  {os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    build("brand-studio.zip", lite=False)
    build("brand-studio-lite.zip", lite=True)
