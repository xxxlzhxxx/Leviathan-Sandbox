# Game Rules: Leviathan Sandbox

## 1. Objective
- You are an AI commander in a 1v1 Real-Time Strategy game.
- Destroy the enemy Base (HP=500) or have more HP when time ends (200 ticks).
- You are "blue" (Left Base at x=0), Enemy is "red" (Right Base at x=19).

## 2. Map & Lanes
- Grid: 20 columns (x=0..19) x 3 lanes (y=0, 1, 2).
- Units move automatically towards the enemy base.
- You can SPAWN units in your spawn zone (Blue: x=1, Red: x=18).
- You can BUILD structures in your build zone (Blue: x=1-5, Red: x=14-18).

## 3. Cards & Stats
- **knight** (Cost: 3): Melee unit. High HP (150), Speed 2. Good tank.
- **archer** (Cost: 4): Ranged unit (Range 3). Low HP (60), Speed 2. Good DPS.
- **goblin** (Cost: 2): Cheap melee. Low HP (40), Fast (Speed 1). Swarm unit.
- **orc** (Cost: 5): Heavy melee. High HP (200), High Damage (20), Slow (Speed 3).
- **wall** (Cost: 2): Defense structure. High HP (300). Blocks movement.
- **turret** (Cost: 5): Defense structure. HP 100. Attacks enemies.

## 4. Mechanics
- **Mana**: You gain 0.5 Mana per turn (Cap 10). Spending mana is instant.
- **Action**: Every turn you can perform ONE action:
  - `{"type": "spawn", "card_id": "knight", "y": 0}` (Spawn unit in lane 0)
  - `{"type": "build", "card_id": "wall", "x": 3, "y": 1}` (Build wall at 3,1)
  - `{"type": "pass", "card_id": "", "y": 0}` (Do nothing, save mana)
