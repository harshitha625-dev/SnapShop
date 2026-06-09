from urllib.parse import urlparse, quote_plus
from backend.config import settings
from backend.models.schemas import PlatformResult

# URL domain → platform key
PLATFORM_MAP = {
    "amazon.in":    "amazon",
    "flipkart.com": "flipkart",
    "myntra.com":   "myntra",
    "ajio.com":     "ajio",
    "meesho.com":   "meesho",
    "nykaa.com":    "nykaa",
}

def detect_platform(url: str) -> str | None:
    """Simple domain matching — no ML needed for this step."""
    host = urlparse(url).hostname or ""
    for domain, platform in PLATFORM_MAP.items():
        if domain in host:
            return platform
    return None

def build_affiliate_url(url: str, platform: str) -> str:
    if platform == "amazon":
        # Amazon: append Associate tag as query param
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}tag={settings.AMAZON_AFFILIATE_TAG}"

    elif platform == "flipkart":
        # Flipkart: wrap with affiliate redirect URL
        enc = quote_plus(url)
        return (
            f"https://www.flipkart.com/ad/affiliate?"
            f"affid={settings.FLIPKART_AFFILIATE_ID}&url={enc}"
        )

    elif platform in ("myntra", "ajio", "nykaa", "meesho"):
        # Cuelinks: single sub-affiliate network for all others
        enc = quote_plus(url)
        return f"https://linksredirect.com/?cid={settings.CUELINKS_CID}&url={enc}"

    return url  # unknown platform — return as-is

def build_platform_result(raw: dict) -> PlatformResult | None:
    url      = raw.get("link") or raw.get("buy_url") or ""
    platform = detect_platform(url)

    # Fallback: match by merchant name string
    if not platform:
        src = (raw.get("source") or "").lower()
        platform = next(
            (p for p in PLATFORM_MAP.values() if p in src),
            "general"
        )

    DISPLAY = {
        "amazon":   "Amazon India", "flipkart": "Flipkart",
        "myntra":   "Myntra",       "ajio":     "Ajio",
        "meesho":   "Meesho",       "nykaa":    "Nykaa",
        "general":  "Web",
    }
    return PlatformResult(
        platform=      DISPLAY.get(platform, platform.title()),
        title=         raw.get("title", ""),
        price=         raw.get("price"),
        original_price=raw.get("original_price"),
        discount=      raw.get("discount"),
        product_url=   url,
        affiliate_url= build_affiliate_url(url, platform),
        thumbnail=     raw.get("thumbnail"),
        rating=        str(raw.get("rating")) if raw.get("rating") else None,
        in_stock=      True,
    )