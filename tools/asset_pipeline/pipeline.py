import os
import yaml
import requests
import time
from openai import OpenAI
from volcenginesdkarkruntime import Ark
from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance
import numpy as np
import concurrent.futures
import cv2
from rembg import remove

# Configuration
CONFIG_PATH = Path("tools/asset_pipeline/config.yaml")
OUTPUT_BASE = Path("web/assets_animated")

# API Config (From LLM_env.md)
SEEDREAM_MODEL = "ep-20260228143218-zwr4g"
SEEDANCE_MODEL = "ep-20260314095139-4m4kq" # Seedance 1.5
API_KEY = os.environ.get("ARK_API_KEY", "31a38e5c-8245-40ba-acf5-145bdf4be9ad")
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def init_openai_client():
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)

def init_ark_client():
    return Ark(api_key=API_KEY, base_url=BASE_URL)

def generate_image(client, prompt, filename):
    if filename.exists():
        print(f"  [Seedream] Reusing/Generating image for: {filename.name}...")
    
    print(f"  [Seedream] Generating image for: {filename.name}...")
    try:
        response = client.images.generate(
            model=SEEDREAM_MODEL,
            prompt=prompt,
            size="2048x2048", 
            n=1
        )
        url = response.data[0].url
        data = requests.get(url).content
        with open(filename, "wb") as f:
            f.write(data)
        return url 
    except Exception as e:
        print(f"  [Error] Seedream failed for {filename.name}: {e}")
        return None

def generate_video(ark_client, prompt, image_url, filename_video):
    if filename_video.exists():
        print(f"  [Skip] Video exists: {filename_video.name}")
        return True

    print(f"  [Seedance] Generating video for: {filename_video.name}...")
    try:
        print(f"    -> Creating task for {filename_video.name}...")
        create_result = ark_client.content_generation.tasks.create(
            model=SEEDANCE_MODEL,
            content=[
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ],
            ratio="1:1", 
        )
        
        task_id = create_result.id
        print(f"    -> Task ID: {task_id}")
        
        # Polling
        start_time = time.time()
        last_log_time = start_time
        while True:
            if time.time() - start_time > 900: # 15 min timeout
                print(f"    -> Timeout waiting for {filename_video.name}")
                return False
            
            if time.time() - last_log_time > 30:
                print(f"    -> Still waiting for {filename_video.name} (Task: {task_id})...")
                last_log_time = time.time()
                
            get_result = ark_client.content_generation.tasks.get(task_id=task_id)
            status = get_result.status
            
            if status == "succeeded":
                print(f"    -> Task {task_id} succeeded!")
                if hasattr(get_result, 'content') and get_result.content:
                     if hasattr(get_result.content, 'video_url'):
                         video_url = get_result.content.video_url
                         data = requests.get(video_url).content
                         with open(filename_video, "wb") as f:
                             f.write(data)
                         return True
                     elif isinstance(get_result.content, list) and len(get_result.content) > 0:
                         video_url = get_result.content[0].video_source.url
                         data = requests.get(video_url).content
                         with open(filename_video, "wb") as f:
                             f.write(data)
                         return True
                     else:
                         print(f"    -> Error: Unexpected content structure.")
                         return False
                else:
                    print(f"    -> Error: No content in success response.")
                    return False
            elif status == "failed":
                print(f"    -> Task {task_id} failed: {get_result.error}")
                return False
            else:
                time.sleep(5) 
                
    except Exception as e:
        print(f"  [Error] Seedance failed for {filename_video.name}: {e}")
        return False

def video_to_spritesheet(video_path, output_path, num_frames=8, target_size=(128, 128)):
    print(f"  [Processing] Creating Sprite Sheet from {video_path.name}...")
    try:
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
        
        frames = []
        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret: break
            if i in indices:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize(target_size)
                img = remove(img)
                frames.append(img)
        
        cap.release()
        
        sheet_width = target_size[0] * len(frames)
        sheet_height = target_size[1]
        sheet = Image.new("RGBA", (sheet_width, sheet_height))
        
        for idx, frame in enumerate(frames):
            sheet.paste(frame, (idx * target_size[0], 0))
            
        sheet.save(output_path)
        print(f"  [Success] Saved Sprite Sheet: {output_path}")
        return True
        
    except Exception as e:
        print(f"  [Error] Sprite Sheet creation failed: {e}")
        return False

