#!/usr/bin/env python3
"""
scripts/build_index.py
==============================================================
Run this ONCE before starting the backend server.
It downloads product images, embeds them with CLIP,
and saves the FAISS index to data/products.faiss

Usage:
    cd snapshop-ml
    python scripts/build_index.py

    # Add more products:
    python scripts/build_index.py --catalog data/my_catalog.json

    # Force rebuild even if index exists:
    python scripts/build_index.py --force
"""
print("SCRIPT STARTED")
import sys, time, json, argparse
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)

from ml.clip_engine import CLIPEngine
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="data/catalog.json")
    parser.add_argument("--force",   action="store_true", help="Rebuild even if index exists")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  SnapShap — CLIP + FAISS Index Builder")
    print("="*60 + "\n")

    # Check if index already exists
    from pathlib import Path
    if Path("data/products.faiss").exists() and not args.force:
        print("✅ Index already exists at data/products.faiss")
        print("   Use --force to rebuild it.\n")

        # Show stats
        engine = CLIPEngine()
        engine.load_index()
        stats = engine.get_index_stats()
        print(f"   Products indexed : {stats['total_products']}")
        print(f"   Embedding dim    : {stats['embedding_dim']}")
        print(f"   Device           : {stats['device']}")
        print(f"   Index size       : {stats['index_size_kb']} KB\n")
        return

    # Load catalog
    print(f"📋 Loading catalog from {args.catalog}…")
    with open(args.catalog) as f:
        catalog = json.load(f)
    print(f"   Found {len(catalog)} products\n")

    # Show catalog preview
    cats = {}
    for p in catalog:
        cats[p.get("category","?")] = cats.get(p.get("category","?"),0) + 1
    print("   Categories:")
    for cat, count in sorted(cats.items()):
        print(f"     {cat:20s} {count} products")
    print()

    # Build index
    print("🧠 Loading CLIP model…")
    engine = CLIPEngine()

    print(f"   Device: {engine.device}")
    print(f"   Dim:    {engine.dim}")
    print()

    print("🔍 Embedding products with CLIP…")
    print("   (This downloads each product image and runs it through the neural network)\n")

    t = time.time()
    engine.build_index(catalog, save=True)
    elapsed = time.time() - t

    print()
    print("="*60)
    print("✅  Index built successfully!")
    print(f"   Products indexed : {engine.index.ntotal}")
    print(f"   Time taken       : {elapsed:.1f}s")
    print(f"   Avg per product  : {elapsed/len(catalog)*1000:.0f}ms")
    print(f"   Saved to         : data/products.faiss")
    print()
    print("Next step: start the server")
    print("  uvicorn backend.main:app --reload")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
