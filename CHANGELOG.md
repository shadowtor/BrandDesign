# Changelog

## 1.0.0

First release. Merges and extends two MIT skills (kaankiziltug/logo-design-skill, fatihaydost/brand-identity-skill).

- Workflow: intake → category research → three greyscale sketches → independent sub-agent review → STOP for the user's pick → refine,
  colour, type, lockups → full kit → kit review.
- `build_kit.py`: logos (square, horizontal, vertical, symbol, wordmark × colour-light, colour-dark, black, white, greyscale × SVG, PNG,
  JPG, PDF), tested favicon/app-icon set, social avatars and banners, letterhead/header/footer, business card with bleed, email
  signature, design tokens, brand guidelines PDF.
- Merch catalogue by business type (coffee, gaming, tech, artist, retail, …) with photographic mockups from free PSDs
  (`--photo-mockups`, downloaded on demand) and clearly labelled illustrations where no PSD exists.
- Live sources: Fontsource, TheColorAPI, Colormind, Iconify; bundled 1,400-logo and palette reference libraries.
- Installer (`tools/install.py`), setup check (`scripts/check_setup.py`), agent install guide, smoke test and CI.
- Three fictional example brands: Kiln (coffee), Rookery (gaming), Marigold Press (illustrator).
