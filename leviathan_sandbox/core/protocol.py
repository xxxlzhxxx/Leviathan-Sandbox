from typing import List, Dict, Optional, Literal
from enum import Enum
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

class ActionType(str, Enum):
    SPAWN = "spawn"
    BUILD = "build"
    PASS = "pass"

class CommandType(str, Enum):
    MOVE = "move"
    ATTACK = "attack"
    STOP = "stop"

class UnitCommand(BaseModel):
    unit_id: str
    type: CommandType
    target_x: Optional[int] = None # Integer target
    target_y: Optional[int] = None
    target_unit_id: Optional[str] = None

# --- State Models (Sent to Agent) ---

class EntityState(BaseModel):
    id: str
    team: str  # "blue" or "red"
    type: str  # "unit", "building", "base"
    subtype: str # "knight", "wall", etc.
    hp: int
    max_hp: int
    x: int # Integer coordinates
    y: int 
    width: int
    height: int
    # Optional dynamic stats
    damage: int = 0
    range: int = 0
    move_speed: int = 0 # Integer speed
    is_frozen: bool = False # Future proofing
    action_state: str = "idle" # idle, move, attack
    target_id: Optional[str] = None # ID of the target being attacked
    facing: str = "right" # "left", "right"

class PlayerState(BaseModel):
    team: str
    mana: int # Integer mana
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
    
    grid_view: List[str] 
    last_turn_changes: List[str]

# --- Action Models (Received from Agent) ---

class Action(BaseModel):
    type: str = "pass" 
    card_id: str = "" 
    x: Optional[int] = None 
    y: int = 0 
    
    commands: List[UnitCommand] = []
    
    # Validation helpers could go here
