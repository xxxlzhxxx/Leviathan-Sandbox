import json
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from clash_of_agents.core.protocol import GameState, PlayerState, EntityState, Action

# Constants
GRID_WIDTH = 20  # X axis: 0-9 (Blue), 10-19 (Red)
GRID_HEIGHT = 3  # Y axis: 0-2 (Three Lanes)
INITIAL_MANA = 100 # Total resources per player for the whole match
BASE_HP = 500    # Lower HP for faster games (was 3000)
BASE_DECAY = 1   # HP loss per DECAY_INTERVAL
DECAY_INTERVAL = 5 # Ticks between decay
TICK_RATE = 10
GAME_DURATION = 300 # 30 seconds max (was 600)
MANA_REGEN = 0.5 # Mana per turn

@dataclass
class Entity:
    id: str
    team: str  # "blue" or "red"
    hp: int
    max_hp: int
    x: int
    y: int
    width: int
    height: int
    type: str # "base", "unit", "building"
    subtype: str = "unknown"

@dataclass
class Unit(Entity):
    damage: int = 0
    range: int = 0
    move_speed: int = 1 # ticks per move (1 = move every tick, 2 = every other tick)
    last_move_tick: int = 0
    target_id: Optional[str] = None

@dataclass
class Building(Entity):
    function: str = "defense" # "base", "defense", "production"

@dataclass
class Player:
    team: str
    mana: float # Use float for regen
    base: Building
    deck: List[str] # Available cards

