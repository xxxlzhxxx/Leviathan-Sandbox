from ..base_entity import Unit

class Catapult(Unit):
    def __init__(self, id: str, team: str, x: int, y: int):
        super().__init__(
            id=id,
            team=team,
            hp=50,
            max_hp=50,
            x=x,
            y=y,
            width=1,
            height=1,
            type="unit",
            subtype="catapult",
            damage=10,
            range=5,
            move_speed=4 # Very Slow
        )
        # Special Attributes
        self.bonus_vs_building = 40 # Total 50 dmg to buildings
