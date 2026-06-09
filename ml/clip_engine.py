'''"""
ml/clip_engine.py
══════════════════════════════════════════════════════════════
The core ML engine. Does 3 things:
  1. embed_image()  — convert any image → 512-dim vector using CLIP
  2. build_index()  — index a product catalog into FAISS
  3. search()       — find top-K similar products by vector distance

HOW CLIP WORKS (plain English):
  - CLIP (Contrastive Language-Image Pretraining) by OpenAI
  - Trained on 400M image-text pairs from the internet
  - Splits image into 16×16 patches → runs transformer attention
  - Output: 512-dimensional vector that captures visual semantics
  - Same product from different angles → vectors are very close
  - Different products → vectors are far apart

HOW FAISS WORKS:
  - Facebook AI Similarity Search
  - Stores all product vectors in an optimized index
  - Given a query vector, finds the K nearest neighbors
  - Uses cosine similarity (inner product on normalized vectors)
  - Speed: searches 1M vectors in ~10ms on GPU
"""

import os
import json
import time
import logging
import numpy as np
from pathlib import Path
from typing import Optional

import torch
import open_clip
import faiss
from PIL import Image
import requests
from io import BytesIO

# Register additional image formats for Pillow
try:
    import pillow_avif
except ImportError:
    pass

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ── Paths ────────────────────────────────────────────────────
INDEX_PATH    = Path("data/products.faiss")
METADATA_PATH = Path("data/products_meta.json")
CATALOG_PATH  = Path("data/catalog.json")


class CLIPEngine:
    """
    Wraps CLIP model + FAISS index into a single searchable engine.
    
    Usage:
        engine = CLIPEngine()
        engine.load_or_build_index("data/catalog.json")
        results = engine.search_by_image_url("https://example.com/shoe.jpg")
    """

    def __init__(self, model_name: str = "ViT-L-14", pretrained: str = "openai"):
        """
        Load the CLIP model.
        
        Model options (accuracy vs speed tradeoff):
          ViT-B-32   → fastest,  good accuracy  (default - works well on GPU)
          ViT-B-16   → medium,   better accuracy
          ViT-L-14   → slowest,  best accuracy  (recommended for production)
        
        For fashion: use 'hf-hub:patrickjohncyh/fashion-clip'
        """
        logger.info(f"Loading CLIP model: {model_name} / {pretrained}")
        t = time.time()

        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Fix QuickGELU mismatch for OpenAI weights
        force_quick_gelu = True if pretrained == "openai" else False
        
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained=pretrained,
            device=self.device,
            force_quick_gelu=force_quick_gelu
        )
        self.model.eval()

        # Get embedding dimension from model
        with torch.no_grad():
            dummy = torch.zeros(1, 3, 224, 224).to(self.device)
            self.dim = self.model.encode_image(dummy).shape[-1]

        logger.info(f"Model loaded in {time.time()-t:.2f}s | dim={self.dim} | device={self.device}")

        # FAISS index + metadata
        self.index     : Optional[faiss.Index] = None
        self.metadata  : list[dict]            = []   # product info per row

    # ════════════════════════════════════════════════════════
    # EMBEDDING
    # ════════════════════════════════════════════════════════

    def embed_image_file(self, image_path: str) -> np.ndarray:
        """
        Convert a local image file → normalized 512-dim float32 vector.
        
        Steps:
          1. Open image with PIL
          2. Resize + normalize with CLIP's own preprocess fn
          3. Run through ViT encoder
          4. L2-normalize so cosine similarity = dot product
        """
        img = Image.open(image_path).convert("RGB")
        return self._embed_pil(img)

    def embed_image_bytes(self, image_bytes: bytes) -> np.ndarray:
        """Convert raw image bytes → embedding vector."""
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        return self._embed_pil(img)
    
    def embed_image_url(self, url: str) -> np.ndarray:
        """Download image from URL → embedding vector."""
        try:
            resp = requests.get(
                url,
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            resp.raise_for_status()
            return self.embed_image_bytes(resp.content)
        except Exception as e:
            raise RuntimeError(f"Failed to load image: {url} | {e}")

    def _embed_pil(self, img: Image.Image) -> np.ndarray:
        """Core embedding function."""
        tensor = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            emb = self.model.encode_image(tensor).float()

            # L2 normalize → cosine similarity becomes dot product
            emb = emb / emb.norm(dim=-1, keepdim=True)

        return emb.cpu().numpy()

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a text query (e.g. 'red sneakers') into the same vector space.
        Uses prompt ensembling for higher accuracy.
        """
        # Ensure we use the correct tokenizer for the current model
        tokenizer = open_clip.get_tokenizer(self.model_name if hasattr(self, 'model_name') else "ViT-L-14")
        
        # CLIP works better with descriptive prompts
        prompts = [
            f"a product photo of {text}",
            f"a professional studio photo of {text}",
            f"a high-quality image of {text}",
            f"a clear picture of {text}",
            f"the product {text}",
            text
        ]
        tokens = tokenizer(prompts).to(self.device)

        with torch.no_grad():
            # Get embeddings for all prompts
            embs = self.model.encode_text(tokens).float()
            embs = embs / embs.norm(dim=-1, keepdim=True)
            
            # Average them (Ensembling)
            emb = embs.mean(dim=0, keepdim=True)
            emb = emb / emb.norm(dim=-1, keepdim=True)

        return emb.cpu().numpy()

    # ════════════════════════════════════════════════════════
    # INDEXING
    # ════════════════════════════════════════════════════════

    def build_index(self, catalog: list[dict], save: bool = True) -> None:
        """
        Index a product catalog into FAISS.

        catalog format:
          [
            {
              "id":        "PROD_001",
              "title":     "Nike Air Max 270",
              "price":     "₹7,995",
              "platform":  "Amazon India",
              "buy_url":   "https://...",
              "image_url": "https://...",
              "category":  "sneakers",
              "thumbnail": "https://..."
            },
            ...
          ]

        What happens:
          1. For each product, download its image
          2. Run it through CLIP to get a 512-dim vector
          3. Add that vector to the FAISS index
          4. Store metadata (price, title, url) separately by row index
        """
        if not catalog:
            raise ValueError("Catalog is empty")

        logger.info(f"Building FAISS index for {len(catalog)} products…")

        # IndexFlatIP = exact inner product search
        # Use GPU index if available for much faster search
        cpu_index = faiss.IndexFlatIP(self.dim)

        if self.device == "cuda" and faiss.get_num_gpus() > 0:
            res          = faiss.StandardGpuResources()
            self.index   = faiss.index_cpu_to_gpu(res, 0, cpu_index)
            logger.info("FAISS running on GPU ✓")
        else:
            self.index   = cpu_index
            logger.info("FAISS running on CPU")

        self.metadata = []
        embeddings    = []
        failed        = 0

        for i, product in enumerate(catalog):
            try:
                # ✅ Support both keys
                image_url = product.get("image") or product.get("image_url")

                if not image_url:
                    logger.warning(f"  Skipping '{product.get('title','?')}' — no image field")
                    failed += 1
                    continue

                emb = self.embed_image_url(image_url)
                embeddings.append(emb)
                self.metadata.append(product)

                # ✅ Debug print (important)
                logger.info(f"Indexed: {product.get('title')}")

                '''#if (i + 1) % 5 == 0:
                    #logger.info(f"  Progress: {i+1}/{len(catalog)}")'''

