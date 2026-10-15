"""Merchandise catalogue: which items suit which kind of business, and where each item's mockup comes from.

Two layers:
  BUSINESS_TYPES  what a brand of that kind would really make (ordered by relevance; first 6-8 are used)
  ITEMS           each item: label, the mockups-design.com page whose free PSD is used for a PHOTOGRAPHIC preview (or None),
                  which logo form suits it, preset (scale / cylinder bend), and whether a flat illustration exists (merch.py)

The agent should still THINK: set brand.json "business_type" (any word; aliases below) or give an explicit "merch" list of
ITEMS keys when the brand is unusual (a gaming community, a bakery that sells aprons, a law firm that gives away umbrellas
is NOT in the catalogue: pick the nearest items and say so). Preview only; see references/merch-catalogue.md.
"""

MD = "https://mockups-design.com/"

# key: label, page slug on mockups-design.com (None = no photo mockup, use illustration), logo form, scale, cylinder degrees
ITEMS = {
    "tee": ("T-shirt", "mens-t-shirt-mockup", "horizontal", 0.5, 0),
    "hoodie": ("Hoodie", "free-hoodie-mockup", "horizontal", 0.45, 0),
    "sweatshirt": ("Sweatshirt", "mens-sweatshirt-mockup", "horizontal", 0.5, 0),
    "polo": ("Polo shirt", "polo-shirt-mockup", "symbol", 0.35, 0),
    "jersey": ("Team jersey", None, "horizontal", 0.5, 0),
    "cap": ("Cap", "free-baseball-cap-mockup", "symbol", 0.5, 0),
    "bucket-hat": ("Bucket hat", "bucket-hat-mockup", "symbol", 0.5, 0),
    "mug": ("Mug", "round-bellied-mug-mockup", "horizontal", 0.55, 40),
    "enamel-mug": ("Enamel mug", "free-enamel-mug-mockup", "horizontal", 0.5, 40),
    "coffee-cup": ("Takeaway coffee cup", "paper-coffee-cup-mockup", "symbol", 0.5, 35),
    "travel-mug": ("Travel mug", None, "vertical", 0.5, 0),
    "bottle": ("Water bottle", "free-sport-water-bottle-mockup", "symbol", 0.5, 30),
    "coffee-bag": ("Coffee bean bag", "free-food-pouch-mockup", "vertical", 0.6, 0),
    "paper-bag": ("Paper bag", "free-paper-bag-mockup", "vertical", 0.55, 0),
    "tote": ("Tote bag", "hanging-tote-bag-mockup", "vertical", 0.55, 0),
    "apron": ("Apron", "stitched-bib-apron-mockup", "horizontal", 0.5, 0),
    "mousemat": ("Mouse mat", "oversized-mouse-pad-mockup", "horizontal", 0.4, 0),
    "usb": ("USB stick", "free-pendrive-mockup", "symbol", 0.6, 0),
    "keychain": ("Keyring", "free-square-keychain-mockup", "symbol", 0.6, 0),
    "lanyard": ("Lanyard and ID badge", None, "horizontal", 0.6, 0),
    "phone-case": ("Phone case", None, "symbol", 0.5, 0),
    "laptop-sleeve": ("Laptop sleeve", None, "horizontal", 0.5, 0),
    "cable": ("Charging cable", None, "symbol", 0.5, 0),
    "business-card": ("Business card", "free-business-card-mockup", "horizontal", 0.5, 0),
    "notebook": ("Notebook", "free-spiral-notebook-mockup", "symbol", 0.45, 0),
    "sticker": ("Round sticker", None, "symbol", 0.6, 0),
    "sticker-sheet": ("Sticker sheet", None, "symbol", 0.6, 0),
    "pin-button": ("Pin badge", "free-pin-button-mockup", "symbol", 0.7, 0),
    "poster": ("Poster", "free-posters-mockup", "vertical", 0.5, 0),
    "signboard": ("Shop signboard", "vintage-wall-signboard-mockup", "horizontal", 0.6, 0),
    "box": ("Product box", "free-box-mockup-80x80x80-mm", "symbol", 0.5, 0),
    "label": ("Label tag", "simple-label-tag-mockup", "symbol", 0.5, 0),
    "calendar": ("Desk calendar", "free-desk-calendar-mockup", "horizontal", 0.5, 0),
    "coaster": ("Coaster", "free-round-coaster-mockup", "symbol", 0.6, 0),
}

