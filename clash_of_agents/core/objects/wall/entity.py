from ..base_entity import Building

class Wall(Building):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=300,
            max_hp=300,
            x=x,
            y=y,
            width=1,
            height=1,
            type="building",
            subtype="wall",
            function="defense"
        )
