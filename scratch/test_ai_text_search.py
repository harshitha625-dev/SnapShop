import asyncio
import sys
import os

sys.path.insert(0, ".")

# Load backend/.env manually for testing API keys
if os.path.exists("backend/.env"):
    with open("backend/.env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

# Fix for windows event loop warning
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.routers.search import search_by_text
from backend.models.schemas import TextSearchRequest

async def run_tests():
    test_queries = [
        "OMG guys look at this beautiful floral printed blue ethnic women's kurta with palace pants set! It is pure cotton, perfect for summer wedding wear.",
        "Hey! Can you find me white running shoes? I need them for athletic training, preferably Nike or Adidas.",
        "pasted: Daniel Wellington Classic Petite 32mm watch for women, analog silver dial, brand new in box with warranty"
    ]
    
    for idx, q in enumerate(test_queries):
        print(f"\n======================================")
        print(f"TEST CASE {idx+1}: '{q[:60]}...'")
        print(f"======================================")
        payload = TextSearchRequest(query=q, max_results=3)
        try:
            resp = await search_by_text(payload)
            print(f"Search ID: {resp.search_id}")
            print(f"Total results: {resp.total_results}")
            
            print("\nTop 3 Matches:")
            for i, match in enumerate(resp.visual_matches[:3]):
                price_display = str(match.price).replace("₹", "Rs.")
                print(f"  {i+1}. {match.title}")
                print(f"     Platform: {match.source} | Price: {price_display}")
                print(f"     Similarity: {match.similarity_score}")
        except Exception as e:
            print(f"Test case failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())
