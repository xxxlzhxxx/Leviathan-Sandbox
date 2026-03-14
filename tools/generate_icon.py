import os
import requests
from openai import OpenAI
from pathlib import Path

API_KEY = os.environ.get("ARK_API_KEY", "31a38e5c-8245-40ba-acf5-145bdf4be9ad")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
SEEDREAM_MODEL = "ep-20260228143218-zwr4g"

def generate_icon():
    if not API_KEY:
        print("Please set ARK_API_KEY environment variable.")
        return

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    prompt = "App icon for a retro pixel art RTS game named Leviathan Sandbox, featuring a medieval castle and pixel knights battling, side view, vibrant colors, clean thick outline, high quality, 2D game asset, white background"
    
    print("Generating icon with Seedream...")
    try:
        response = client.images.generate(
            model=SEEDREAM_MODEL,
            prompt=prompt,
            size="2048x2048",
            n=1
        )
        url = response.data[0].url
        print(f"Icon generated! Downloading from {url}...")
        
        data = requests.get(url).content
        
        # Save to root or web/assets
        output_path = Path("logo.png")
        with open(output_path, "wb") as f:
            f.write(data)
            
        print(f"Icon saved to {output_path.absolute()}")
        
    except Exception as e:
        print(f"Failed to generate icon: {e}")

if __name__ == "__main__":
    generate_icon()
