'''"""
backend/routers/catalog.py
Manage the product catalog and FAISS index at runtime.
"""
import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends

from backend.models.schemas import IndexStats
from ml.clip_engine import CLIPEngine, get_engine

router = APIRouter()
logger = logging.getLogger(__name__)
CATALOG_PATH = Path("data/catalog.json")


@router.get("/catalog/stats", response_model=IndexStats)
def get_stats(engine: CLIPEngine = Depends(get_engine)):
    """How many products are indexed, what device, model info."""
    return IndexStats(**engine.get_index_stats())


@router.get("/catalog/products")
def list_products(engine: CLIPEngine = Depends(get_engine)):
    """List all indexed products."""
    return {"products": engine.metadata, "total": len(engine.metadata)}


@router.get("/catalog/trending")
def trending():
    """Trending search categories for the homepage."""
    return {"categories": [
        {"icon": "👗", "name": "Ethnic Wear",   "text": "indian kurta ethnic dress"},
        {"icon": "👟", "name": "Sneakers",       "text": "sports sneakers running shoes"},
        {"icon": "⌚", "name": "Watches",        "text": "wrist watch analog"},
        {"icon": "📱", "name": "Smartphones",    "text": "smartphone mobile android"},
        {"icon": "👜", "name": "Bags",           "text": "women handbag tote"},
        {"icon": "💄", "name": "Beauty",         "text": "lipstick makeup beauty"},
    ]}


@router.post("/catalog/rebuild")
async def rebuild_index(engine: CLIPEngine = Depends(get_engine)):
    """
    Reload catalog from disk and rebuild the FAISS index.
    Call this after adding new products to catalog.json.
    """
    if not CATALOG_PATH.exists():
        raise HTTPException(404, f"Catalog not found at {CATALOG_PATH}")

    with open(CATALOG_PATH) as f:
        catalog = json.load(f)

    logger.info(f"Rebuilding index with {len(catalog)} products…")
    engine.build_index(catalog, save=True)

    return {
        "message": f"Index rebuilt with {engine.index.ntotal} products",
        "total":   engine.index.ntotal,
    }


@router.post("/catalog/add")
async def add_product(product: dict, engine: CLIPEngine = Depends(get_engine)):
    """
    Add a single product to the catalog and re-index it.

    Required fields: id, title, price, platform, buy_url, image_url
    """
    required = ["id", "title", "price", "platform", "buy_url", "image_url"]
    missing  = [f for f in required if f not in product]
    if missing:
        raise HTTPException(422, f"Missing fields: {missing}")

    # Append to catalog file
    catalog = json.loads(CATALOG_PATH.read_text()) if CATALOG_PATH.exists() else []
    if any(p["id"] == product["id"] for p in catalog):
        raise HTTPException(409, f"Product ID '{product['id']}' already exists")

    catalog.append(product)
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))

    # Rebuild index
    engine.build_index(catalog, save=True)
    return {"message": f"Added '{product['title']}'. Index now has {engine.index.ntotal} products."}'''


"""backend/routers/catalog.py"""
import json
from pathlib import Path
from fastapi import APIRouter, Depends
from ml.clip_engine import CLIPEngine, get_engine

router  = APIRouter()
CATALOG = Path("data/catalog.json")

@router.get("/catalog/stats")
def stats(engine: CLIPEngine = Depends(get_engine)):
    return engine.get_stats()

@router.get("/catalog/trending")
def trending():
    return {"categories": [
        {"icon":"👗","name":"Ethnic Wear",  "description":"blue anarkali kurta ethnic dress"},
        {"icon":"👟","name":"Sneakers",     "description":"white nike adidas running sneakers"},
        {"icon":"⌚","name":"Watches",      "description":"analog wristwatch formal dial"},
        {"icon":"📱","name":"Smartphones",  "description":"android smartphone samsung oneplus"},
        {"icon":"👜","name":"Bags",         "description":"women leather handbag tote"},
        {"icon":"💄","name":"Beauty",       "description":"lipstick makeup foundation cosmetics"},
    ]}

@router.post("/catalog/rebuild")
async def rebuild(engine: CLIPEngine = Depends(get_engine)):
    catalog = json.loads(CATALOG.read_text())
    engine.build_index(catalog, save=True)
    return {"message": f"Rebuilt with {engine.index.ntotal} products"}