from ..base_entity import Building

SUB_GRID = 10

class Base(Building):
    def __init__(self, id: str, team: str, x: int, y: int, hp: int):
        super().__init__(
            id=id,
            team=team,
            hp=hp,
            max_hp=hp, # Should match initial HP
            x=x,
            y=y,
            width=3 * SUB_GRID,
            height=3 * SUB_GRID,
            type="base",
            subtype="base",
            function="base"
        )
