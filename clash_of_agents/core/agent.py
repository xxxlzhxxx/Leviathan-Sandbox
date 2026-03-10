import random
import json
import time
from typing import List, Dict, Optional, Tuple, Any
from abc import ABC, abstractmethod
from clash_of_agents.core.protocol import GameState, Action

# --- Game Rules for System Prompt ---
GAME_RULES = """
# Game Rules: Clash of Agents

## 1. Objective
- You are an AI commander in a 1v1 Real-Time Strategy game.
- Destroy the enemy Base (HP=500) or have more Mana/HP when time ends (300 ticks).
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
"""

class Agent(ABC):
    def __init__(self, team: str, system_prompt: str = ""):
        self.team = team
        self.system_prompt = system_prompt # User Strategy from YAML

    @abstractmethod
    def decide(self, state: GameState) -> Action:
        """Takes the current game state and returns an action."""
        pass

class RandomAgent(Agent):
    """A dumb agent that plays randomly."""
    def decide(self, state: GameState) -> Action:
        # Simple random logic
        
        # 1. Try to spawn a unit (50% chance)
        if state.me.mana >= 2 and random.random() < 0.5:
            # Pick a random affordable card
            affordable = []
            costs = {"knight": 3, "archer": 4, "goblin": 2, "orc": 5}
            for card in state.me.deck:
                if card in costs and state.me.mana >= costs[card]:
                    affordable.append(card)
            
            if affordable:
                card = random.choice(affordable)
                lane = random.randint(0, 2)
                return Action(type="spawn", card_id=card, y=lane)

        # 2. Try to build a wall (10% chance)
        if "wall" in state.me.deck and state.me.mana >= 2 and random.random() < 0.1:
             # Random valid x, y
             lane = random.randint(0, 2)
             # Valid x for blue: 1-5, red: 14-18
             if self.team == "blue":
                 x = random.randint(1, 5)
             else:
                 x = random.randint(14, 18)
             return Action(type="build", card_id="wall", x=x, y=lane)

        # 3. Otherwise Pass
        return Action(type="pass", card_id="", y=0)

class ScriptedAgent(Agent):
    """A simple rule-based agent."""
    def decide(self, state: GameState) -> Action:
        # Rule 1: If mana is full, spend it!
        if state.me.mana >= 8:
            return Action(type="spawn", card_id="knight", y=1) # Mid push
        
        return Action(type="pass", card_id="", y=0)

class VolcAgent(Agent):
    """
    Adapter for VolcEngine (Doubao) via OpenAI SDK.
    """
    def __init__(self, team: str, system_prompt: str = "", api_key: str = "", model: str = "ep-20260224155825-66kc4", debug: bool = False):
        super().__init__(team, system_prompt)
        self.api_key = api_key
        self.model = model
        self.debug = debug
        self.client = None
        
        try:
            from openai import OpenAI
            # VolcEngine Endpoint
            self.client = OpenAI(
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key=api_key
            )
        except ImportError:
            print("OpenAI SDK not found. Please install `openai`.")

    def decide(self, state: GameState) -> Action:
        state_json = state.model_dump_json()
        
        # ASCII Grid Visualization for Prompt
        grid_str = "\n".join(state.grid_view)
        
        # Diff Visualization
        diff_str = "\n".join(state.last_turn_changes) if state.last_turn_changes else "No significant changes."

        # Construct the full prompt
        # System: Game Rules + User Strategy (Personality)
        system_content = f"""
{GAME_RULES}

## YOUR STRATEGY / PERSONALITY
{self.system_prompt}

RETURN ONLY A VALID JSON ACTION. No markdown.
"""
        
        # User: Current State
        user_content = f"""
Current Situation (Turn {state.turn}/{state.max_turns}):

[Grid View]
{grid_str}
(Legend: .=Empty, K/k=Knight, A/a=Archer, G/g=Goblin, W/w=Wall, B/b=Base. Uppercase=Blue, Lowercase=Red)

[Events Since Last Turn]
{diff_str}

[Full State JSON]
{state_json}
"""

        if self.debug:
            full_prompt_log = f"""
--- [LLM Input for {self.team}] ---
SYSTEM:
{system_content}

USER:
{user_content}
-----------------------------------
"""
            print(full_prompt_log)

        if self.client:
            # Real Call
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": user_content}
                    ]
                )
                content = response.choices[0].message.content
                
                # Clean content (sometimes models wrap in ```json ... ```)
                content = content.replace("```json", "").replace("```", "").strip()
                
                if self.debug:
                    print(f"--- [LLM Output for {self.team}] ---\n{content}\n------------------------------------")
                
                action_dict = json.loads(content)
                return Action(**action_dict)
            except Exception as e:
                print(f"VolcAgent Error: {e}")
                return Action(type="pass", card_id="", y=0)
        else:
            return Action(type="pass", card_id="", y=0)
