---
name: "leviathan-gameplay"
description: "Game rules and strategy guide for Leviathan Sandbox. Invoke when user wants to understand gameplay or write bots."
---

# Gameplay Rules

Leviathan Sandbox is a turn-based strategy game played on a 24x3 grid.

## Map Layout

- **Size**: 24 Columns x 3 Rows (Lanes).
- **Blue Base**: Occupies Columns 0-2 (Left). Spawns units at Column 3.
- **Red Base**: Occupies Columns 21-23 (Right). Spawns units at Column 20.
- **Goal**: Destroy the enemy base (HP reduced to 0).

## Resources

- **Mana**: Players start with 5 mana and gain 0.5 per tick. Max 10.
- **Costs**:
  - Goblin: 2
  - Knight: 3
  - Archer: 4
  - Orc: 5
  - Catapult: 6
  - Wall: 2
  - Turret: 4

## Actions

On each turn (every 10 ticks), an Agent can perform ONE action:
1. **Spawn**: Place a unit in a lane (`y=0,1,2`).
2. **Build**: Place a structure (Wall/Turret) at a specific coordinate (`x, y`).
3. **Pass**: Do nothing and accumulate mana.

## Writing a Bot

Create a YAML file in `strategies/`:

```yaml
name: "My Bot"
type: "aggressive" # Uses hardcoded aggressive logic
system_prompt: "Rush the enemy!" # Used if type is 'volc' (AI)
api_key: "sk-..." # Optional, for AI-driven bots
```

Supported types:
- `random`: Random moves.
- `scripted`: Simple rule-based logic.
- `aggressive`: Spams units, pushes lanes.
- `siege`: Defensive, builds turrets/catapults.
- `volc`: Uses LLM to decide moves based on `system_prompt`.

To run a battle:

```bash
python3 -m leviathan_sandbox.cli.main fight strategies/my_bot.yaml strategies/opponent.yaml
```
