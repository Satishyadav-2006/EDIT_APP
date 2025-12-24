import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "phi3:mini",
    "prompt": "Hello",
    "stream": False,
    "options": {
        "temperature": 0.0,
        "num_predict": 220,
        "stop": ["User:"]
    }
}

try:
    print(f"Sending request to {url} with payload: {payload}")
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    response.raise_for_status()
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
