# Installing brand-studio (instructions for an AI agent)

You are an AI coding agent (Claude Code, Codex CLI, Gemini CLI, Cursor, Copilot or similar). A user asked you to install the
**brand-studio** skill. Follow these steps in order. Do not skip the checks, and report what you actually saw.

## 0. Facts about this skill

- It is an *Agent Skill*: a folder named `brand-studio` containing `SKILL.md` plus `scripts/`, `references/`, `templates/`, `assets/`.
- It needs **Python 3.9+**, a **Chromium-based browser** (Chrome, Edge, Brave or Chromium) and, for fonts and optional photographic
  mockups, **internet access**. [`uv`](https://docs.astral.sh/uv/) is recommended: the skill's scripts use it to install Pillow, pypdf,
  fonttools, uharfbuzz and psd-tools on first use. Nothing else is installed and nothing runs at install time.
- Installing = copying (or symlinking) `skills/brand-studio` to the right skills folder. Do not modify files inside it.

## 1. Get the repository

```bash
git clone https://github.com/shadowtor/BrandDesign.git
cd BrandDesign
```

If the user already has a clone, run `git pull` instead. If `git` is not available, download the repository ZIP from GitHub and extract it.

## 2. Install into the right place

Pick the target for the agent the user is running (ask only if you cannot tell). The installer script does the copy safely and replaces
an older `brand-studio` folder in the target only:

| Agent | Command | Installed to |
|---|---|---|
| Claude Code | `python tools/install.py --claude` | `~/.claude/skills/brand-studio` |
| Codex CLI | `python tools/install.py --codex` | `~/.codex/skills/brand-studio` |
| Gemini CLI | `python tools/install.py --gemini` | `~/.gemini/skills/brand-studio` |
| One project only | `python tools/install.py --project` | `./.claude/skills/brand-studio` |
| Other agent | `python tools/install.py --dest <that agent's skills folder>` | `<folder>/brand-studio` |

Use `python3` instead of `python` on macOS/Linux when `python` is missing; on Windows use `python` or `py -3`.
Add `--link` to symlink instead of copy (useful if the user will edit the repository).

**Claude Code plugin alternative** (no clone needed): tell the user to run
`/plugin marketplace add shadowtor/BrandDesign` and then `/plugin install brand-studio@brand-studio`.
You cannot run slash commands yourself; give them these two lines.

## 3. Verify

```bash
python skills/brand-studio/scripts/check_setup.py
```

Expected: `PASS` for Python and a Chromium browser; `PASS` or `WARN` for uv and network. A `FAIL` means the skill cannot work:
fix it first (the line includes the fix). `INFO` lines for Pillow/pypdf/fonttools are normal: they are installed on demand.
If `uv` is missing, offer to install it (command is in the `WARN` line) or run
`pip install pillow pypdf fonttools uharfbuzz pymupdf` (plus `"psd-tools[composite]" numpy scipy scikit-image` for `--photo-mockups`) for the same effect.

Optional deeper check (needs internet, ~2 minutes): `python tools/smoke_test.py`.

## 4. Tell the user it is installed

Say: where it was installed, the result of `check_setup.py`, and that they must **start a new agent session** so the skill is picked up.
Then suggest a first request, for example:

> Design a brand identity for *<name>*, a *<what they do>* for *<audience>*. It should feel *<three adjectives>*. Show me three logo sketches first.

The skill will ask a few questions, research the category, show three greyscale sketches reviewed by an independent sub-agent and
**stop for the user's pick** before building the full kit.

## 5. Rules while installing

- Never run scripts from the skill other than `check_setup.py` during installation.
- Never commit, push or publish anything on the user's behalf.
- Never download files other than the repository itself. (Photographic mockups are downloaded later, on demand, by the skill, and only
  when the user asks for them; see the README credits.)
- If a step fails, show the exact error and stop; do not improvise a different install location without asking.

## 6. Uninstall

`python tools/install.py --uninstall --claude` (or `--codex`, `--gemini`, `--project`). The cache of downloaded mockup PSDs lives in
`~/.cache/brand-studio` and can be deleted at any time.
