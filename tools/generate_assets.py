import os
import yaml
from openai import OpenAI
import requests
from pathlib import Path

# Load API Key
def load_api_key():
    try:
        with open("strategies/volc_attack.yaml", "r") as f:
            data = yaml.safe_load(f)
            return data.get("api_key")
    except Exception as e:
        print(f"Error loading API key: {e}")
        return None

api_key = load_api_key()
if not api_key:
    print("API Key not found in strategies/volc_attack.yaml")
    exit(1)

# Initialize Client
# Correct Seedream Endpoint ID from LLM_env.md
SEEDREAM_ENDPOINT = "ep-20260228143218-zwr4g"

client = OpenAI(
    api_key=api_key,
    base_url="https://ark.cn-beijing.volces.com/api/v3",
)

# Units to generate
units = {
    "knight": "A pixel art sprite of a medieval knight in armor, side view, 2d game asset, white background, retro style",
    "archer": "A pixel art sprite of an archer with a bow, side view, 2d game asset, white background, retro style",
    "goblin": "A pixel art sprite of a green goblin with a dagger, side view, 2d game asset, white background, retro style",
    "orc": "A pixel art sprite of a fierce orc warrior with an axe, side view, 2d game asset, white background, retro style",
    "catapult": "A pixel art sprite of a wooden catapult siege engine, side view, 2d game asset, white background, retro style",
    "wall": "A pixel art sprite of a stone wall section, isometric or side view, 2d game asset, white background, retro style",
    "turret": "A pixel art sprite of a defensive turret tower, side view, 2d game asset, white background, retro style",
    "base": "A pixel art sprite of a main castle base or command center, side view, 2d game asset, white background, retro style"
}

# Output directories
# We will save to both web/assets and core/objects/...
web_assets_dir = Path("web/assets")
web_assets_dir.mkdir(parents=True, exist_ok=True)

# Helper to save image
def save_image(img_data, unit_name):
    # Save to web/assets
    with open(web_assets_dir / f"{unit_name}.png", "wb") as f:
        f.write(img_data)
    print(f"  -> Saved to web/assets/{unit_name}.png")
    
    # Save to core/objects/{name}/assets/sprite.png
    obj_assets_dir = Path(f"leviathan_sandbox/core/objects/{unit_name}/assets")
    obj_assets_dir.mkdir(parents=True, exist_ok=True)
    with open(obj_assets_dir / "sprite.png", "wb") as f:
        f.write(img_data)
    print(f"  -> Saved to {obj_assets_dir}/sprite.png")

print(f"Generating REAL assets for {len(units)} units using Seedream ({SEEDREAM_ENDPOINT})...")

for name, prompt in units.items():
    print(f"Generating {name}...")
    try:
        response = client.images.generate(
            model=SEEDREAM_ENDPOINT,
            prompt=prompt,
            size="2048x2048", # Correct size for Seedream (minimum 3.6M pixels)
            n=1
        )
        
        image_url = response.data[0].url
        print(f"  -> Generated: {image_url}")
        
        # Download image
        img_data = requests.get(image_url).content
        save_image(img_data, name)
        
    except Exception as e:
        print(f"  -> Error generating {name}: {e}")
