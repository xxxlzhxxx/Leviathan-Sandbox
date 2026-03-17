from ..base_entity import Unit

SUB_GRID = 10

class Knight(Unit):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=150,
            max_hp=150,
            x=x,
            y=y,
            width=SUB_GRID,
            height=SUB_GRID,
            type="unit",
            subtype="knight",
            damage=15,
            range=SUB_GRID,
            move_speed=5
        )
