import sys
import os
sys.path.insert(0, ".")
from ml.clip_engine import get_engine

engine = get_engine()
# Same image, different resolution/quality
url1 = 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80'
url2 = 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=200&q=50'

res1 = engine.search_by_image_url(url1).get("results", [])
res2 = engine.search_by_image_url(url2).get("results", [])

if res1:
    print(f"URL 1 (400px) Top Match: {res1[0]['title']} | Score: {res1[0]['similarity_score']}")
if res2:
    print(f"URL 2 (200px) Top Match: {res2[0]['title']} | Score: {res2[0]['similarity_score']}")

# Text search "Nike shoe"
res_text = engine.search_by_text("Nike shoe").get("results", [])
if res_text:
    print(f"\nText 'Nike shoe' Top Match: {res_text[0]['title']} | Score: {res_text[0]['similarity_score']}")