def create_variants(sheet_path, name, suffix=""):
    print(f"  [Processing] Creating variants for {name} {suffix}...")
    
    blue_path = OUTPUT_BASE / f"{name}{suffix}_blue.png"
    red_path = OUTPUT_BASE / f"{name}{suffix}_red.png"
    
    try:
        img = Image.open(sheet_path).convert("RGBA")
        
        width, height = img.size
        frame_width = 128
        num_frames = width // frame_width
        
        # Blue (No Flip - Original Orientation - Facing Right)
        img.save(blue_path)
        
        # Red (Flip Horizontal - Facing Left + Tint)
        red_sheet = Image.new("RGBA", (width, height))
        for i in range(num_frames):
            frame = img.crop((i * frame_width, 0, (i + 1) * frame_width, height))
            # Flip frame
            frame_flipped = ImageOps.mirror(frame)
            # Tint frame (Reddish)
            r, g, b, a = frame_flipped.split()
            r = r.point(lambda i: i * 1.2)
            g = g.point(lambda i: i * 0.8)
            b = b.point(lambda i: i * 0.8)
            frame_tinted = Image.merge("RGBA", (r, g, b, a))
            red_sheet.paste(frame_tinted, (i * frame_width, 0))
        red_sheet.save(red_path)
        
    except Exception as e:
        print(f"  [Error] Variant creation failed: {e}")

def process_unit_pipeline(unit, data, openai_client, ark_client):
    # Paths
    base_img_path = OUTPUT_BASE / f"{unit}_base.png"
    
    video_move_path = OUTPUT_BASE / f"{unit}_move.mp4"
    if not video_move_path.exists():
        video_move_path = OUTPUT_BASE / f"{unit}.mp4"
        
    sheet_move_path = OUTPUT_BASE / f"{unit}_move_sheet.png"
    
    video_attack_path = OUTPUT_BASE / f"{unit}_attack.mp4"
    sheet_attack_path = OUTPUT_BASE / f"{unit}_attack_sheet.png"
    
    # 1. Image
    image_url = None
    need_url = not (video_move_path.exists() and video_attack_path.exists())
    
    if need_url:
        image_url = generate_image(openai_client, data['prompt'], base_img_path)
        if not image_url:
            print(f"  [Error] Failed to get image URL for {unit}.")
            return
    
    # Process Base Image Variants (Static)
    if base_img_path.exists():
        try:
            # Resize and remove bg for static usage
            img = Image.open(base_img_path)
            img = img.resize((128, 128))
            img = remove(img)
            base_processed_path = OUTPUT_BASE / f"{unit}_processed.png"
            img.save(base_processed_path)
            create_variants(base_processed_path, unit, "") # e.g. knight_blue.png
        except Exception as e:
            print(f"  [Error] Failed to process base image for {unit}: {e}")

    # 2. Move Animation
    if not video_move_path.exists() and image_url:
        generate_video(ark_client, data['animation_prompt'], image_url, video_move_path)
    
    if video_move_path.exists():
        print(f"  [Regenerating] Move sprite sheet...")
        if video_to_spritesheet(video_move_path, sheet_move_path):
            create_variants(sheet_move_path, unit, "_move")

    # 3. Attack Animation
    if 'attack_prompt' in data:
        if not video_attack_path.exists() and image_url:
            generate_video(ark_client, data['attack_prompt'], image_url, video_attack_path)
        
        if video_attack_path.exists():
            print(f"  [Regenerating] Attack sprite sheet...")
            if video_to_spritesheet(video_attack_path, sheet_attack_path):
                create_variants(sheet_attack_path, unit, "_attack")
    
    print(f"Completed pipeline for {unit}.")

def run():
    config = load_config()
    openai_client = init_openai_client()
    ark_client = init_ark_client()
    
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    
    # Process all units defined in config
    # print(f"Starting asset generation for all units: {list(config['units'].keys())}")
    
    target_units = ["wall", "base"]
    print(f"Starting asset generation for targets: {target_units}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for unit, data in config['units'].items():
            if unit in target_units:
                # Submit task for each unit
                futures.append(
                    executor.submit(process_unit_pipeline, unit, data, openai_client, ark_client)
                )
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Pipeline task failed: {e}")

if __name__ == "__main__":
    run()