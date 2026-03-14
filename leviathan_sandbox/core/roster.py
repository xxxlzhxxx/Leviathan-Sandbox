from typing import Dict, Any

OPPONENTS = {
    "1": {
        "name": "Training Dummy",
        "type": "scripted",
        "description": "A simple bot that only spawns Knights when mana is full. Good for testing basics.",
        "difficulty": "Easy"
    },
    "2": {
        "name": "Goblin Rusher",
        "type": "random", # Or specialized random logic
        "description": "Spams random units without much thought. Unpredictable but uncoordinated.",
        "difficulty": "Easy-Medium"
    },
    "3": {
        "name": "Siege Master",
        "type": "siege",
        "description": "Focuses on defense with Turrets and long-range Catapult attacks. Hard to break.",
        "difficulty": "Medium"
    },
    "4": {
        "name": "Aggressive Commander",
        "type": "aggressive",
        "description": "Relentlessly pushes lanes with Knights and Archers. Will punish slow setups.",
        "difficulty": "Hard"
    },
    "5": {
        "name": "The Strategist (AI)",
        "type": "volc",
        "prompt": "You are a balanced strategist. You analyze the enemy's weak lane and exploit it. You mix tanks and dps units effectively.",
        "description": "An AI-powered agent that adapts to your moves. (Requires API Key)",
        "difficulty": "Adaptive"
    },
    "6": {
        "name": "The Berserker (AI)",
        "type": "volc",
        "prompt": "You are a berserker. You do not care about defense. You only care about damage. ALL IN!",
        "description": "An extremely aggressive AI that ignores defense. (Requires API Key)",
        "difficulty": "Hard"
    },
    "7": {
        "name": "The Turtle (AI)",
        "type": "volc",
        "prompt": "You are a turtle. You love walls and turrets. You only attack when you have a massive advantage. Survive at all costs.",
        "description": "A defensive AI that tries to win by stalling or counter-attacking.",
        "difficulty": "Medium"
    }
}

def get_opponent_by_id(oid: str) -> Dict[str, Any]:
    return OPPONENTS.get(str(oid))
