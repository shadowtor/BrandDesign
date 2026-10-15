# Contributing

Thanks for helping. The most useful contributions:

- **Merch items**: add a row to `ITEMS` in `skills/brand-studio/scripts/merch_catalog.py` (label, mockups-design.com page slug or `None`,
  logo form, scale, cylinder). If there is no free PSD, add an illustration function to `merch.py`. If a PSD needs placement tweaks,
  add an entry to `ADJUST` after comparing the result with the mockup's own preview image.
- **Business types**: extend `BUSINESS_TYPES` / `ALIASES` with what that kind of business really makes (not a generic mug and shirt).
- **Reference data**: sector palettes and logos you have the right to redistribute (see `references/library-guide.md`).
- **Evals**: prompts and expected behaviour in `skills/brand-studio/evals/`.
- **Bug reports**: include your OS, `python skills/brand-studio/scripts/check_setup.py` output and the failing command.

## Before opening a pull request
1. `python tools/smoke_test.py` passes (needs a Chromium browser and internet).
2. Any new script has a docstring with usage, runs with `--help`, and keeps working on Windows, macOS and Linux (no shell-specific code).
3. New third-party data or fonts: add them to `THIRD_PARTY_NOTICES.md` with their licence. Never commit PSD/PSB files, client work or
   anything you do not have the right to publish.
4. Keep claims honest: tests say what they do not cover; heuristics are labelled as heuristics.

By contributing you agree your work is released under the repository's MIT licence.
