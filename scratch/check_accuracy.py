from ml.clip_engine import get_engine
import json

engine = get_engine()

# Test Case 1: Search by the EXACT image of the Nike shoe
img_url = "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&q=80"
print(f"\n--- Testing Image Search for: {img_url} ---")
results = engine.search_by_image_url(img_url)
if results:
    for i, res in enumerate(results[:3]):
        print(f"{i+1}. {res['title']} | Score: {res['similarity_score']}")

# Test Case 2: Search by the EXACT image of the Roadster dress
img_url_dress = "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=400&q=80"
print(f"\n--- Testing Image Search for: {img_url_dress} ---")
results_dress = engine.search_by_image_url(img_url_dress)
if results_dress:
    for i, res in enumerate(results_dress[:3]):
        print(f"{i+1}. {res['title']} | Score: {res['similarity_score']}")

# Test Case 3: Search by text "Floral dress"
print("\n--- Testing Text Search for: 'Floral dress' ---")
results_text = engine.search_by_text("Floral dress")
if results_text:
    for i, res in enumerate(results_text[:3]):
        print(f"{i+1}. {res['title']} | Score: {res['similarity_score']}")
else:
    print("No results found with default min_score. Checking raw scores...")
    # Get raw scores without min_score filter
    vec = engine.embed_text("Floral dress")
    raw_results = engine.search(vec, top_k=3, min_score=0.0)
    for i, res in enumerate(raw_results):
        print(f"{i+1}. {res['title']} | Score: {res['similarity_score']}")
