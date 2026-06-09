import requests
import json

url = "http://127.0.0.1:8000/api/search/text"
payload = {
    "query": "Nike",
    "category": "footwear"
}

resp = requests.post(url, json=payload)
print(f"Status: {resp.status_code}")
data = resp.json()

print(f"Total results: {data['total_results']}")
for res in data['visual_matches']:
    print(f"- {res['title']} | Category: {res['category']} | Score: {res['similarity_score']}")

payload_all = {
    "query": "Nike",
    "category": "All"
}
resp_all = requests.post(url, json=payload_all)
print(f"\nStatus (All): {resp_all.status_code}")
data_all = resp_all.json()
print(f"Total results (All): {data_all['total_results']}")
