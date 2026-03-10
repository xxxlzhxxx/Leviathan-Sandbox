from ..base_entity import Building

class Turret(Building):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=100,
            max_hp=100,
            x=x,
            y=y,
            width=1,
            height=1,
            type="building",
            subtype="turret",
            function="attack"
        )
        # Combat Stats
        self.damage = 15 # Buffed from 5 (default)
        self.range = 4   # Buffed from 3
        self.move_speed = 1 # Attack speed (ticks per attack)