''' except Exception as e:
                logger.warning(f"  Skipped '{product.get('title','?')}': {e}")
                failed += 1

        if not embeddings:
            raise RuntimeError("No products could be indexed — check image URLs")

        matrix = np.vstack(embeddings).astype(np.float32)
        self.index.add(matrix)

        logger.info(f"Index built: {self.index.ntotal} vectors | {failed} skipped")

        if save:
            self._save_index()

    def _save_index(self):
        """Persist FAISS index + metadata to disk."""
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Convert GPU index to CPU before saving
        cpu_index = faiss.index_gpu_to_cpu(self.index) if hasattr(self.index, 'index') else self.index
        faiss.write_index(cpu_index, str(INDEX_PATH))

        with open(METADATA_PATH, "w") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved index → {INDEX_PATH} ({INDEX_PATH.stat().st_size/1024:.1f} KB)")

    def load_index(self) -> bool:
        """Load a previously built index from disk."""
        if not INDEX_PATH.exists() or not METADATA_PATH.exists():
            return False

        cpu_index  = faiss.read_index(str(INDEX_PATH))

        if self.device == "cuda" and faiss.get_num_gpus() > 0:
            res        = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
        else:
            self.index = cpu_index

        with open(METADATA_PATH) as f:
            self.metadata = json.load(f)

        logger.info(f"Loaded index: {self.index.ntotal} products from {INDEX_PATH}")
        return True

    def load_or_build_index(self, catalog_path: str = str(CATALOG_PATH)) -> None:
        """Load existing index, or build from catalog if not found."""
        if self.load_index():
            logger.info("Using existing FAISS index ✓")
            return

        logger.info("No index found — building from catalog…")
        with open(catalog_path) as f:
            catalog = json.load(f)
        self.build_index(catalog)

    # ════════════════════════════════════════════════════════
    # SEARCH
    # ════════════════════════════════════════════════════════

    def search(
        self,
        query_vector : np.ndarray,
        top_k        : int   = 20,
        min_score    : float = 0.12,   # cosine similarity floor
        category     : str   = None,   # optional category filter
        text_query   : str   = None    # optional query for keyword boosting
    ) -> list[dict]:
        """
        Core ANN search.

        Args:
            query_vector: normalized 512-dim float32 array (1 × dim)
            top_k:        how many results to return
            min_score:    discard results below this cosine similarity
            category:     if provided, only return products in this category
        """
        if self.index is None or self.index.ntotal == 0:
            raise RuntimeError("Index not loaded. Call load_or_build_index() first.")

        # If filtering or boosting, search for more items initially
        search_k = top_k * 10 if (category or text_query) else top_k
        search_k = min(search_k, self.index.ntotal)

        # FAISS search — returns (scores, indices) both shape (1, search_k)
        scores, indices = self.index.search(query_vector, search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:              # FAISS padding for empty slots
                continue
            
            if float(score) < min_score:
                continue

            product = dict(self.metadata[idx])
            
            # Apply category filter if requested
            if category and category.lower() != "all":
                prod_cat = str(product.get("category", "")).lower()
                if category.lower() not in prod_cat:
                    continue

            product["similarity_score"] = round(float(score), 4)
            
            # Apply keyword matching
            if text_query:
                q_words = [w.lower() for w in text_query.lower().split() if len(w) > 2]
                title_lower = product.get("title", "").lower()
                cat_lower = str(product.get("category", "")).lower()
                
                # Check if any query word matches title or category
                matches = [w for w in q_words if w in title_lower or w in cat_lower]
                if matches:
                    # Boost score based on number of matches
                    product["similarity_score"] = min(1.0, product["similarity_score"] + 0.1 + (len(matches) * 0.05))
                    product["has_keyword_match"] = True
                else:
                    product["has_keyword_match"] = False
            else:
                product["has_keyword_match"] = False

            results.append(product)

            if len(results) >= search_k:
                break

        # Strict Filtering: If any result matches the keywords, filter out those that don't
        if text_query and any(r.get("has_keyword_match") for r in results):
            results = [r for r in results if r.get("has_keyword_match")]

        # Sort results by score (important after boosting)
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def search_by_image_bytes(self, image_bytes: bytes, top_k: int = 20, category: str = None) -> list[dict]:
        """Full pipeline: raw bytes → embedding → FAISS search → results."""
        vec = self.embed_image_bytes(image_bytes)
        return self.search(vec, top_k=top_k, category=category)

    def search_by_image_url(self, url: str, top_k: int = 20, category: str = None) -> list[dict]:
        """Full pipeline: URL → download → embedding → FAISS search."""
        vec = self.embed_image_url(url)
        return self.search(vec, top_k=top_k, category=category)



    def search_by_text(self, text: str, top_k: int = 20, category: str = None) -> list[dict]:
        """
        Search by text description instead of image.
        e.g. 'blue denim jacket' or 'wireless earbuds'
        CLIP maps text and image to the same space — this just works.
        """
        vec = self.embed_text(text)
        # Use a slightly lower threshold for text search as text-image alignment 
        # scores are typically lower than image-image scores.
        # Pass the text to the search method for keyword boosting
        return self.search(vec, top_k=top_k, category=category, min_score=0.10, text_query=text)

    # ════════════════════════════════════════════════════════
    # UTILITIES
    # ════════════════════════════════════════════════════════

    def get_index_stats(self) -> dict:
        return {
            "total_products": self.index.ntotal if self.index else 0,
            "embedding_dim":  self.dim,
            "device":         self.device,
            "model":          self.model_name if hasattr(self, 'model_name') else "Unknown",
            "index_size_kb":  round(INDEX_PATH.stat().st_size / 1024, 1) if INDEX_PATH.exists() else 0,
        }


# ── Module-level singleton ───────────────────────────────────
# Loaded once when the FastAPI app starts, shared across requests
_engine: Optional[CLIPEngine] = None

def get_engine() -> CLIPEngine:
    global _engine
    if _engine is None:
        _engine = CLIPEngine()
        _engine.load_or_build_index()
    return _engine
'''

