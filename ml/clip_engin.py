"""
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

    def __init__(self, model_name: str = "ViT-B-32", pretrained: str = "openai"):
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

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            model_name,
            pretrained=pretrained,
            device=self.device,
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
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        return self.embed_image_bytes(resp.content)

    def _embed_pil(self, img: Image.Image) -> np.ndarray:
        """Core embedding function."""
        tensor = self.preprocess(img).unsqueeze(0).to(self.device)

        with torch.no_grad():
            emb = self.model.encode_image(tensor).float()

            # L2 normalize → cosine similarity becomes dot product
            # This makes FAISS IndexFlatIP equivalent to cosine similarity
            emb = emb / emb.norm(dim=-1, keepdim=True)

        return emb.cpu().numpy().astype(np.float32)

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a text query (e.g. 'red sneakers') into the same vector space.
        This is CLIP's superpower — image and text share one embedding space.
        """
        tokenizer = open_clip.get_tokenizer("ViT-B-32")
        tokens    = tokenizer([text]).to(self.device)

        with torch.no_grad():
            emb = self.model.encode_text(tokens).float()
            emb = emb / emb.norm(dim=-1, keepdim=True)

        return emb.cpu().numpy().astype(np.float32)

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
                emb = self.embed_image_url(product["image_url"])
                embeddings.append(emb)
                self.metadata.append(product)
                if (i + 1) % 10 == 0:
                    logger.info(f"  Indexed {i+1}/{len(catalog)} products…")

            except Exception as e:
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
        min_score    : float = 0.20,   # cosine similarity floor
    ) -> list[dict]:
        """
        Core ANN search.

        Args:
            query_vector: normalized 512-dim float32 array (1 × dim)
            top_k:        how many results to return
            min_score:    discard results below this cosine similarity
                          (0.0 = everything, 1.0 = exact match only)
                          0.20 is generous — tightened in production

        Returns:
            List of product dicts with added 'similarity_score' field.

        How it works:
            FAISS computes dot-product between query and every indexed vector.
            Since all vectors are L2-normalized, dot-product == cosine similarity.
            Higher score = more visually similar.

            Score interpretation:
              > 0.85  same product, different photo
              0.65-0.85  same category, similar style
              0.40-0.65  related category
              < 0.40   probably unrelated
        """
        if self.index is None or self.index.ntotal == 0:
            raise RuntimeError("Index not loaded. Call load_or_build_index() first.")

        k = min(top_k, self.index.ntotal)

        # FAISS search — returns (scores, indices) both shape (1, k)
        scores, indices = self.index.search(query_vector, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:              # FAISS padding for empty slots
                continue
            if float(score) < min_score:
                continue
            product = dict(self.metadata[idx])
            product["similarity_score"] = round(float(score), 4)
            results.append(product)

        return results

    def search_by_image_bytes(self, image_bytes: bytes, top_k: int = 20) -> list[dict]:
        """Full pipeline: raw bytes → embedding → FAISS search → results."""
        vec = self.embed_image_bytes(image_bytes)
        return self.search(vec, top_k=top_k)

    def search_by_image_url(self, url: str, top_k: int = 20) -> list[dict]:
        """Full pipeline: URL → download → embedding → FAISS search."""
        vec = self.embed_image_url(url)
        return self.search(vec, top_k=top_k)

    def search_by_text(self, text: str, top_k: int = 20) -> list[dict]:
        """
        Search by text description instead of image.
        e.g. 'blue denim jacket' or 'wireless earbuds'
        CLIP maps text and image to the same space — this just works.
        """
        vec = self.embed_text(text)
        return self.search(vec, top_k=top_k)

    # ════════════════════════════════════════════════════════
    # UTILITIES
    # ════════════════════════════════════════════════════════

    def get_index_stats(self) -> dict:
        return {
            "total_products": self.index.ntotal if self.index else 0,
            "embedding_dim":  self.dim,
            "device":         self.device,
            "model":          "ViT-B-32",
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
