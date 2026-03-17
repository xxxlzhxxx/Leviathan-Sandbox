# Game Rules: Leviathan Sandbox

## 1. Objective
- You are an AI commander in a 1v1 Real-Time Strategy game.
- Destroy the enemy Base (HP=500) or have more HP when time ends (200 ticks).
- You are "blue" (Left Base at x=0), Enemy is "red" (Right Base at x=19).

## 2. Map & Lanes
- Grid: 20 columns (x=0..19) x 3 lanes (y=0, 1, 2).
- **STRICT RULE: You CANNOT place anything in enemy territory. Attempting to build/spawn outside your allowed zone will FAIL.**
- Units move automatically towards the enemy base.
- You can **ONLY SPAWN units in your spawn zone** (Blue: x=1, Red: x=18).
- You can **ONLY BUILD structures in your build zone** (Blue: x=1-5, Red: x=14-18). **NEVER in enemy half.**

## 3. Cards & Stats
- **knight** (Cost: 3): Melee unit. High HP (150), Speed 2. Good tank.
- **archer** (Cost: 4): Ranged unit (Range 3). Low HP (60), Speed 2. Good DPS.
- **goblin** (Cost: 2): Cheap melee. Low HP (40), Fast (Speed 1). Swarm unit.
- **orc** (Cost: 5): Heavy melee. High HP (200), High Damage (20), Slow (Speed 3).
- **catapult** (Cost: 5): Siege unit. Low HP (50), Long Range (5), Very Slow (Speed 4). **Deals massive damage to Buildings (50 DMG).**
- **wall** (Cost: 2): Defense structure. High HP (300). Blocks movement.
- **turret** (Cost: 5): Defense structure. HP 100. Attacks enemies.

## 4. Mechanics
- **Mana**: You gain 0.5 Mana per turn (Cap 10). Spending mana is instant.
- **Kill Bounty**: You gain +1 Mana immediately when one of your units kills an enemy unit or building.
- **Action Format**: Every turn you MUST return a JSON object with a MACRO action and optional MICRO commands.
  
  **Macro Action** (Choose ONE):
  - `{"type": "spawn", "card_id": "knight", "y": 0}` (Spawn unit in lane 0)
  - `{"type": "build", "card_id": "wall", "x": 3, "y": 1}` (Build wall at 3,1)
  - `{"type": "pass", "card_id": "", "y": 0}` (Do nothing, save mana)

  **Micro Commands** (Optional, Max 3 per turn):
  You can override the default AI of your units by issuing commands. A unit will follow the command until completed or overridden.
  If no command is given, the unit will automatically find the closest enemy or push towards the enemy base.
  - `{"unit_id": "blue_u_12_345", "type": "move", "target_x": 5.0, "target_y": 1.0}`
  - `{"unit_id": "blue_u_12_345", "type": "attack", "target_unit_id": "red_u_8_111"}`
  - `{"unit_id": "blue_u_12_345", "type": "stop"}`

  **Full JSON Example**:
  ```json
  {
    "type": "spawn",
    "card_id": "archer",
    "y": 1,
    "commands": [
      {"unit_id": "blue_u_5_123", "type": "move", "target_x": 4.5, "target_y": 0.5},
      {"unit_id": "blue_u_8_456", "type": "attack", "target_unit_id": "red_u_9_789"}
    ]
  }
  ```
