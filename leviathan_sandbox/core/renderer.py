import cv2
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from leviathan_sandbox.core.protocol import GameState

# Constants matching frontend
GRID_W = 24
GRID_H = 3
COL_WIDTH = 80
LANE_HEIGHT = 100
CANVAS_W = 1200 + 40 # 24 * 50? No, let's match frontend logic roughly
# Frontend: CANVAS_W = 1200 + 40. COL_WIDTH = 1200 / 24 = 50.
# Wait, frontend said COL_WIDTH = PLAY_AREA_W / GRID_W = 1200 / 24 = 50.
# CELL_SIZE was 80 but COL_WIDTH is effectively 50.
# Let's stick to frontend dimensions for consistency.
REAL_COL_WIDTH = 50
REAL_LANE_HEIGHT = 100
REAL_CANVAS_W = 1240
REAL_CANVAS_H = 300
FPS = 30
SPRITE_SIZE = 128

ASSETS_DIR = Path(__file__).parent.parent.parent / "leviathan_sandbox" / "web" / "assets"
ANIMATED_DIR = Path(__file__).parent.parent.parent / "leviathan_sandbox" / "web" / "assets_animated"

class HeadlessRenderer:
    def __init__(self, replay_path: Path, output_path: Path):
        self.replay_path = replay_path
        self.output_path = output_path
        self.assets = {}
        self.load_assets()
        
    def load_assets(self):
        """Load all assets into memory."""
        # Static assets
        for p in ASSETS_DIR.glob("*.png"):
            try:
                img = Image.open(p).convert("RGBA")
                self.assets[p.stem] = img
            except Exception as e:
                print(f"Warning: Failed to load {p}: {e}")
                
        # Animated assets (spritesheets)
        for p in ANIMATED_DIR.glob("*.png"):
            try:
                img = Image.open(p).convert("RGBA")
                self.assets[p.stem] = img
            except Exception as e:
                print(f"Warning: Failed to load {p}: {e}")

    def render(self):
        print(f"Rendering replay {self.replay_path} to video...")
        with open(self.replay_path, "r") as f:
            data = json.load(f)
        
        ticks = data["ticks"]
        # Assuming 1 tick = 0.5s in game logic? 
        # Frontend playbackSpeed = 2 (2 ticks per second?)
        # Let's say we want to render at 30 FPS.
        # And we want 2 ticks per second. So 15 frames per tick.
        frames_per_tick = 15 
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(self.output_path), fourcc, FPS, (REAL_CANVAS_W, REAL_CANVAS_H))
        
        for i in range(len(ticks) - 1):
            current_state = ticks[i]
            next_state = ticks[i+1]
            
            for f in range(frames_per_tick):
                alpha = f / frames_per_tick
                frame_img = self.draw_frame(current_state, next_state, alpha, i * frames_per_tick + f)
                
                # Convert PIL to OpenCV (BGR)
                frame_np = np.array(frame_img)
                frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGBA2BGR)
                out.write(frame_bgr)
                
        out.release()
        print(f"Video saved to {self.output_path}")
        return str(self.output_path)

    def draw_frame(self, state1, state2, alpha, total_frame_idx):
        # Create canvas
        canvas = Image.new("RGBA", (REAL_CANVAS_W, REAL_CANVAS_H), (30, 30, 30, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Draw Grid
        offset_x = 20
        
        # Background Zones
        # Blue Base (3 cols)
        draw.rectangle([offset_x, 0, offset_x + 3 * REAL_COL_WIDTH, REAL_CANVAS_H], fill=(0, 0, 100, 50))
        # Red Base (3 cols)
        draw.rectangle([offset_x + (GRID_W - 3) * REAL_COL_WIDTH, 0, offset_x + GRID_W * REAL_COL_WIDTH, REAL_CANVAS_H], fill=(100, 0, 0, 50))
        
        # Grid Lines
        for x in range(GRID_W + 1):
            draw.line([(offset_x + x * REAL_COL_WIDTH, 0), (offset_x + x * REAL_COL_WIDTH, REAL_CANVAS_H)], fill=(60, 60, 60), width=1)
        for y in range(GRID_H + 1):
            draw.line([(offset_x, y * REAL_LANE_HEIGHT), (offset_x + GRID_W * REAL_COL_WIDTH, y * REAL_LANE_HEIGHT)], fill=(60, 60, 60), width=1)

        # Draw Entities
        entities1 = {e["id"]: e for e in state1["entities"]}
        entities2 = {e["id"]: e for e in state2["entities"]}
        
        # Get all unique IDs from both states
        all_ids = set(entities1.keys()) | set(entities2.keys())
        
        # Sort by Y to handle occlusion simply
        sorted_ids = sorted(list(all_ids), key=lambda eid: entities1.get(eid, {}).get("y", 0))
        
        for eid in sorted_ids:
            e1 = entities1.get(eid)
            e2 = entities2.get(eid)
            
            if not e1: continue # Skip if only in next frame (spawned next frame)
            
            # Interpolate Position
            if e2:
                x = e1["x"] + (e2["x"] - e1["x"]) * alpha
                y = e1["y"] + (e2["y"] - e1["y"]) * alpha
                hp = e1["hp"] # HP changes instantly on tick boundary usually
            else:
                # Entity died or despawned
                x = e1["x"]
                y = e1["y"]
                hp = e1["hp"]
            
            # Determine Action & Asset
            action = "idle"
            if e2 and (e2["x"] != e1["x"] or e2["y"] != e1["y"]):
                action = "move"
            
            # Simple attack heuristic: every other second? 
            # Or use game logic? Replay doesn't store "is_attacking".
            # Frontend uses: if (Math.floor(currentPlaybackTick / 20) % 2 === 1) -> attack
            # Let's simplify: if not moving, idle. 
            # We can improve this if we record actions in replay.
            
            # Asset Key
            team = e1["team"]
            subtype = e1["subtype"]
            
            asset_key = f"{subtype}_{team}" # Default static
            
            # Try animated
            anim_key = f"{subtype}_{action}_{team}"
            if anim_key in self.assets:
                sheet = self.assets[anim_key]
                # Frame calculation
                # 8 frames loop
                anim_frame = (total_frame_idx // 3) % 8 
                
                # Crop from sheet
                # sheet is horizontal strip
                w, h = sheet.size
                frame_w = w // 8 # Assuming 8 frames
                frame_h = h
                
                # Check if 128x128
                if frame_h == 128:
                    pass
                
                sx = anim_frame * frame_w
                sprite = sheet.crop((sx, 0, sx + frame_w, frame_h))
                
                # No need to flip, assets are pre-flipped
            else:
                # Static fallback
                if asset_key in self.assets:
                    sprite = self.assets[asset_key]
                else:
                    continue # No asset found
            
            # Resize to fit grid?
            # Grid cell is 50x100. Asset is 128x128.
            # Base is 3x3 (150x300).
            
            target_w = int(e1["width"] * REAL_COL_WIDTH)
            target_h = int(e1["height"] * REAL_LANE_HEIGHT)
            
            # Keep aspect ratio? Or stretch?
            # Frontend: ctx.drawImage(img, x, y, w, h) -> Stretches
            
            sprite = sprite.resize((target_w, target_h), Image.NEAREST)
            
            # Draw
            draw_x = int(offset_x + x * REAL_COL_WIDTH)
            draw_y = int(y * REAL_LANE_HEIGHT)
            
            canvas.alpha_composite(sprite, (draw_x, draw_y))
            
            # Draw HP Bar
            bar_w = target_w - 4
            bar_h = 4
            hp_pct = max(0, hp / e1["max_hp"])
            
            draw.rectangle([draw_x + 2, draw_y + 2, draw_x + 2 + bar_w, draw_y + 2 + bar_h], fill=(0, 0, 0))
            color = (0, 255, 0) if hp_pct > 0.5 else (255, 0, 0)
            draw.rectangle([draw_x + 2, draw_y + 2, draw_x + 2 + int(bar_w * hp_pct), draw_y + 2 + bar_h], fill=color)

        # Draw UI Overlay (Scores)
        # Blue HP
        blue_hp = int(state1["players"]["blue"]["hp"])
        red_hp = int(state1["players"]["red"]["hp"])
        
        font = ImageFont.load_default()
        draw.text((20, 10), f"BLUE HP: {blue_hp}", fill=(100, 200, 255), font=font)
        draw.text((REAL_CANVAS_W - 100, 10), f"RED HP: {red_hp}", fill=(255, 100, 100), font=font)
        
        return canvas

