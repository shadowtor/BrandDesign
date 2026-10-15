#!/usr/bin/env python3
"""Install (or update / remove) the brand-studio skill for Claude Code, Codex CLI, Gemini CLI or any folder.

  python tools/install.py                 # Claude Code + Codex, copy mode (default)
  python tools/install.py --claude        # only ~/.claude/skills/brand-studio
  python tools/install.py --codex         # only ~/.codex/skills/brand-studio
  python tools/install.py --gemini        # only ~/.gemini/skills/brand-studio
  python tools/install.py --dest DIR      # DIR/brand-studio (any agent that reads Agent Skills folders)
  python tools/install.py --project       # ./.claude/skills/brand-studio in the current project
  python tools/install.py --link          # symlink instead of copy (live-edit while developing; may need admin on Windows)
  python tools/install.py --uninstall     # remove the chosen targets
  python tools/install.py --check         # run the setup check afterwards

Installing replaces an existing brand-studio folder in the target (it asks nothing: the target is this skill only).
No network access, no packages are installed here; the skill's scripts install Pillow/pypdf/fonttools through uv on first use.
"""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "skills", "brand-studio")
NAME = "brand-studio"


def targets(a):
    home = os.path.expanduser("~")
    t = []
    if a.dest:
        t.append(os.path.join(os.path.abspath(a.dest), NAME))
    if a.project:
        t.append(os.path.join(os.getcwd(), ".claude", "skills", NAME))
    if a.claude or not (a.codex or a.gemini or a.dest or a.project):
        t.append(os.path.join(home, ".claude", "skills", NAME))
    if a.codex or not (a.claude or a.gemini or a.dest or a.project):
        t.append(os.path.join(home, ".codex", "skills", NAME))
    if a.gemini:
        t.append(os.path.join(home, ".gemini", "skills", NAME))
    return t


def remove(path):
    if os.path.islink(path):
        os.unlink(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claude", action="store_true")
    ap.add_argument("--codex", action="store_true")
    ap.add_argument("--gemini", action="store_true")
    ap.add_argument("--project", action="store_true")
    ap.add_argument("--dest")
    ap.add_argument("--link", action="store_true")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(os.path.join(SRC, "SKILL.md")):
        sys.exit(f"error: {SRC} has no SKILL.md; run this from a full clone of the repository")
    for t in targets(a):
        if a.uninstall:
            remove(t)
            print("removed", t)
            continue
        os.makedirs(os.path.dirname(t), exist_ok=True)
        remove(t)
        if a.link:
            os.symlink(SRC, t, target_is_directory=True)
            print("linked ", t, "->", SRC)
        else:
            shutil.copytree(SRC, t, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            print("copied ", t)
    if a.check and not a.uninstall:
        subprocess.call([sys.executable, os.path.join(SRC, "scripts", "check_setup.py")])
    elif not a.uninstall:
        print("\nNext: python skills/brand-studio/scripts/check_setup.py   (verifies Python, uv, a Chromium browser, network)")
        print("Then start a new agent session and ask for a logo or brand identity.")


if __name__ == "__main__":
    main()
