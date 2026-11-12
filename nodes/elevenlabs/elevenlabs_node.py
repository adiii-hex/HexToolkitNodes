# Tests that the ElevenLabs API key works. Listing voices uses no credits.
import json
from pathlib import Path

import requests

KEYS_FILE = Path(__file__).resolve().parents[2] / "keys" / "keys.json"
api_key = json.loads(KEYS_FILE.read_text()).get("elevenlabs_key")

response = requests.get(
    "https://api.elevenlabs.io/v1/voices",
    headers={"xi-api-key": api_key},
    timeout=30,
)

if response.ok:
    print("ElevenLabs API works")
    print(f"{len(response.json()['voices'])} voices available")
else:
    print(f"ElevenLabs API failed ({response.status_code}): {response.text[:200]}")
