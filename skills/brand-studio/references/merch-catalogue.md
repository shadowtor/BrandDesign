# Merchandise: choose items the brand would really make

Merch mockups exist to judge the logo *in use*, so the items must be things this kind of business would plausibly produce, not a
generic mug-and-shirt set. `scripts/merch_catalog.py` holds the catalogue; `brand.json` selects from it.

## How items are chosen
1. Set `business_type` in brand.json (free word; aliases map it: `cafe`→coffee, `esports`→gaming, `illustrator`→artist,
   `fintech`→finance, `wishlist`→retail...). If absent, `industry` is used; unknown → `general`.
2. The business type gives an ordered list (first 6–8 used). Examples:
   - **coffee**: coffee bean bag, travel mug, takeaway cup, mug, apron, tote, tee, cap
   - **gaming**: team jersey, mouse mat, hoodie, tee, cap, sticker sheet, lanyard, keyring
   - **tech / saas**: business card, USB stick, charging cable, lanyard, phone case, laptop sleeve, tee, sticker sheet
   - **artist**: sticker sheet, business card, tee, tote, notebook, poster, pin badge
   - also fashion, fitness, finance, services, health, beauty, event, music, education, community, retail, trades, kids, pets, bakery, bar, food
3. **Override when the brand is unusual**: set `"merch": ["item", ...]` using keys from `merch_catalog.ITEMS`. Think about who the
   customer is and what they would actually hold, wear or have on their desk (a climbing gym: chalk bag is not in the catalogue,
   so pick the nearest: tote + bottle + tee, and say so). Do not pad the list: 6 good items beat 12 generic ones.

## Where each mockup comes from (in this order)
1. **Photographic** (`--photo-mockups`): the free PSD from mockups-design.com for that item (`ITEMS[...][1]` is the page slug),
   downloaded on demand into `~/.cache/brand-studio/mockups`, logo placed in the smart-object layer by `psd_mockup.py`.
2. **Illustration**: a flat vector scene drawn by `merch.py` for items with no PSD page (jersey, lanyard, phone case, cable,
   travel mug, sticker sheet...) or when the PSD cannot be filled cleanly.
3. Never invent an item that has neither: leave it out and say so.

`mockups/manifest.json` lists every real mockup file (`kind: photo | illustration`); the guidelines "In use" pages are built from it,
so the guideline PDF only ever shows files that exist in the kit and labels each one.

## Adding items or sources
- New item: add a row to `ITEMS` (label, mockups-design page slug or `None`, logo form, scale, cylinder degrees) and, if there is no
  PSD page, a scene function in `merch.py` (`SCENES`).
- New PSD: run `psd_mockup.py brand.json --psd file.psd --out out.png --item <key>`; check against the mockup's own JPG; tune `scale` /
  `cylinder` in the catalogue. PSD layouts vary: the script looks for a smart object named Design (or Your design / Logo), hides
  "delete this layer" slides, maps the artboard onto the smart object's transform quad and clips with its mask.
- Unblast (unblast.com) hosts many more mockups (lanyards, jerseys, phone cases, USB cards, tumblers, coffee packaging) but each is
  third-party with its own licence and a JavaScript download step: download by hand, read the licence on the page, then use `--psd`.

## Licences (preview use)
mockups-design.com: free for any purpose incl. commercial, no attribution required, but do not redistribute the PSD files; sharing a
flattened finished image is allowed. Keep PSDs in the cache folder, never in a deliverable or repository. Credit the site in any
public write-up (see the repository README).