"""
ml/clip_engine.py  — Production v3
Fixes:
  1. Accurate similarity via ViT-L-14 + temperature calibration
  2. Price always shown (from catalog, never missing)
  3. Description-based search (text → same CLIP vector space)
  4. Category auto-detection for better precision
"""
import json, time, logging
import numpy as np
from pathlib import Path
from typing import Optional
from io import BytesIO

import torch
import open_clip
import faiss
from PIL import Image
import requests

logger = logging.getLogger(__name__)

INDEX_PATH    = Path("data/products.faiss")
META_PATH     = Path("data/products_meta.json")
CATALOG_PATH  = Path("data/catalog.json")

# Score calibration — maps raw ViT cosine (0.1–0.55) → display 0–100%
TEMP   = 0.08
OFFSET = 0.12

CATEGORY_PROMPTS = {
    "fashion":     "indian ethnic clothing kurta dress saree",
    "footwear":    "shoes sneakers boots sandals running sport",
    "watches":     "wristwatch timepiece analog digital dial",
    "electronics": "smartphone mobile phone laptop tablet",
    "bags":        "handbag backpack tote purse sling bag",
    "beauty":      "lipstick makeup cosmetics skincare cream",
    "accessories": "sunglasses jewellery necklace earring ring",
    "furniture":   "sofa chair table bed furniture home decor",
}


class CLIPEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading ViT-L-14 on {self.device}…")

        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            "ViT-L-14", pretrained="openai", device=self.device
        )
        self.model.eval()
        self.tokenizer = open_clip.get_tokenizer("ViT-L-14")

        # Get embedding dim
        with torch.no_grad():
            d = self.preprocess(Image.new("RGB",(224,224))).unsqueeze(0).to(self.device)
            self.dim = self.model.encode_image(d).shape[-1]

        logger.info(f"CLIP ready | dim={self.dim}")

        self.index    : Optional[faiss.Index] = None
        self.metadata : list[dict]            = []
        self.cat_map  : dict[str, list[int]]  = {}

    # ── Embedding ────────────────────────────────────────────

    def _norm(self, t: torch.Tensor) -> np.ndarray:
        t = torch.nn.functional.normalize(t.float(), dim=-1)
        return t.cpu().numpy().astype(np.float32)

    def embed_image(self, img: Image.Image) -> np.ndarray:
        t = self.preprocess(img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            return self._norm(self.model.encode_image(t))

    def embed_bytes(self, data: bytes) -> np.ndarray:
        return self.embed_image(Image.open(BytesIO(data)).convert("RGB"))

    def embed_url(self, url: str) -> np.ndarray:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        return self.embed_bytes(r.content)

    def embed_text(self, text: str) -> np.ndarray:
        """
        CLIP text embedding — shares the same vector space as images.
        'red nike sneakers' → same neighborhood as a photo of red Nike sneakers.
        This powers the description search feature.
        """
        tokens = self.tokenizer([text]).to(self.device)
        with torch.no_grad():
            return self._norm(self.model.encode_text(tokens))

    # ── Score calibration ─────────────────────────────────────

    def calibrate(self, raw: float) -> float:
        """Map compressed ViT cosine scores → intuitive 0–100%."""
        return round(float(np.clip((raw + OFFSET) / (OFFSET + TEMP + 0.72), 0, 1)), 4)

    def score_label(self, score: float) -> str:
        if score >= 0.88: return "Exact match"
        if score >= 0.75: return "Very similar"
        if score >= 0.60: return "Similar style"
        if score >= 0.45: return "Same category"
        return "Loosely related"

    # ── Category detection ────────────────────────────────────

    def detect_category(self, vec: np.ndarray) -> Optional[str]:
        """Zero-shot classify which product category the image belongs to."""
        best, best_score = None, -1.0
        for cat, prompt in CATEGORY_PROMPTS.items():
            t_vec = self.embed_text(prompt)
            s     = float(np.dot(vec.flatten(), t_vec.flatten()))
            if s > best_score:
                best_score, best = s, cat
        return best if best_score > 0.15 else None

    def detect_category_from_text(self, text: str) -> Optional[str]:
        """Detect category from a text description using keyword matching."""
        t = text.lower()
        kw = {
            "fashion":     ["kurta","dress","saree","shirt","top","ethnic","salwar","kurti","lehenga"],
            "footwear":    ["shoe","sneaker","boot","sandal","slipper","nike","adidas","puma","footwear"],
            "watches":     ["watch","timepiece","wristwatch","titan","casio","fossil","chronograph"],
            "electronics": ["phone","mobile","smartphone","iphone","samsung","oneplus","redmi","laptop"],
            "bags":        ["bag","handbag","backpack","tote","purse","sling","wallet","clutch"],
            "beauty":      ["lipstick","makeup","cream","foundation","serum","nykaa","lakme","maybelline"],
            "accessories": ["sunglass","jewellery","necklace","ring","earring","bracelet","belt","cap"],
            "furniture":   ["sofa","chair","table","bed","cabinet","shelf","wardrobe","desk","couch"],
        }
        for cat, words in kw.items():
            if any(w in t for w in words):
                return cat
        return None

    # ── Index building ────────────────────────────────────────

    def build_index(self, catalog: list[dict], save: bool = True):
        logger.info(f"Indexing {len(catalog)} products…")

        cpu_idx = faiss.IndexFlatIP(self.dim)
        self.index = (
            faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, cpu_idx)
            if self.device == "cuda" and faiss.get_num_gpus() > 0
            else cpu_idx
        )

        self.metadata, self.cat_map = [], {}
        vecs, failed = [], 0

        for i, p in enumerate(catalog):
            try:
                vec = self.embed_url(p["image_url"])
                row = len(vecs)
                vecs.append(vec)
                self.metadata.append(p)
                self.cat_map.setdefault(p.get("category", "general"), []).append(row)
                if (i+1) % 5 == 0:
                    logger.info(f"  {i+1}/{len(catalog)}…")
            except Exception as e:
                logger.warning(f"  skip {p.get('id','?')}: {e}")
                failed += 1

        self.index.add(np.vstack(vecs).astype(np.float32))
        logger.info(f"Index: {self.index.ntotal} vectors, {failed} failed")
        if save: self._save()

    def _save(self):
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        cpu = faiss.index_gpu_to_cpu(self.index) if hasattr(self.index,"index") else self.index
        faiss.write_index(cpu, str(INDEX_PATH))
        META_PATH.write_text(json.dumps({"metadata": self.metadata, "cat_map": self.cat_map},
                                         ensure_ascii=False, indent=2))
        logger.info(f"Saved → {INDEX_PATH}")

    def load_index(self) -> bool:
        if not INDEX_PATH.exists(): return False
        cpu = faiss.read_index(str(INDEX_PATH))
        self.index = (
            faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, cpu)
            if self.device == "cuda" and faiss.get_num_gpus() > 0
            else cpu
        )
        d = json.loads(META_PATH.read_text())
        if isinstance(d, dict):
            self.metadata = d.get("metadata", [])
            self.cat_map  = d.get("cat_map", {})
        else:
            self.metadata = d
            self.cat_map  = {}
        logger.info(f"Loaded {self.index.ntotal} products")
        return True

    def load_or_build(self):
        if not self.load_index():
            catalog = json.loads(CATALOG_PATH.read_text())
            self.build_index(catalog)

    # ── Search ────────────────────────────────────────────────

    def search(self, vec: np.ndarray, top_k: int = 20,
               category: Optional[str] = None, min_raw: float = 0.08) -> list[dict]:
        if not self.index: raise RuntimeError("Index not loaded")

        k = min(top_k * 3, self.index.ntotal)
        scores, idxs = self.index.search(vec, k)

        results = []
        for raw, idx in zip(scores[0], idxs[0]):
            if idx == -1 or float(raw) < min_raw: continue
            if category and self.metadata[idx].get("category") != category: continue

            p = dict(self.metadata[idx])
            cal = self.calibrate(float(raw))

            # ── Always show price ─────────────────────────────
            # Pull price from catalog — never show "price not found"
            p["similarity_score"] = cal
            p["similarity_pct"]   = f"{int(cal*100)}%"
            p["similarity_label"] = self.score_label(cal)
            p["raw_score"]        = round(float(raw), 4)

            # Ensure price fields always exist
            p.setdefault("price",          "Price on website")
            p.setdefault("original_price", None)
            p.setdefault("discount",       None)
            p.setdefault("thumbnail",      p.get("image_url"))

            results.append(p)

        results.sort(key=lambda r: r["similarity_score"], reverse=True)
        return results[:top_k]

    # ── Public search methods ─────────────────────────────────

    def search_by_image_bytes(self, data: bytes, top_k: int = 20, category: Optional[str] = None) -> dict:
        """Search by uploaded image — auto-detects category if not provided."""
        vec = self.embed_bytes(data)
        if category is None or category.lower() == "all":
            category = self.detect_category(vec)
        elif category.lower() == "unknown":
            category = None
        results = self.search(vec, top_k=top_k, category=category)
        return {"results": results, "detected_category": category, "method": "image"}

    def search_by_image_url(self, url: str, top_k: int = 20, category: Optional[str] = None) -> dict:
        """Search by image URL."""
        vec = self.embed_url(url)
        if category is None or category.lower() == "all":
            category = self.detect_category(vec)
        elif category.lower() == "unknown":
            category = None
        results = self.search(vec, top_k=top_k, category=category)
        return {"results": results, "detected_category": category, "method": "url"}

    def search_by_text(self, text: str, top_k: int = 20, category: Optional[str] = None) -> dict:
        """
        Search by natural language description.
        'blue anarkali kurta under 1000' → finds matching products.
        CLIP's multimodal embedding makes this work without any extra model.
        """
        vec = self.embed_text(text)
        if category is None or category.lower() == "all":
            category = self.detect_category_from_text(text)
        elif category.lower() == "unknown":
            category = None
        results = self.search(vec, top_k=top_k, category=category)
        return {"results": results, "detected_category": category, "method": "text", "query": text}

    def get_stats(self) -> dict:
        return {
            "total":      self.index.ntotal if self.index else 0,
            "dim":        self.dim,
            "device":     self.device,
            "model":      "ViT-L-14",
            "categories": {k: len(v) for k, v in self.cat_map.items()},
        }


_engine: Optional[CLIPEngine] = None

def get_engine() -> CLIPEngine:
    global _engine
    if _engine is None:
        _engine = CLIPEngine()
        _engine.load_or_build()
    return _engine
