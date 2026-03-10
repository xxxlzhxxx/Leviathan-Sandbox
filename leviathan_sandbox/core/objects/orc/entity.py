from ..base_entity import Unit

class Orc(Unit):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=200,
            max_hp=200,
            x=x,
            y=y,
            width=1,
            height=1,
            type="unit",
            subtype="orc",
            damage=20,
            range=1,
            move_speed=3
        )