class Game:
    def __init__(self):
        self.tick = 0
        self.entities: List[Entity] = []
        self.replay_log = []
        self.winner = None
        
        # Initialize Bases
        # Blue Base: x=0, y=0-2 (3x1)
        blue_base = Building(
            id="blue_base",
            team="blue",
            hp=BASE_HP,
            max_hp=BASE_HP,
            x=0,
            y=0,
            width=1,
            height=3,
            type="base",
            subtype="base",
            function="base"
        )
        # Red Base: x=19, y=0-2 (3x1)
        red_base = Building(
            id="red_base",
            team="red",
            hp=BASE_HP,
            max_hp=BASE_HP,
            x=GRID_WIDTH - 1,
            y=0,
            width=1,
            height=3,
            type="base",
            subtype="base",
            function="base"
        )
        
        self.entities.append(blue_base)
        self.entities.append(red_base)

        self.players = {
            "blue": Player("blue", 5.0, blue_base, ["knight", "archer", "wall"]), # Start with 5 mana
            "red": Player("red", 5.0, red_base, ["goblin", "orc", "turret"])
        }
        
        self.last_turn_snapshot = [] # List[Entity] snapshot from previous turn

    def get_grid_view(self, team: str) -> List[str]:
        """Generates a 3x20 ASCII grid.
        Rows are lanes (0, 1, 2).
        Chars: 
          . = Empty
          K/A/G/O = Unit (Upper=Blue, Lower=Red)
          W/T = Building
          B = Base
        """
        grid = [['.' for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        # Mapping
        # Blue: Uppercase, Red: Lowercase
        # Knight -> K/k
        # Archer -> A/a
        # Goblin -> G/g
        # Orc -> O/o
        # Wall -> W/w
        # Turret -> T/t
        # Base -> B/b
        
        char_map = {
            "knight": "K", "archer": "A", "goblin": "G", "orc": "O",
            "wall": "W", "turret": "T", "base": "B"
        }
        
        for e in self.entities:
            # Determine char
            base_char = char_map.get(e.subtype, "?")
            if e.team == "red":
                base_char = base_char.lower()
            
            # Place on grid
            # Entities can be > 1x1 (Base is 3x1)
            for dy in range(e.height):
                for dx in range(e.width):
                    if 0 <= e.y + dy < GRID_HEIGHT and 0 <= e.x + dx < GRID_WIDTH:
                        grid[e.y + dy][e.x + dx] = base_char
        
        # Convert to strings
        return ["".join(row) for row in grid]

    def get_diff_logs(self) -> List[str]:
        """Simple diff between self.last_turn_snapshot and current entities."""
        # TODO: A real diff would track ID positions.
        # For now, let's just return key events logged during run_tick?
        # Actually, comparing positions is better.
        
        changes = []
        
        # Build dicts by ID
        old_map = {e.id: e for e in self.last_turn_snapshot}
        new_map = {e.id: e for e in self.entities}
        
        # Check spawned
        for eid, e in new_map.items():
            if eid not in old_map:
                changes.append(f"{e.team} {e.subtype} spawned at ({e.x}, {e.y})")
        
        # Check died
        for eid, e in old_map.items():
            if eid not in new_map and e.type != "base": # Base doesn't die in entity list usually
                changes.append(f"{e.team} {e.subtype} died at ({e.x}, {e.y})")
        
        # Check moved/damaged (optional, might be too verbose)
        # Let's just track spawn/die for high level context
        
        return changes

    def get_state(self, team: str) -> GameState:
        """Generates a serialized GameState for a specific team (Agent view)."""
        player = self.players[team]
        opponent_team = "red" if team == "blue" else "blue"
        opponent = self.players[opponent_team]
        
        entity_states = []
        for e in self.entities:
            # FoW Logic could be here (e.g. only visible if in range)
            # For now, full visibility
            
            # Map Entity -> EntityState
            # Handle potential missing attributes safely
            damage = getattr(e, 'damage', 0)
            range_val = getattr(e, 'range', 0)
            speed = getattr(e, 'move_speed', 0)
            
            es = EntityState(
                id=e.id,
                team=e.team,
                type=e.type,
                subtype=e.subtype,
                hp=e.hp,
                max_hp=e.max_hp,
                x=e.x,
                y=e.y,
                width=e.width,
                height=e.height,
                damage=damage,
                range=range_val,
                move_speed=speed
            )
            entity_states.append(es)
            
        return GameState(
            turn=self.tick,
            max_turns=GAME_DURATION,
            my_team=team,
            opponent_team=opponent_team,
            map_width=GRID_WIDTH,
            map_height=GRID_HEIGHT,
            entities=entity_states,
            me=PlayerState(
                team=team,
                mana=int(player.mana),
                base_hp=player.base.hp,
                deck=player.deck
            ),
            opponent=PlayerState(
                team=opponent_team,
                mana=int(opponent.mana), # Hidden info? Maybe estimate?
                base_hp=opponent.base.hp,
                deck=opponent.deck # Hidden deck?
            ),
            grid_view=self.get_grid_view(team),
            last_turn_changes=self.get_diff_logs()
        )


    def process_action(self, team: str, action: Action):
        """Processes a single action from an agent."""
        if action.type == "pass":
            return True
            
        if action.type == "spawn":
            # Map card_id to unit type
            # Validation handled inside spawn_unit
            return self.spawn_unit(team, action.card_id, action.y)
            
        if action.type == "build":
            if action.x is None:
                return False
            return self.build_structure(team, action.card_id, action.x, action.y)
            
        return False

    def _is_occupied(self, x: int, y: int, width: int = 1, height: int = 1, exclude_id: str = None) -> bool:
        for e in self.entities:
            if e.id == exclude_id or e.hp <= 0:
                continue
            # Check overlap
            if (x < e.x + e.width and x + width > e.x and
                y < e.y + e.height and y + height > e.y):
                return True
        return False

    def spawn_unit(self, team: str, unit_type: str, lane: int):
        """Spawns a unit from the base into a specific lane (y-coordinate)."""
        player = self.players[team]
        
        # Cost check (Simple hardcoded costs for now)
        costs = {"knight": 3, "archer": 4, "goblin": 2, "orc": 5}
        cost = costs.get(unit_type, 3)
        
        if player.mana < cost:
            return False
            
        # Spawn Position
        # Blue spawns at x=1, Red at x=18
        spawn_x = 1 if team == "blue" else GRID_WIDTH - 2
        spawn_y = lane # 0, 1, or 2
        
        if not (0 <= spawn_y < GRID_HEIGHT):
            return False
            
        if self._is_occupied(spawn_x, spawn_y):
            return False

        player.mana -= cost
        
        # Stats
        stats = {
            "knight": {"hp": 150, "damage": 15, "range": 1, "speed": 2},
            "archer": {"hp": 60, "damage": 10, "range": 3, "speed": 2},
            "goblin": {"hp": 40, "damage": 8, "range": 1, "speed": 1}, # Fast
            "orc": {"hp": 200, "damage": 20, "range": 1, "speed": 3}, # Slow
        }
        s = stats.get(unit_type, stats["knight"])
        
        unit = Unit(
            id=f"{team}_u_{self.tick}_{random.randint(1000,9999)}",
            team=team,
            hp=s["hp"],
            max_hp=s["hp"],
            x=spawn_x,
            y=spawn_y,
            width=1,
            height=1,
            type="unit",
            subtype=unit_type,
            damage=s["damage"],
            range=s["range"],
            move_speed=s["speed"]
        )
        self.entities.append(unit)
        return True

    def build_structure(self, team: str, building_type: str, x: int, y: int):
        """Builds a structure. Validates placement area."""
        player = self.players[team]
        
        # Construction Zone: First 5 cols from base
        # Blue: x in [1, 5]
        # Red: x in [14, 18] (19 is base)
        valid_zone = False
        if team == "blue" and 1 <= x <= 5:
            valid_zone = True
        elif team == "red" and (GRID_WIDTH - 6) <= x <= (GRID_WIDTH - 2):
            valid_zone = True
            
        if not valid_zone:
            return False
            
        # Cost
        costs = {"wall": 2, "turret": 5}
        cost = costs.get(building_type, 5)
        
        if player.mana < cost:
            return False

        if self._is_occupied(x, y):
            return False
            
        player.mana -= cost
        
        stats = {
            "wall": {"hp": 300, "function": "defense"},
            "turret": {"hp": 100, "function": "attack"} # Turret not fully implemented yet
        }
        s = stats.get(building_type, stats["wall"])
        
        building = Building(
            id=f"{team}_b_{self.tick}_{random.randint(1000,9999)}",
            team=team,
            hp=s["hp"],
            max_hp=s["hp"],
            x=x,
            y=y,
            width=1,
            height=1,
            type="building",
            subtype=building_type,
            function=s["function"]
        )
        self.entities.append(building)
        return True

    def run_tick(self):
        from copy import deepcopy
        # Snapshot state
        self.last_turn_snapshot = deepcopy(self.entities)
        
        self.tick += 1
        
        # 0. Base Decay & Mana Regen
        for p in self.players.values():
            if self.tick % DECAY_INTERVAL == 0:
                p.base.hp -= BASE_DECAY
            
            p.mana = min(p.mana + MANA_REGEN, 10.0) # Cap at 10
            if p.base.hp <= 0:
                p.base.hp = 0

        # 1. AI Logic (Handled externally via process_action now)
        # But units still need to move/attack automatically (Engine Logic)
        
        # 2. Unit Logic
        units = [e for e in self.entities if e.type == "unit" and e.hp > 0]
        
        for unit in units:
            # Check move speed
            if (self.tick - unit.last_move_tick) < unit.move_speed:
                continue 
            
            # Find target
            enemies = [e for e in self.entities if e.team != unit.team and e.hp > 0]
            target = None
            min_dist = 999
            
            # Forward direction
            dx_dir = 1 if unit.team == "blue" else -1
            
            # Check for enemies in attack range
            for e in enemies:
                # Closest point on entity e to unit
                ex_closest = max(e.x, min(unit.x, e.x + e.width - 1))
                ey_closest = max(e.y, min(unit.y, e.y + e.height - 1))
                
                dist = abs(ex_closest - unit.x) + abs(ey_closest - unit.y)
                if dist <= unit.range:
                    if dist < min_dist:
                        min_dist = dist
                        target = e
            
            if target:
                # Attack
                target.hp -= unit.damage
            else:
                # Move
                next_x = unit.x + dx_dir
                next_y = unit.y # Stay in lane usually
                
                # Check bounds
                if 0 <= next_x < GRID_WIDTH:
                    # Check collision with ANY entity (friend or foe)
                    if not self._is_occupied(next_x, next_y, exclude_id=unit.id):
                        unit.x = next_x
                        unit.y = next_y
                        unit.last_move_tick = self.tick
                    else:
                        pass # Blocked

        # 3. Cleanup Dead Entities
        self.entities = [e for e in self.entities if e.hp > 0 or e.type == "base"]

        # 4. Check Win Condition
        blue_hp = self.players["blue"].base.hp
        red_hp = self.players["red"].base.hp
        
        if blue_hp <= 0 or red_hp <= 0 or self.tick >= GAME_DURATION:
            if blue_hp > red_hp:
                self.winner = "blue"
            elif red_hp > blue_hp:
                self.winner = "red"
            else:
                # HP is equal, check remaining mana (resources)
                blue_mana = self.players["blue"].mana
                red_mana = self.players["red"].mana
                if blue_mana > red_mana:
                    self.winner = "blue"
                elif red_mana > blue_mana:
                    self.winner = "red"
                else:
                    self.winner = "draw"
        
        # Log
        snapshot = {
            "tick": self.tick,
            "entities": [asdict(e) for e in self.entities],
            "players": {
                k: {"mana": v.mana, "hp": v.base.hp} for k, v in self.players.items()
            }
        }
        self.replay_log.append(snapshot)

    def run_simulation(self):
        print("Starting simulation...")
        for _ in range(GAME_DURATION):
            self.run_tick()
            if self.winner:
                print(f"Game Over! Winner: {self.winner}")
                break
        return self.replay_log

    def save_replay(self, filename="replay.json"):
        with open(filename, "w") as f:
            json.dump({
                "match_id": "match_3lane_v1",
                "winner": self.winner,
                "ticks": self.replay_log
            }, f, indent=None) # Compact JSON
