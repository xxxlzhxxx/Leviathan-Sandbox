from ..base_entity import Unit

class Knight(Unit):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=150,
            max_hp=150,
            x=x,
            y=y,
            width=1,
            height=1,
            type="unit",
            subtype="knight",
            damage=15,
            range=1,
            move_speed=2
        )
