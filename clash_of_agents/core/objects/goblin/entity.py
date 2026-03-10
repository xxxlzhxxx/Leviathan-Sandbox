from ..base_entity import Unit

class Goblin(Unit):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=40,
            max_hp=40,
            x=x,
            y=y,
            width=1,
            height=1,
            type="unit",
            subtype="goblin",
            damage=8,
            range=1,
            move_speed=1
        )
