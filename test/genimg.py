import os
import base64
import requests

api_key = os.environ["OPENAI_API_KEY"]

url = "https://api.openai.com/v1/responses"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

payload = {
    "model": "dall-e-3",
    "input": "Generate an image of gray tabby cat hugging an otter with an orange scarf",
    "tools": [
        {
            "type": "image_generation"
        }
    ],
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
)

response.raise_for_status()

data = response.json()

# Cerca il risultato della generazione immagine
image_base64 = None

for output in data["output"]:
    if output["type"] == "image_generation_call":
        image_base64 = output["result"]
        break

if image_base64:
    with open("otter.png", "wb") as f:
        f.write(base64.b64decode(image_base64))

    print("Immagine salvata in otter.png")
else:
    print("Nessuna immagine generata")
