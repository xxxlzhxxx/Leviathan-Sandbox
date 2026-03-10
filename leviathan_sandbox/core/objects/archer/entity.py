from ..base_entity import Unit

class Archer(Unit):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=60,
            max_hp=60,
            x=x,
            y=y,
            width=1,
            height=1,
            type="unit",
            subtype="archer",
            damage=10,
            range=3,
            move_speed=2
        )
