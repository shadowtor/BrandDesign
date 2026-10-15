# Notes on the source cards

Cards prefixed `bi-` are copied unchanged from brand-identity-skill (MIT). They mention its `brand.py` pipeline
(`init`, `logos`, `build`, `kit`, `mix`, `critique`, `site ...`, `fonts ...`) and `sets.json`/`identity.json`. That pipeline is NOT
bundled here (it needs fonttools/harfbuzz/skia and a site engine); this skill uses the same ideas with lighter tools:

| brand-identity step | here |
|---|---|
| `fonts search/audit` | `scripts/live_sources.py fonts`, `outline_text.py`, licence rules in `bi-type.md` |
| `logos` contact sheet, `logo_audit` | `concept_sheet.py`, `svg_audit.py`, `preview_sheet.py` |
| palette build/audit/tokens | `scripts/palette/*` (bundled, identical code) |
| `kit` | `scripts/build_kit.py` (+ guidelines, favicons, social, stationery, mockups) |
| `site extract/apply` | open the site in the browser pane and read colours/fonts by hand; mock pages not bundled |
| `mix` | do it by hand: take one set's mark and another's palette, re-colour, re-run the palette audit |
| `critique` | follow `bi-critique.md` + `critique.md`; run `palette_audit.py` and `svg_audit.py` |

Conflict resolved: logo-design says specify CMYK + Pantone; brand-identity says never invent them. This skill shows
screen-derived CMYK labelled indicative and leaves Pantone blank. The sources are MIT (see LICENSE-* files); logo and
palette library data are trademarks of their owners (TRADEMARKS-*.md, THIRD_PARTY_NOTICES.md): study only.
