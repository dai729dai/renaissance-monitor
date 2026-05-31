import requests
import os

webhook = os.environ["DISCORD_WEBHOOK"]

response = requests.post(
    webhook,
    json={
        "content": "GitHub Monitor Test"
    },
    timeout=30
)

print("Status:", response.status_code)
