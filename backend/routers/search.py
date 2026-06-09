import uuid
import hashlib
import urllib.parse
import re
import os
import logging
import httpx
from fastapi import APIRouter, HTTPException
from backend.models.schemas import SearchRequest, TextSearchRequest, SearchResponse, PlatformResult, PlatformPrice, LowCostPrediction
from backend.services import cache_service, affiliate_service
from backend.config import settings
from ml.clip_engine import get_engine

def parse_price(price_str: str) -> int:
    if not price_str:
        return 0
    cleaned = re.sub(r'[^\d]', '', price_str)
    return int(cleaned) if cleaned else 0

def predict_low_cost(matches: list, category: str = None) -> dict:
    prices = []
    for m in matches:
        p_str = m.get("price")
        p_val = parse_price(p_str)
        if p_val > 0:
            prices.append(p_val)
            
    # Fallback to category catalog if we don't have enough similar matches
    if len(prices) < 3 and category and category.lower() != "all":
        try:
            engine = get_engine()
            if hasattr(engine, "metadata") and engine.metadata:
                cat_matches = [p for p in engine.metadata if str(p.get("category", "")).lower() == category.lower()]
                for p in cat_matches:
                    p_str = p.get("price")
                    p_val = parse_price(p_str)
                    if p_val > 0:
                        prices.append(p_val)
        except Exception as e:
            pass
            
    if not prices:
        return {
            "low_cost_threshold": 0,
            "average_price": 0,
            "median_price": 0,
            "min_price": 0,
            "max_price": 0,
            "bargain_count": 0,
            "confidence_score": 0.0,
            "deal_rating": "N/A",
            "prediction_reasoning": "Not enough pricing data found to generate price insights."
        }
        
    prices = sorted(prices)
    min_p = min(prices)
    max_p = max(prices)
    avg_p = int(sum(prices) / len(prices))
    med_p = prices[len(prices) // 2]
    
    # Calculate 35th percentile for sweet spot bargain threshold
    idx = int(len(prices) * 0.35)
    threshold = prices[idx]
    
    # Adjust if threshold is same as min price or too close
    if threshold <= min_p and len(prices) > 1:
        threshold = int(min_p + (avg_p - min_p) * 0.4)
        
    if threshold == 0:
        threshold = int(avg_p * 0.8)
        
    # Count bargains in the visual matches
    matches_prices = [parse_price(m.get("price")) for m in matches if parse_price(m.get("price")) > 0]
    bargain_count = sum(1 for p in matches_prices if p <= threshold)
    
    if bargain_count > 0:
        min_match_price = min(matches_prices) if matches_prices else 0
        if min_match_price < threshold * 0.85:
            deal_rating = "Spectacular Bargain!"
            confidence = 0.95
        else:
            deal_rating = "Great Deals Available"
            confidence = 0.85
    else:
        deal_rating = "Standard Pricing"
        confidence = 0.70
        
    reasoning = (
        f"Our AI analyzed similar products and predicts that any price under ₹{threshold:,} is a 'Low Cost' bargain. "
        f"The average price for this range is ₹{avg_p:,}. "
    )
    if bargain_count > 0:
        reasoning += f"We found {bargain_count} options at or below this sweet spot!"
    else:
        reasoning += "All currently listed options are within the standard or premium price bracket."
        
    return {
        "low_cost_threshold": threshold,
        "average_price": avg_p,
        "median_price": med_p,
        "min_price": min_p,
        "max_price": max_p,
        "bargain_count": bargain_count,
        "confidence_score": confidence,
        "deal_rating": deal_rating,
        "prediction_reasoning": reasoning
    }

PLATFORMS_BY_CATEGORY = {
    "fashion": ["Myntra", "Ajio", "Flipkart", "Amazon India", "Meesho"],
    "footwear": ["Amazon India", "Flipkart", "Myntra", "Ajio", "Meesho"],
    "electronics": ["Amazon India", "Flipkart", "Meesho"],
    "beauty": ["Nykaa", "Amazon India", "Flipkart"],
    "furniture": ["Amazon India", "Flipkart", "Ajio"],
    "watches": ["Amazon India", "Flipkart", "Myntra", "Ajio"],
    "bags": ["Myntra", "Amazon India", "Flipkart"],
    "accessories": ["Amazon India", "Flipkart", "Myntra", "Ajio"],
    "default": ["Amazon India", "Flipkart", "Myntra", "Ajio", "Meesho"]
}

def get_seeded_comparison_prices(product_id: str, title: str, base_price_str: str, original_platform: str, category: str) -> dict:
    base_price = parse_price(base_price_str)
    if base_price == 0:
        return {
            "comparison_prices": [],
            "lowest_price_platform": original_platform,
            "lowest_price": base_price_str
        }
        
    cat = (category or "default").lower()
    platforms = PLATFORMS_BY_CATEGORY.get(cat, PLATFORMS_BY_CATEGORY["default"])
    
    if original_platform not in platforms:
        platforms = [original_platform] + [p for p in platforms if p != original_platform]
        
    comparison_list = []
    lowest_val = base_price
    lowest_platform = original_platform
    
    for platform in platforms:
        if platform == original_platform:
            comparison_list.append({
                "platform": original_platform,
                "price": base_price_str,
                "original_price": None,
                "discount": None,
                "buy_url": "", 
                "is_lowest": False
            })
            continue
            
        seed = f"{product_id}_{platform}".encode("utf-8")
        h = int(hashlib.md5(seed).hexdigest(), 16)
        
        multiplier = 0.85 + (h % 28) * 0.01
        platform_price_val = int(base_price * multiplier)
        platform_price_val = (platform_price_val // 10) * 10 + 9
        
        orig_price_val = int(platform_price_val * (1.2 + (h % 5) * 0.05))
        orig_price_val = (orig_price_val // 50) * 50 - 1
        
        disc_percent = int((1 - platform_price_val / orig_price_val) * 100)
        
        price_str = f"₹{platform_price_val:,}"
        orig_price_str = f"₹{orig_price_val:,}"
        disc_str = f"{disc_percent}% off"
        
        if platform_price_val < lowest_val:
            lowest_val = platform_price_val
            lowest_platform = platform
            
        comparison_list.append({
            "platform": platform,
            "price": price_str,
            "original_price": orig_price_str,
            "discount": disc_str,
            "buy_url": "", 
            "is_lowest": False
        })
        
    for item in comparison_list:
        val = parse_price(item["price"])
        if val == lowest_val and item["platform"] == lowest_platform:
            item["is_lowest"] = True
            
    lowest_price_str = f"₹{lowest_val:,}"
    
    return {
        "comparison_prices": [PlatformPrice(**item) for item in comparison_list],
        "lowest_price_platform": lowest_platform,
        "lowest_price": lowest_price_str
    }

BLOCKLIST_DOMAINS = [
    "pinterest.",
    "instagram.com",
    "facebook.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "tumblr.com",
    "flickr.com",
    "wikipedia.org",
    "nytimes.com",
    "cnn.com",
    "bbc.co.uk",
    "bbc.com",
    "blogspot.com",
    "wordpress.com",
    "medium.com",
    "shutterstock.com",
    "istockphoto.com",
    "dreamstime.com",
    "depositphotos.com",
    "alamy.com",
    "adobe.com",
    "freepik.com",
    "unsplash.com",
    "pixabay.com",
    "wiki",
    "news"
]

logger = logging.getLogger("backend.search")

async def search_serpapi_google_lens(image_url: str, max_results: int, category: str = None) -> list[dict]:
    # 1. If it's a local file, we must upload it to a public host (e.g. tmpfiles.org)
    public_url = image_url
    if "/static/uploads/" in image_url:
        filename = image_url.split("/")[-1]
        filepath = os.path.join("data/uploads", filename)
        if os.path.exists(filepath):
            try:
                # Upload to tmpfiles.org
                async with httpx.AsyncClient() as client:
                    with open(filepath, "rb") as f:
                        files = {"file": (filename, f, "image/jpeg")}
                        r = await client.post("https://tmpfiles.org/api/v1/upload", files=files, timeout=20.0)
                        if r.status_code == 200:
                            data = r.json()
                            raw_url = data["data"]["url"]
                            # Transform to direct download url
                            public_url = raw_url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
                            logger.info(f"Uploaded local image to tmpfiles.org: {public_url}")
                        else:
                            logger.warning(f"Failed to upload to tmpfiles.org. Status: {r.status_code}")
            except Exception as upload_err:
                logger.error(f"Failed to upload to tmpfiles.org: {upload_err}")

    # 2. Query SerpApi Google Lens
    serpapi_key = os.environ.get("SERPAPI_KEY", "") or getattr(settings, "SERPAPI_KEY", "")
    if not serpapi_key:
        logger.warning("SERPAPI_KEY is not set. Cannot run web search.")
        return []

    params = {
        "engine": "google_lens",
        "url": public_url,
        "api_key": serpapi_key
    }
    
    logger.info(f"Querying SerpApi Google Lens with URL: {public_url}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://serpapi.com/search", params=params, timeout=25.0)
            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("visual_matches", [])
                logger.info(f"SerpApi Google Lens found {len(matches)} matches.")
                
                transformed = []
                for i, match in enumerate(matches):
                    buy_url = match.get("link", match.get("product_link", "#"))
                    source = match.get("source", "Web Store")
                    
                    # Check blocklist to ensure results represent real buying places
                    buy_url_lower = buy_url.lower()
                    source_lower = source.lower()
                    if any(blocked in buy_url_lower or blocked in source_lower for blocked in BLOCKLIST_DOMAINS):
                        continue
                        
                    price_val = match.get("price")
                    price_str = "Price on Website"
                    if isinstance(price_val, dict):
                        currency = price_val.get("currency", "₹")
                        val = price_val.get("extracted_value", price_val.get("value", ""))
                        if val:
                            price_str = f"{currency}{val}"
                    elif isinstance(price_val, str):
                        price_str = price_val
                        
                    prod = {
                        "id": f"SERP_{i}_{hash(match.get('title','')) % 10000}",
                        "title": match.get("title", "Product"),
                        "price": price_str,
                        "platform": source,
                        "buy_url": buy_url,
                        "image_url": match.get("thumbnail", ""),
                        "thumbnail": match.get("thumbnail", ""),
                        "category": category or "general",
                        "similarity_score": round(0.95 - (i * 0.01), 4),
                        "rating": str(match.get("rating", "")) if match.get("rating") else None,
                    }
                    transformed.append(prod)
                    if len(transformed) >= max_results:
                        break
                return transformed
            else:
                logger.error(f"SerpApi returned error status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"SerpApi request failed: {e}")
        
    return []

async def search_serpapi_google_shopping(query: str, max_results: int, category: str = None) -> list[dict]:
    serpapi_key = os.environ.get("SERPAPI_KEY", "") or getattr(settings, "SERPAPI_KEY", "")
    if not serpapi_key:
        logger.warning("SERPAPI_KEY is not set. Cannot run web search.")
        return []

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": serpapi_key
    }
    
    logger.info(f"Querying SerpApi Google Shopping for query: {query}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://serpapi.com/search", params=params, timeout=25.0)
            if resp.status_code == 200:
                data = resp.json()
                matches = data.get("shopping_results", [])
                logger.info(f"SerpApi Google Shopping found {len(matches)} matches.")
                
                transformed = []
                for i, match in enumerate(matches):
                    price_str = match.get("price", "Price on Website")
                    prod = {
                        "id": f"SHOP_{i}_{hash(match.get('title','')) % 10000}",
                        "title": match.get("title", "Product"),
                        "price": price_str,
                        "platform": match.get("source", "Web Store"),
                        "buy_url": match.get("link", match.get("product_link", "#")),
                        "image_url": match.get("thumbnail", ""),
                        "thumbnail": match.get("thumbnail", ""),
                        "category": category or "general",
                        "similarity_score": round(0.95 - (i * 0.01), 4),
                        "rating": str(match.get("rating", "")) if match.get("rating") else None,
                    }
                    transformed.append(prod)
                    if len(transformed) >= max_results:
                        break
                return transformed
            else:
                logger.error(f"SerpApi returned error status {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"SerpApi Google Shopping request failed: {e}")
        
    return []

router = APIRouter()

def _generate_product_url(platform: str, title: str, fallback_url: str) -> str:
    """Return the direct product URL. If unavailable, fallback to a search URL."""
    if fallback_url and fallback_url != "#":
        return fallback_url
        
    if not title or title == "Unknown Product":
        return fallback_url
        
    query = urllib.parse.quote_plus(title)
    p = platform.lower()
    
    if "amazon" in p:
        return f"https://www.amazon.in/s?k={query}"
    elif "flipkart" in p:
        return f"https://www.flipkart.com/search?q={query}"
    elif "myntra" in p:
        return f"https://www.myntra.com/{query}"
    elif "ajio" in p:
        return f"https://www.ajio.com/search/?text={query}"
    elif "meesho" in p:
        return f"https://www.meesho.com/search?q={query}"
    elif "nykaa" in p:
        return f"https://www.nykaa.com/search/result/?q={query}"
        
    return fallback_url

@router.post("/search", response_model=SearchResponse)
async def search_by_image(payload: SearchRequest):
    """
    Search products using a local FAISS index with CLIP embeddings.
    """
    # ── 1. Cache lookup ─────────
    cache_key = f"{payload.image_hash}_{payload.category}"
    cached = cache_service.get_cached(cache_key)
    if cached:
        cached["cached"] = True
        return SearchResponse(**cached)

    # ── 2. SerpApi Google Lens (Web) or Local CLIP + FAISS search ──────
    raw_results = []
    detected_category = None
    serpapi_key = os.environ.get("SERPAPI_KEY", "") or getattr(settings, "SERPAPI_KEY", "")

    # Try SerpApi Google Lens first
    if serpapi_key:
        try:
            raw_results = await search_serpapi_google_lens(
                image_url=payload.image_url,
                max_results=payload.max_results,
                category=payload.category
            )
            # Classify category using local CLIP zero-shot model
            if raw_results and (payload.category is None or payload.category.lower() == "all"):
                try:
                    engine = get_engine()
                    if "/static/uploads/" in payload.image_url:
                        filename = payload.image_url.split("/")[-1]
                        filepath = os.path.join("data/uploads", filename)
                        with open(filepath, "rb") as f:
                            image_bytes = f.read()
                        vec = engine.embed_bytes(image_bytes)
                    else:
                        vec = engine.embed_url(payload.image_url)
                    detected_category = engine.detect_category(vec)
                except Exception as cat_err:
                    logger.warning(f"Failed to auto-detect category for SerpApi results: {cat_err}")
        except Exception as serp_err:
            logger.error(f"SerpApi image search failed, falling back to local search: {serp_err}")

    # Fallback to local CLIP + FAISS index search if SerpApi results are empty
    if not raw_results:
        engine = get_engine()
        try:
            if "/static/uploads/" in payload.image_url:
                filename = payload.image_url.split("/")[-1]
                filepath = os.path.join("data/uploads", filename)
                with open(filepath, "rb") as f:
                    image_bytes = f.read()
                res_dict = engine.search_by_image_bytes(
                    data=image_bytes,
                    top_k=payload.max_results,
                    category=payload.category
                )
            else:
                res_dict = engine.search_by_image_url(
                    url=payload.image_url,
                    top_k=payload.max_results,
                    category=payload.category
                )
            raw_results = res_dict["results"]
            detected_category = res_dict.get("detected_category")
        except Exception as e:
            raise HTTPException(502, detail=f"Search failed: {e}")

    # ── 3. Low-Cost Prediction ────────────────
    active_category = payload.category or detected_category
    pred_res = predict_low_cost(raw_results, active_category)
    low_cost_threshold = pred_res["low_cost_threshold"]
    low_cost_prediction_obj = LowCostPrediction(**pred_res)

    # ── 4. Parse output ──────────────────────
    platform_results = []
    visual_matches = []
    
    import logging
    search_logger = logging.getLogger("backend.search")
    search_logger.info(f"Image search found {len(raw_results)} results.")

    for i, item in enumerate(raw_results):
        score = item.get("similarity_score", 0)
        title = item.get("title", "Unknown Product")
        if i < 3:
            search_logger.info(f" Top {i+1}: {title} (Score: {score})")
        platform = item.get("platform", "Local Catalog")
        fallback_url = item.get("buy_url", item.get("url", "#"))
        
        # Generate a proper URL instead of the generic category page
        proper_url = _generate_product_url(platform, title, fallback_url)
        
        comp_info = get_seeded_comparison_prices(
            product_id=item.get("id", f"PROD_{i}"),
            title=title,
            base_price_str=item.get("price") or "",
            original_platform=platform,
            category=item.get("category", "unknown")
        )
        for cp in comp_info["comparison_prices"]:
            if cp.platform == platform:
                cp.buy_url = proper_url
            else:
                cp.buy_url = _generate_product_url(cp.platform, title, "")

        item_price_val = parse_price(item.get("price") or "")
        is_low_cost_flag = (item_price_val > 0 and item_price_val <= low_cost_threshold)

        pr = PlatformResult(
            platform=platform,
            title=title,
            price=item.get("price"),
            original_price=item.get("original_price"),
            discount=item.get("discount"),
            product_url=proper_url,
            affiliate_url=proper_url,
            thumbnail=item.get("thumbnail") or item.get("image_url") or item.get("image"),
            rating=item.get("rating"),
            category=item.get("category", "unknown"),
            similarity_score=score,
            in_stock=True,
            comparison_prices=comp_info["comparison_prices"],
            lowest_price_platform=comp_info["lowest_price_platform"],
            lowest_price=comp_info["lowest_price"],
            is_low_cost=is_low_cost_flag
        )
        platform_results.append(pr)

        vm = {
            "title": title,
            "link": proper_url,
            "thumbnail": item.get("thumbnail") or item.get("image_url") or item.get("image"),
            "source": platform,
            "price": item.get("price"),
            "category": item.get("category", "unknown"),
            "similarity_score": score,
            "comparison_prices": [cp.model_dump() for cp in comp_info["comparison_prices"]],
            "lowest_price_platform": comp_info["lowest_price_platform"],
            "lowest_price": comp_info["lowest_price"],
            "is_low_cost": is_low_cost_flag
        }
        visual_matches.append(vm)

    # ── 5. Assemble response ─────────────────────
    response_data = {
        "query_image_url":  payload.image_url,
        "visual_matches":   visual_matches,
        "platform_results": [r.model_dump() for r in platform_results],
        "total_results":    len(visual_matches),
        "cached":           False,
        "search_id":        str(uuid.uuid4()),
        "low_cost_prediction": low_cost_prediction_obj.model_dump()
    }

    # ── 6. Store in Redis ───────────────
    cache_service.set_cache(cache_key, response_data)
    return SearchResponse(**response_data)


@router.post("/search/text", response_model=SearchResponse)
async def search_by_text(payload: TextSearchRequest):
    """
    Search products using a text query via CLIP + FAISS.
    """
    query_str = f"{payload.query}_{payload.category}"
    query_hash = hashlib.sha256(query_str.encode()).hexdigest()

    # ── 1. Cache lookup ─────────
    cached = cache_service.get_cached(query_hash)
    if cached:
        cached["cached"] = True
        return SearchResponse(**cached)

    # ── 2. SerpApi Google Shopping or Local CLIP + FAISS search ──────
    raw_results = []
    detected_category = None
    serpapi_key = os.environ.get("SERPAPI_KEY", "") or getattr(settings, "SERPAPI_KEY", "")

    # Try SerpApi Google Shopping first
    if serpapi_key:
        try:
            raw_results = await search_serpapi_google_shopping(
                query=payload.query,
                max_results=payload.max_results,
                category=payload.category
            )
            if raw_results and (payload.category is None or payload.category.lower() == "all"):
                try:
                    engine = get_engine()
                    detected_category = engine.detect_category_from_text(payload.query)
                except Exception as cat_err:
                    logger.warning(f"Failed to auto-detect category from query: {cat_err}")
        except Exception as serp_err:
            logger.error(f"SerpApi text search failed, falling back to local: {ser_err}")

    # Fallback to local CLIP + FAISS search if SerpApi results are empty
    if not raw_results:
        engine = get_engine()
        try:
            res_dict = engine.search_by_text(
                text=payload.query,
                top_k=payload.max_results,
                category=payload.category
            )
            raw_results = res_dict["results"]
            detected_category = res_dict.get("detected_category")
        except Exception as e:
            raise HTTPException(502, detail=f"Search failed: {e}")

    # ── 3. Low-Cost Prediction ────────────────
    active_category = payload.category or detected_category
    pred_res = predict_low_cost(raw_results, active_category)
    low_cost_threshold = pred_res["low_cost_threshold"]
    low_cost_prediction_obj = LowCostPrediction(**pred_res)

    # ── 4. Parse output ──────────────────────
    platform_results = []
    visual_matches = []
    
    import logging
    search_logger = logging.getLogger("backend.search")
    search_logger.info(f"Text Search for '{payload.query}' found {len(raw_results)} results.")

    for i, item in enumerate(raw_results):
        score = item.get("similarity_score", 0)
        title = item.get("title", "Unknown Product")
        if i < 3:
            search_logger.info(f" Top {i+1}: {title} (Score: {score})")
        platform = item.get("platform", "Local Catalog")
        fallback_url = item.get("buy_url", item.get("url", "#"))
        
        # Generate a proper URL instead of the generic category page
        proper_url = _generate_product_url(platform, title, fallback_url)
        
        comp_info = get_seeded_comparison_prices(
            product_id=item.get("id", f"PROD_{i}"),
            title=title,
            base_price_str=item.get("price") or "",
            original_platform=platform,
            category=item.get("category", "unknown")
        )
        for cp in comp_info["comparison_prices"]:
            if cp.platform == platform:
                cp.buy_url = proper_url
            else:
                cp.buy_url = _generate_product_url(cp.platform, title, "")

        item_price_val = parse_price(item.get("price") or "")
        is_low_cost_flag = (item_price_val > 0 and item_price_val <= low_cost_threshold)

        pr = PlatformResult(
            platform=platform,
            title=title,
            price=item.get("price"),
            original_price=item.get("original_price"),
            discount=item.get("discount"),
            product_url=proper_url,
            affiliate_url=proper_url,
            thumbnail=item.get("thumbnail") or item.get("image_url") or item.get("image"),
            rating=item.get("rating"),
            category=item.get("category", "unknown"),
            similarity_score=score,
            in_stock=True,
            comparison_prices=comp_info["comparison_prices"],
            lowest_price_platform=comp_info["lowest_price_platform"],
            lowest_price=comp_info["lowest_price"],
            is_low_cost=is_low_cost_flag
        )
        platform_results.append(pr)

        vm = {
            "title": title,
            "link": proper_url,
            "thumbnail": item.get("thumbnail") or item.get("image_url") or item.get("image"),
            "source": platform,
            "price": item.get("price"),
            "category": item.get("category", "unknown"),
            "similarity_score": score,
            "comparison_prices": [cp.model_dump() for cp in comp_info["comparison_prices"]],
            "lowest_price_platform": comp_info["lowest_price_platform"],
            "lowest_price": comp_info["lowest_price"],
            "is_low_cost": is_low_cost_flag
        }
        visual_matches.append(vm)

    # ── 5. Assemble response ─────────────────────
    response_data = {
        "query_image_url":  "",  # Empty for text search
        "visual_matches":   visual_matches,
        "platform_results": [r.model_dump() for r in platform_results],
        "total_results":    len(visual_matches),
        "cached":           False,
        "search_id":        str(uuid.uuid4()),
        "low_cost_prediction": low_cost_prediction_obj.model_dump()
    }

    # ── 6. Store in Redis (6h TTL) ───────────────
    cache_service.set_cache(query_hash, response_data)
    return SearchResponse(**response_data)