BUSINESS_TYPES = {
    "coffee": ["coffee-bag", "travel-mug", "coffee-cup", "mug", "apron", "tote", "tee", "cap"],
    "food": ["apron", "paper-bag", "coffee-cup", "box", "tote", "label", "tee", "cap"],
    "bakery": ["paper-bag", "apron", "box", "label", "tote", "coffee-cup", "tee"],
    "bar": ["coaster", "apron", "tee", "cap", "tote", "bottle", "poster"],
    "gaming": ["jersey", "mousemat", "hoodie", "tee", "cap", "sticker-sheet", "lanyard", "keychain"],
    "tech": ["business-card", "usb", "cable", "lanyard", "phone-case", "laptop-sleeve", "tee", "sticker-sheet"],
    "saas": ["business-card", "hoodie", "tee", "sticker-sheet", "mug", "notebook", "lanyard", "laptop-sleeve"],
    "artist": ["sticker-sheet", "business-card", "tee", "tote", "notebook", "poster", "pin-button"],
    "fashion": ["tote", "tee", "hoodie", "cap", "paper-bag", "label", "poster"],
    "fitness": ["tee", "bottle", "cap", "hoodie", "tote", "polo", "sticker"],
    "finance": ["business-card", "notebook", "mug", "tote", "poster", "lanyard", "signboard"],
    "services": ["business-card", "notebook", "mug", "polo", "tote", "signboard", "calendar"],
    "health": ["tote", "bottle", "tee", "notebook", "mug", "label", "business-card"],
    "beauty": ["label", "box", "paper-bag", "tote", "business-card", "sticker"],
    "event": ["tee", "lanyard", "tote", "cap", "sticker-sheet", "poster", "pin-button", "bottle"],
    "music": ["tee", "hoodie", "poster", "tote", "sticker-sheet", "pin-button", "cap"],
    "education": ["tee", "tote", "lanyard", "bottle", "sticker-sheet", "notebook", "hoodie"],
    "community": ["tee", "hoodie", "sticker-sheet", "tote", "cap", "pin-button", "mug"],
    "retail": ["paper-bag", "tote", "tee", "sticker-sheet", "mug", "business-card", "hoodie", "label"],
    "trades": ["polo", "cap", "tee", "business-card", "signboard", "mug", "sticker"],
    "kids": ["tee", "tote", "sticker-sheet", "bottle", "notebook", "cap"],
    "pets": ["tote", "tee", "label", "sticker-sheet", "bottle", "cap"],
    "general": ["tee", "tote", "mug", "business-card", "sticker-sheet", "notebook"],
}

ALIASES = {
    "cafe": "coffee", "café": "coffee", "roaster": "coffee", "roastery": "coffee", "coffee-shop": "coffee",
    "restaurant": "food", "takeaway": "food", "catering": "food", "beverage": "food", "drink": "food", "brewery": "bar",
    "pub": "bar", "winery": "bar", "bakery": "bakery", "patisserie": "bakery",
    "game": "gaming", "games": "gaming", "esports": "gaming", "clan": "gaming", "guild": "gaming", "streamer": "gaming",
    "software": "tech", "developer": "tech", "devtool": "tech", "developer-tools": "tech", "ai": "tech", "hardware": "tech",
    "it": "tech", "startup": "saas", "b2b": "saas", "platform": "saas", "app": "saas", "consumer-app": "saas",
    "illustrator": "artist", "designer": "artist", "creative": "artist", "studio": "artist", "photographer": "artist",
    "maker": "artist", "craft": "artist", "art": "artist",
    "clothing": "fashion", "apparel": "fashion", "boutique": "fashion",
    "gym": "fitness", "sport": "fitness", "sports": "fitness", "yoga": "fitness",
    "bank": "finance", "fintech": "finance", "insurance": "finance", "accounting": "finance", "legal": "services",
    "law": "services", "consulting": "services", "agency": "services", "real-estate": "services",
    "clinic": "health", "wellness": "health", "medical": "health", "dental": "health", "therapy": "health",
    "cosmetics": "beauty", "skincare": "beauty", "salon": "beauty",
    "festival": "event", "conference": "event", "meetup": "event", "band": "music", "label-records": "music",
    "school": "education", "university": "education", "nonprofit": "community", "charity": "community",
    "club": "community", "ecommerce": "retail", "shop": "retail", "store": "retail", "marketplace": "retail",
    "wishlist": "retail", "shopping": "retail", "construction": "trades", "plumber": "trades", "electrician": "trades",
    "landscaping": "trades", "children": "kids", "vet": "pets", "pet": "pets",
}


def resolve_type(brand):
    for key in ("business_type", "industry"):
        v = (brand.get(key) or "").strip().lower().replace(" ", "-")
        if not v:
            continue
        v = ALIASES.get(v, v)
        if v in BUSINESS_TYPES:
            return v
    return "general"


def items_for(brand, limit=8):
    """Explicit brand['merch'] wins; otherwise the business type's list (unknown keys dropped)."""
    explicit = [i for i in (brand.get("merch") or []) if i in ITEMS]
    if explicit:
        return explicit
    return BUSINESS_TYPES[resolve_type(brand)][:limit]


def page_url(item):
    slug = ITEMS[item][1]
    return (MD + slug + "/") if slug else None


def spec(item):
    label, slug, form, scale, cyl = ITEMS[item]
    return {"label": label, "page": page_url(item), "form": form, "scale": scale, "cylinder": cyl}
