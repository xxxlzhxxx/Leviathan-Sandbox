from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Entity:
    id: str
    team: str  # "blue" or "red"
    hp: int
    max_hp: int
    x: int # Integer
    y: int # Integer
    width: int
    height: int
    type: str # "base", "unit", "building"
    subtype: str = "unknown"

@dataclass
class Unit(Entity):
    damage: int = 0
    range: int = 0
    move_speed: int = 1 # ticks per move
    last_attack_tick: int = 0 
    last_move_tick: int = 0 # Added for integer movement cooldown
    target_id: Optional[str] = None
    
    # Command State
    command: Optional[Any] = None # Stores active UnitCommand
    action_state: str = "idle" # idle, move, attack

@dataclass
class Building(Entity):
    function: str = "defense" # "base", "defense", "production"
