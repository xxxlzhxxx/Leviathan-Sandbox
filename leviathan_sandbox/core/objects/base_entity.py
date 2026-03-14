from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class Entity:
    id: str
    team: str  # "blue" or "red"
    hp: int
    max_hp: int
    x: float # Changed to float
    y: float # Changed to float
    width: int
    height: int
    type: str # "base", "unit", "building"
    subtype: str = "unknown"

@dataclass
class Unit(Entity):
    damage: int = 0
    range: int = 0
    move_speed: float = 1.0 # tiles per tick
    last_attack_tick: int = 0 # Renamed from last_move_tick
    target_id: Optional[str] = None
    
    # Command State
    command: Optional[Any] = None # Stores active UnitCommand

@dataclass
class Building(Entity):
    function: str = "defense" # "base", "defense", "production"
