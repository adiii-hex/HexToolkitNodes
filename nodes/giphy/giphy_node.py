# Tests that the Giphy API key works.
import json
from pathlib import Path

import requests

KEYS_FILE = Path(__file__).resolve().parents[2] / "keys" / "keys.json"
api_key = json.loads(KEYS_FILE.read_text()).get("giphy_key")

response = requests.get(
    "https://api.giphy.com/v1/gifs/search",
    params={"api_key": api_key, "q": "test", "limit": 1},
    timeout=30,
)

if response.ok:
    print("Giphy API works")
    print(response.json()["data"][0]["url"])
else:
    print(f"Giphy API failed ({response.status_code}): {response.text[:200]}")
