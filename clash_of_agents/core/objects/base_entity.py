from dataclasses import dataclass
from typing import Optional

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
    move_speed: int = 1 # ticks per move
    last_move_tick: int = 0
    target_id: Optional[str] = None

@dataclass
class Building(Entity):
    function: str = "defense" # "base", "defense", "production"
