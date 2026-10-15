# Third-party notices

## Code and guidance incorporated (MIT)
| Source | What was taken | Licence |
|---|---|---|
| [kaankiziltug/logo-design-skill](https://github.com/kaankiziltug/logo-design-skill) | design process and principles references, SVG tooling (`svg_audit`, `preview_sheet`, `concept_sheet`, `render_png`, `export_variants`, `presentation_board`, `search_library`, `svglib`), checkpoint workflow, 28 example concept boards | MIT, see `LICENSE-upstream-logo-design-skill` |
| [fatihaydost/brand-identity-skill](https://github.com/fatihaydost/brand-identity-skill) | palette tooling (`colorlib`, `palette_build`, `palette_audit`, `export_tokens`, `i18nlib`, `identitylib`, `presentlib`, `pal_catalog`, `search_palettes`), accessibility, AI-defaults, cohesion, type, reproduction, kit and critique cards (prefixed `bi-`), example boards | MIT, see `LICENSE-upstream-brand-identity-skill` and `THIRD_PARTY_NOTICES-brand-identity.md` |

## Reference data (study only, not covered by this repository's licence)
- `skills/brand-studio/assets/logo-library/` — 1,400+ real-world SVG logos. They are trademarks of their owners, included for
  study and classification only. See `TRADEMARKS-logo-library.md`. Never copy, trace or ship them for a client.
- `skills/brand-studio/assets/palette-library/` — measured public-site colours of real brands. Names and colours belong to their
  owners. See `TRADEMARKS-palette-library.md`.
- `skills/brand-studio/assets/examples/` — concept boards from the two upstream projects, showing fictional brands.

If you are a rights holder and want an item removed from the reference libraries, open an issue.

## Fonts
Fonts are never bundled. Scripts fetch Google Fonts families (SIL OFL 1.1 or Apache 2.0) on demand, cache them locally and outline
them into logos, which the OFL permits. Families used in the examples: Young Serif, Hanken Grotesk, Chakra Petch, Barlow,
Instrument Serif, Instrument Sans (all OFL). Check a family's licence before using it commercially.

## Photographic mockups
Optional. PSD files are downloaded on demand from mockups-design.com into a local cache and are never part of this repository or of
any kit. Only the rendered preview images in `examples/` are published, under the site's licence (finished flattened images may
be shared; PSDs must not be redistributed). See the README credits for the mockups used.

## Services queried at run time (no keys, no data sent beyond the query)
Google Fonts CSS API, Fontsource API, TheColorAPI, Colormind, Iconify. Each is subject to its own terms.
