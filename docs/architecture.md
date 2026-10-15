# How brand-studio fits together

```
brief ──► research ──► 3 greyscale sketches ──► independent review ──► ⛔ user picks
                                                                          │
   final artwork (final/*.svg) + brand.json ◄── refine · colour · type · lockups
                    │
                    ▼
            build_kit.py ──► logo/ favicons/ social/ stationery/ mockups/ tokens/ guidelines/ README.md
                    │                                   ▲
                    └─ optional --photo-mockups ────────┘  (PSD from mockups-design.com → psd_mockup.py)
```

## Folders in `skills/brand-studio/`
| Path | What |
|---|---|
| `SKILL.md` | the instructions the agent loads: intake, research, checkpoint, kit, honesty rules |
| `references/` | design knowledge loaded on demand: process, principles, mark types, colour, type, testing, kit anatomy, review agent, merch catalogue, live sources, examples. Cards prefixed `bi-` are from brand-identity-skill |
| `scripts/` | the tools (all Python). Logo tooling from logo-design-skill; `palette/` from brand-identity-skill; the kit builders are new |
| `templates/` | `brand.example.json`, review brief, guideline and presentation templates |
| `assets/` | `logo-library/` (1,400 reference SVGs, study only), `palette-library/`, `examples/` (boards), `i18n/`, `ai-defaults.json` |
| `evals/` | prompts and expected behaviour for testing the skill |

## Scripts
| Script | Job |
|---|---|
| `outline_text.py` | set a Google Font (kerned) and write it as SVG paths + metrics |
| `compose_lockup.py` | symbol + wordmark → horizontal, vertical, square |
| `svg_audit.py`, `preview_sheet.py`, `concept_sheet.py` | check a mark; test sheet (16 px, one-colour, reversed, shelf); the checkpoint image |
| `review_pack.py` | assemble the brief + files for the independent review sub-agent |
| `palette/*` | build an OKLCH palette from seeds, audit WCAG contrast and colour-blind pairs, export CSS/SCSS/Tailwind/DTCG tokens |
| `build_kit.py` | orchestrates the stages below; each stage can fail without stopping the others |
| `favicon_test.py` | build + test favicon/app-icon set (ICO structure, sizes, manifest, maskable safe zone, 16 px pixel checks) |
| `collateral.py` | social avatars/banners, letterhead, header/footer, business card, email signature |
| `merch_catalog.py`, `merch.py`, `psd_mockup.py` | business type → items; illustrated scenes; optional photographic PSD mockups |
| `guidelines.py` | the brand guidelines PDF built from the real files |
| `live_sources.py` | Fontsource, TheColorAPI, Colormind, Iconify lookups |
| `kitlib.py` | shared: recolouring, batch Chrome rendering, PDF split, contrast maths |
| `check_setup.py` | verify Python, uv, a Chromium browser, network |

## Design decisions
- **Everything renders through a headless Chromium browser** so one engine produces PNG, JPG, PDF and screenshots on every OS.
  Many files are packed onto one sheet and cropped (Pillow), because launching a browser per file is slow.
- **No live `<text>` in finished logos**: wordmarks are outlined from real fonts; anything else risks font fallback on other machines.
- **Honest numbers**: CMYK is shown as screen-derived and indicative, Pantone is left blank, clear space/min size are flagged as
  starting values, tests state what they do not cover.
- **The checkpoint is a hard stop**: no colour or kit work before the user picks a sketch.
- **Third-party PSDs are cache-only**: downloaded on demand, never copied into a kit or the repository.
