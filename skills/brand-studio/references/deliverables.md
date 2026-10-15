# Deliverables spec

What a complete kit contains, how each file is made and tested. `scripts/build_kit.py brand.json --out deliver`
builds all of it from the approved artwork; stages can be run alone (`--skip`).

| Deliverable | Where it comes from | Test |
|---|---|---|
| Horizontal / vertical / square lockups, symbol, wordmark | designed during refinement; `compose_lockup.py` gives the rule-based first cut | `svg_audit.py` on each; renders at 512 and 64 px looked at |
| Colour-light, colour-dark, black, white, greyscale of each | `kitlib.variants_of` (greyscale by CIE lightness; dark version lifts parts that fail 3:1 on the dark ground, or use `dark_map`) | look at all five on their grounds (guidelines page 5); one-colour needs real holes, not white shapes |
| SVG, PNG (256/512/1024/2048, transparent), JPG (2000 px, on white or ink), PDF (vector) | build_kit stage `logos` | PNG sizes exist; PDFs open; JPG has no transparency halo |
| Favicons: svg, ico 16/32/48, png, apple-touch 180, 192/512, maskable, webmanifest, head snippet | `favicon_test.py` | script checks file structure, ICO contents, manifest, maskable safe zone, 16 px blob/coverage/contrast; sheet `favicon-test.png`; final word is a real browser |
| Social avatars + banners | `collateral.py` | circle-safe zone; content right of the avatar overlap; sizes re-checked against current platform docs |
| Letterhead A4 (sample + blank), header/footer bands, business card with bleed, email signature | `collateral.py` | sample text is labelled sample; check margins at 100% |
| Merchandise mockups (sector-relevant) | `merch.py` | the right logo version for each object colour; labelled as mockups |
| Photo mockups (optional `--photo-mockups`) | `psd_mockup.py`: mockups-design.com PSDs, smart object replaced, perspective + optional cylinder bend; item colour decides the logo version | compare with the mockup's JPG; apron/tee/mug verified, other PSDs may need `--scale`/`--cylinder` tuning or have a different layer layout (script lists layers and stops) |
| Brand guidelines PDF | `guidelines.py` | read every page: no invented claims, ratios present, misuse drawn from the real mark |
| Tokens (CSS/SCSS/Tailwind/DTCG) + fonts.md | `palette/palette_build.py` + `palette_audit.py` + `export_tokens.py` | audit has 0 gates; fix the palette, never export a failing one |

## Colour reproduction honesty
- HEX/RGB/HSL/OKLCH are exact for screen. CMYK shown in the kit is **screen-derived and indicative**; Pantone is
  **left blank** for a physical book; a printer supplies the real values for their paper/profile (`bi-reproduction.md`).
- Vivid primaries dull in CMYK; say so and suggest a spot colour if the brand colour must be vivid on paper.

## brand.json
See `templates/brand.example.json`. Paths are relative to the JSON file. Required: name, colors.primary/ink/paper,
logo.symbol or logo.horizontal. Everything else degrades gracefully (pages and files for missing inputs are skipped).
Put final artwork in `final/`; keep concept files in `concepts/` and review output in `review/`.

## Minimum sizes and clear space
Defaults in the guidelines are starting values flagged as such. Replace them with measured ones: render the symbol at
16/24/32 px (favicon test), find the size just above where the defining feature vanishes, record px and mm.

## brand.json logo keys added in use
`favicon_source` (small-size SVG, ideally with a backing disc so it reads on light and dark tabs) · `app_icon` `{bg, fg}` (`fg: "keep"` keeps the mark's own colours on the tile) · `dark_map` (hex swaps for the dark-ground version) · `symbol_small`.
The favicon test's tab-contrast warning uses the mean ink colour, so a light backing disc can trigger a false warning: read the sheet, not only the number.
