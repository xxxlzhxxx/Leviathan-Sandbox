---
name: "leviathan-create-unit"
description: "How to add new units to Leviathan Sandbox: asset generation and game logic. Invoke when user wants to create a new game character."
---

# Create New Unit

To add a new unit (e.g., "Mage") to the game:

## 1. Define Asset Prompts (`tools/asset_pipeline/config.yaml`)

Add a new entry under `units:`:

```yaml
  mage:
    prompt: "A pixel art sprite of a mage in robes holding a staff, side view facing right, 2D game asset, 16-bit pixel art, white background"
    animation_prompt: "The mage is floating slightly, staff glowing, side view facing right, smooth looping animation"
    attack_prompt: "The mage casts a fireball to the right, staff raised, side view facing right, attacking, dynamic action"
```

## 2. Generate Assets

Run the asset pipeline:

```bash
python3 tools/asset_pipeline/pipeline.py
```

This will automatically:
1. Generate base image, move video, and attack video.
2. Convert videos to sprite sheets.
3. Create Blue (Right) and Red (Left + Tinted) variants.
4. Save to `web/assets_animated/`.

## 3. Register in Game Logic (`leviathan_sandbox/core/game.py`)

1. Update `char_map` in `Game.get_grid_view` method to assign a character for ASCII visualization (e.g., `"mage": "M"`).
2. Add the unit to `self.players` decks if you want it to be playable immediately.

## 4. Define Unit Behavior (Optional)

If the unit has special logic (e.g., AOE attack, healing), create a new class in `leviathan_sandbox/core/objects/unit/` inheriting from `Unit` or `Entity`, and implement custom `tick()` logic.

## 5. Update Frontend (`leviathan_sandbox/web/index.html`)

Add the unit name to the `assetNames` array so the frontend preloads its sprites:

```javascript
const assetNames = ["knight", "archer", ..., "mage"];
```

The frontend will automatically handle animation states (`_move`, `_attack`) based on the unit's action state in the replay.
