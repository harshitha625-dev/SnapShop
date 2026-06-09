#!/usr/bin/env python3
"""
scripts/test_search.py
══════════════════════════════════════════════════════════════
Test the CLIP + FAISS search pipeline end-to-end.
Run this after build_index.py to confirm everything works.

Usage:
    python scripts/test_search.py

    # Test with your own image:
    python scripts/test_search.py --image path/to/shoe.jpg

    # Test with a URL:
    python scripts/test_search.py --url https://example.com/product.jpg

    # Test text search (CLIP superpower):
    python scripts/test_search.py --text "red sneakers nike"
"""

import sys, argparse
sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.WARNING)

from ml.clip_engine import CLIPEngine

TEST_URLS = {
    "sneaker": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400",
    "watch":   "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400",
    "dress":   "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400",
    "phone":   "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400",
    "bag":     "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=400",
}

def print_results(results: list, query: str):
    print(f"\n{'═'*55}")
    print(f"  Query: {query}")
    print(f"  Results: {len(results)} found")
    print(f"{'═'*55}")

    if not results:
        print("  ❌ No results found above similarity threshold")
        return

    for i, r in enumerate(results[:5], 1):
        score   = r.get("similarity_score", 0)
        bar_len = int(score * 20)
        bar     = "█" * bar_len + "░" * (20 - bar_len)

        print(f"\n  #{i} [{bar}] {score:.3f}")
        print(f"     {r['title'][:50]}")
        print(f"     {r['platform']:15s} {r['price']:10s}  ★{r.get('rating','?')}")
        print(f"     Category: {r.get('category','?')}")

    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="Path to local image file")
    parser.add_argument("--url",   help="Image URL to search")
    parser.add_argument("--text",  help="Text query (CLIP text→image search)")
    parser.add_argument("--all",   action="store_true", help="Run all test URLs")
    args = parser.parse_args()

    print("\n" + "═"*55)
    print("  SnapShop — CLIP + FAISS Search Test")
    print("═"*55)

    print("\n🧠 Loading CLIP model + FAISS index…")
    engine = CLIPEngine()
    if not engine.load_index():
        print("\n❌ No index found! Run this first:")
        print("   python scripts/build_index.py\n")
        sys.exit(1)

    stats = engine.get_index_stats()
    print(f"✅ Index loaded: {stats['total_products']} products | {stats['device']}\n")

    if args.image:
        print(f"📸 Searching by image file: {args.image}")
        results = engine.search(engine.embed_image_file(args.image), top_k=10)
        print_results(results, args.image)

    elif args.url:
        print(f"🌐 Searching by URL: {args.url[:60]}…")
        results = engine.search_by_image_url(args.url, top_k=10)
        print_results(results, args.url)

    elif args.text:
        print(f"📝 Text search: '{args.text}'")
        results = engine.search_by_text(args.text, top_k=10)
        print_results(results, args.text)

    else:
        # Run all test cases
        print("Running all test cases…\n")
        for name, url in TEST_URLS.items():
            print(f"📸 Testing: {name}")
            try:
                results = engine.search_by_image_url(url, top_k=5)
                print_results(results, f"{name} ({url[:40]}…)")
            except Exception as e:
                print(f"  ❌ Failed: {e}\n")

    print("Test complete ✅\n")


if __name__ == "__main__":
    main()
