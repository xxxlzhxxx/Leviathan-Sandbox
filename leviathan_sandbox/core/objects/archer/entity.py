from ..base_entity import Unit

class Archer(Unit):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=30,  # Nerfed from 60 to be more fragile
            max_hp=30,
            x=x,
            y=y,
            width=1,
            height=1,
            type="unit",
            subtype="archer",
            damage=15, # Buffed damage slightly
            range=4,   # Increased range to compensate
            move_speed=2
        )
