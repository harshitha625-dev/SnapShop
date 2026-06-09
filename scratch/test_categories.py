import requests

url = "http://127.0.0.1:8000/api/search/text"

# 1. Search All
r1 = requests.post(url, json={"query": "Nike", "category": "All"})
print(f"All: {r1.json()['total_results']} results")

# 2. Search Watches (should be 0 or different)
r2 = requests.post(url, json={"query": "Nike", "category": "watches"})
print(f"Watches: {r2.json()['total_results']} results")

# 3. Search Footwear
r3 = requests.post(url, json={"query": "Nike", "category": "footwear"})
print(f"Footwear: {r3.json()['total_results']} results")
