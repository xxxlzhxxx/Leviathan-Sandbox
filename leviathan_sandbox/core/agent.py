import random
import json
import time
from typing import List, Dict, Optional, Tuple, Any
from abc import ABC, abstractmethod
from pathlib import Path
from leviathan_sandbox.core.protocol import GameState, Action

def load_game_rules():
    """Load game rules from prompts/game_rules.md"""
    try:
        # Assuming prompts dir is at the root of the repo, relative to this file
        # core/agent.py -> ../../prompts/game_rules.md
        base_path = Path(__file__).parent.parent.parent
        rules_path = base_path / "prompts" / "game_rules.md"
        with open(rules_path, "r") as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load game rules from {rules_path}: {e}")
        return "Game Rules Not Found."

GAME_RULES = load_game_rules()

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

class AggressiveAgent(Agent):
    """A bot that aggressively pushes lanes."""
    def decide(self, state: GameState) -> Action:
        # 1. If mana is high, spawn big units
        if state.me.mana >= 6:
            if "catapult" in state.me.deck:
                return Action(type="spawn", card_id="catapult", y=random.randint(0, 2))
            elif "knight" in state.me.deck:
                return Action(type="spawn", card_id="knight", y=random.randint(0, 2))
        
        # 2. If mana is medium, spawn support
        if state.me.mana >= 4:
            if "archer" in state.me.deck:
                # Spawn behind a random lane
                return Action(type="spawn", card_id="archer", y=random.randint(0, 2))
            elif "orc" in state.me.deck:
                return Action(type="spawn", card_id="orc", y=random.randint(0, 2))
        
        # 3. If mana is low, spawn cheap units or pass
        if state.me.mana >= 2:
            if "goblin" in state.me.deck:
                return Action(type="spawn", card_id="goblin", y=random.randint(0, 2))
            if "wall" in state.me.deck and random.random() < 0.2:
                 # Build wall randomly in front
                 lane = random.randint(0, 2)
                 x = random.randint(3, 8) if self.team == "blue" else random.randint(12, 17)
                 return Action(type="build", card_id="wall", x=x, y=lane)

        return Action(type="pass", card_id="", y=0)

class SiegeAgent(Agent):
    """A bot that focuses on siege and defense."""
    def decide(self, state: GameState) -> Action:
        # 1. Defense first: Build turret if mana allows and RNG says yes
        if "turret" in state.me.deck and state.me.mana >= 4 and random.random() < 0.3:
            lane = random.randint(0, 2)
            # Defensive position
            x = random.randint(1, 4) if self.team == "blue" else random.randint(16, 19)
            return Action(type="build", card_id="turret", x=x, y=lane)

        # 2. Siege: Catapult
        if "catapult" in state.me.deck and state.me.mana >= 6:
            return Action(type="spawn", card_id="catapult", y=random.randint(0, 2))

        # 3. Tank: Orc/Knight
        if state.me.mana >= 5:
            if "orc" in state.me.deck:
                return Action(type="spawn", card_id="orc", y=random.randint(0, 2))
            if "knight" in state.me.deck:
                return Action(type="spawn", card_id="knight", y=random.randint(0, 2))

        # 4. Spam: Goblin
        if "goblin" in state.me.deck and state.me.mana >= 2:
             return Action(type="spawn", card_id="goblin", y=random.randint(0, 2))

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
                if self.debug:
                    print(f"--- [LLM Output for {self.team}] ---\n{content}\n------------------------------------")
                
                # Parse JSON
                try:
                    action_dict = json.loads(content)
                    return Action(**action_dict)
                except json.JSONDecodeError:
                    # Fallback if markdown block
                    if "```json" in content:
                        clean_content = content.split("```json")[1].split("```")[0].strip()
                        action_dict = json.loads(clean_content)
                        return Action(**action_dict)
                    print(f"Error parsing JSON from LLM: {content}")
                    return Action(type="pass", card_id="", y=0)

            except Exception as e:
                print(f"VolcEngine API Error: {e}")
                return Action(type="pass", card_id="", y=0)
        
        return Action(type="pass", card_id="", y=0)