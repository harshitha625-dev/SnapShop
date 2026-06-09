
import requests
import json

def test_api():
    url = "http://localhost:8000/api/search/text"
    payload = {
        "query": "nike shoes",
        "max_results": 5
    }
    try:
        resp = requests.post(url, json=payload)
        print(f"Status: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
