from typing import List, Dict, Optional, Literal
from pydantic import BaseModel

# --- Enums ---
class EntityType(str):
    BASE = "base"
    UNIT = "unit"
    BUILDING = "building"

class UnitType(str):
    KNIGHT = "knight"
    ARCHER = "archer"
    GOBLIN = "goblin"
    ORC = "orc"

class BuildingType(str):
    WALL = "wall"
    TURRET = "turret"
    BASE = "base"

class ActionType(str):
    SPAWN = "spawn"
    BUILD = "build"
    PASS = "pass"

# --- State Models (Sent to Agent) ---

class EntityState(BaseModel):
    id: str
    team: str  # "blue" or "red"
    type: str  # "unit", "building", "base"
    subtype: str # "knight", "wall", etc.
    hp: int
    max_hp: int
    x: int
    y: int
    width: int
    height: int
    # Optional dynamic stats
    damage: int = 0
    range: int = 0
    move_speed: int = 0
    is_frozen: bool = False # Future proofing

class PlayerState(BaseModel):
    team: str
    mana: int
    base_hp: int
    deck: List[str]

class GameState(BaseModel):
    turn: int
    max_turns: int
    my_team: str
    opponent_team: str
    map_width: int
    map_height: int
    entities: List[EntityState]
    me: PlayerState
    opponent: PlayerState
    
    # New Fields for Grid & Diff
    # 3x20 string array, e.g. [ "...", "K.G", "..." ]
    # '.' = Empty, 'K' = Knight, 'G' = Goblin, etc.
    grid_view: List[str] 
    
    # Text description of changes since last turn
    # e.g. ["Blue Knight moved to (2,1)", "Red Goblin spawned at (18,0)"]
    last_turn_changes: List[str]

# --- Action Models (Received from Agent) ---

class Action(BaseModel):
    type: str # "spawn", "build", "pass"
    card_id: str # e.g. "knight", "wall"
    x: Optional[int] = None # For building
    y: int # Lane index (0, 1, 2)
    
    # Validation helpers could go here
