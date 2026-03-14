import random
import time
import json
from typing import List, Dict, Optional, Any
from dataclasses import asdict
from leviathan_sandbox.core.protocol import GameState, EntityState, PlayerState, Action
from leviathan_sandbox.core.objects.base.entity import Base
from leviathan_sandbox.core.objects.knight.entity import Knight
from leviathan_sandbox.core.objects.archer.entity import Archer
from leviathan_sandbox.core.objects.goblin.entity import Goblin
from leviathan_sandbox.core.objects.orc.entity import Orc
from leviathan_sandbox.core.objects.catapult.entity import Catapult
from leviathan_sandbox.core.objects.wall.entity import Wall
from leviathan_sandbox.core.objects.turret.entity import Turret

GRID_WIDTH = 24  # 3 (Base) + 18 (Battlefield) + 3 (Base)
GRID_HEIGHT = 3
GAME_DURATION = 200 # Ticks
MANA_REGEN = 0.1 # Per tick
BASE_HP = 1000
BASE_DECAY = 1 # Per decay interval
DECAY_INTERVAL = 10
SUDDEN_DEATH_START = 150

class Player:
    def __init__(self, team: str, mana: float, base: Base, deck: List[str]):
        self.team = team
        self.mana = mana
        self.base = base
        self.deck = deck

class Game:
    def __init__(self):
        self.tick_count = 0
        self.max_turns = GAME_DURATION
        self.entities = []
        self.replay_log = []
        self.winner = None
        self.last_turn_snapshot = []
        
        # Blue Base: x=0, y=0-2 (3x3)
        blue_base = Base(id="blue_base", team="blue", x=0, y=0, hp=BASE_HP)
        # Red Base: x=21, y=0-2 (3x3)
        red_base = Base(id="red_base", team="red", x=GRID_WIDTH - 3, y=0, hp=BASE_HP)
        
        self.players = {
            "blue": Player("blue", 5.0, blue_base, ["knight", "archer", "wall", "catapult"]),
            "red": Player("red", 5.0, red_base, ["goblin", "orc", "turret", "catapult"])
        }
        
        self.entities.append(blue_base)
        self.entities.append(red_base)

    def get_grid_view(self, team: str) -> List[str]:
        grid = [['.' for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        char_map = {
            "knight": "K", "archer": "A", "goblin": "G", "orc": "O", "catapult": "C",
            "wall": "W", "turret": "T", "base": "B"
        }
        
        for e in self.entities:
            if e.hp <= 0: continue
            char = char_map.get(e.subtype, "?")
            if e.team == "red":
                char = char.lower()
            
            # Entity might be larger than 1x1
            for dy in range(e.height):
                for dx in range(e.width):
                    cx, cy = e.x + dx, e.y + dy
                    if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT:
                        grid[cy][cx] = char
                        
        return ["".join(row) for row in grid]

    def get_diff_logs(self) -> List[str]:
        logs = []
        # Compare self.entities with self.last_turn_snapshot
        # Simplified: just log events (attack, death)
        # But we don't have event log stored.
        # Let's return empty for now or implement event logging later.
        return []

    def get_state(self, team: str) -> GameState:
        opponent_team = "red" if team == "blue" else "blue"
        player = self.players[team]
        opponent = self.players[opponent_team]
        
        entity_states = []
        for e in self.entities:
            if e.hp <= 0: continue
            
            damage = getattr(e, 'damage', 0)
            range_val = getattr(e, 'range', 0)
            speed = getattr(e, 'move_speed', 0)
            
            es = EntityState(
                id=e.id,
                team=e.team,
                type=e.type,
                subtype=e.subtype,
                hp=e.hp,
                max_hp=e.max_hp,
                x=e.x,
                y=e.y,
                width=e.width,
                height=e.height,
                damage=damage,
                range=range_val,
                move_speed=speed
            )
            entity_states.append(es)
            
        return GameState(
            turn=self.tick_count,
            max_turns=GAME_DURATION,
            my_team=team,
            opponent_team=opponent_team,
            map_width=GRID_WIDTH,
            map_height=GRID_HEIGHT,
            entities=entity_states,
            me=PlayerState(
                team=team,
                mana=int(player.mana),
                base_hp=player.base.hp,
                deck=player.deck
            ),
            opponent=PlayerState(
                team=opponent_team,
                mana=int(opponent.mana), 
                base_hp=opponent.base.hp,
                deck=opponent.deck 
            ),
            grid_view=self.get_grid_view(team),
            last_turn_changes=self.get_diff_logs()
        )

    def process_action(self, team: str, action: Action):
        """Processes a single action from an agent."""
        if action.type == "pass":
            return True
            
        if action.type == "spawn":
            return self.spawn_unit(team, action.card_id, action.y)
            
        if action.type == "build":
            if action.x is None:
                return False
            return self.build_structure(team, action.card_id, action.x, action.y)
            
        return False

    def _is_occupied(self, x: int, y: int, width: int = 1, height: int = 1, exclude_id: str = None, ignore_team: str = None) -> bool:
        for e in self.entities:
            if e.id == exclude_id or e.hp <= 0:
                continue
            
            if ignore_team and e.team == ignore_team:
                continue

            if (x < e.x + e.width and x + width > e.x and
                y < e.y + e.height and y + height > e.y):
                return True
        return False

    def spawn_unit(self, team: str, unit_type: str, lane: int):
        player = self.players[team]
        
        costs = {"knight": 3, "archer": 4, "goblin": 2, "orc": 5, "catapult": 5}
        cost = costs.get(unit_type, 3)
        
        if player.mana < cost:
            return False
            
        spawn_x = 1 if team == "blue" else GRID_WIDTH - 2
        spawn_y = lane 
        
        if not (0 <= spawn_y < GRID_HEIGHT):
            return False
            
        if self._is_occupied(spawn_x, spawn_y, ignore_team=team):
            return False

        player.mana -= cost
        
        unit_id = f"{team}_u_{self.tick_count}_{random.randint(1000,9999)}"
        unit = None
        
        if unit_type == "knight":
            unit = Knight(id=unit_id, team=team, x=spawn_x, y=spawn_y)
        elif unit_type == "archer":
            unit = Archer(id=unit_id, team=team, x=spawn_x, y=spawn_y)
        elif unit_type == "goblin":
            unit = Goblin(id=unit_id, team=team, x=spawn_x, y=spawn_y)
        elif unit_type == "orc":
            unit = Orc(id=unit_id, team=team, x=spawn_x, y=spawn_y)
        elif unit_type == "catapult":
            unit = Catapult(id=unit_id, team=team, x=spawn_x, y=spawn_y)
            
        if unit:
            self.entities.append(unit)
            return True
        return False

    def build_structure(self, team: str, building_type: str, x: int, y: int):
        player = self.players[team]
        
        valid_zone = False
        if team == "blue" and 1 <= x <= 5:
            valid_zone = True
        elif team == "red" and (GRID_WIDTH - 6) <= x <= (GRID_WIDTH - 2):
            valid_zone = True
            
        if not valid_zone:
            return False
            
        costs = {"wall": 2, "turret": 5}
        cost = costs.get(building_type, 5)
        
        if player.mana < cost:
            return False

        if self._is_occupied(x, y):
            return False
            
        player.mana -= cost
        
        build_id = f"{team}_b_{self.tick_count}_{random.randint(1000,9999)}"
        building = None
        
        if building_type == "wall":
            building = Wall(id=build_id, team=team, x=x, y=y)
        elif building_type == "turret":
            building = Turret(id=build_id, team=team, x=x, y=y)
            
        if building:
            self.entities.append(building)
            return True
        return False

    def run_tick(self):
        from copy import deepcopy
        self.last_turn_snapshot = deepcopy(self.entities)
        
        self.tick_count += 1
        
        is_sudden_death = self.tick_count >= SUDDEN_DEATH_START
        current_decay = BASE_DECAY * 5 if is_sudden_death else BASE_DECAY

        for p in self.players.values():
            if self.tick_count % DECAY_INTERVAL == 0:
                p.base.hp -= current_decay
            
            p.mana = min(p.mana + MANA_REGEN, 10.0) 
            if p.base.hp <= 0:
                p.base.hp = 0

        attackers = [e for e in self.entities if (e.type == "unit" or (e.type == "building" and getattr(e, 'function', '') == 'attack')) and e.hp > 0]
        
        for attacker in attackers:
            speed = getattr(attacker, 'move_speed', 1)
            if speed < 1: speed = 1
            
            if (self.tick_count - getattr(attacker, 'last_move_tick', 0)) < speed:
                continue 
            
            enemies = [e for e in self.entities if e.team != attacker.team and e.hp > 0]
            target = None
            min_dist = 999
            
            dx_dir = 1 if attacker.team == "blue" else -1
            
            attack_range = getattr(attacker, 'range', 0)
            if attacker.type == "building" and not hasattr(attacker, 'range'):
                 attack_range = 3
            
            for e in enemies:
                ex_closest = max(e.x, min(attacker.x, e.x + e.width - 1))
                ey_closest = max(e.y, min(attacker.y, e.y + e.height - 1))
                
                dist = abs(ex_closest - attacker.x) + abs(ey_closest - attacker.y)
                if dist <= attack_range:
                    if dist < min_dist:
                        min_dist = dist
                        target = e
            
            if target:
                damage = getattr(attacker, 'damage', 0)
                if attacker.type == "building" and damage == 0: damage = 5 
                
                bonus_vs_building = getattr(attacker, 'bonus_vs_building', 0)
                if target.type == "building" or target.type == "base":
                     damage += bonus_vs_building

                target.hp -= damage
                attacker.last_move_tick = self.tick_count 
                
                if target.hp <= 0:
                     self.players[attacker.team].mana = min(self.players[attacker.team].mana + 1.0, 10.0)

            elif attacker.type == "unit":
                next_x = attacker.x + dx_dir
                next_y = attacker.y 
                
                if 0 <= next_x < GRID_WIDTH:
                    if not self._is_occupied(next_x, next_y, exclude_id=attacker.id, ignore_team=attacker.team):
                        attacker.x = next_x
                        attacker.y = next_y
                        attacker.last_move_tick = self.tick_count
                    else:
                        pass 

        self.entities = [e for e in self.entities if e.hp > 0 or e.type == "base"]

        blue_hp = self.players["blue"].base.hp
        red_hp = self.players["red"].base.hp
        
        if blue_hp <= 0 or red_hp <= 0 or self.tick_count >= GAME_DURATION:
            if blue_hp > red_hp:
                self.winner = "blue"
            elif red_hp > blue_hp:
                self.winner = "red"
            else:
                blue_mana = self.players["blue"].mana
                red_mana = self.players["red"].mana
                if blue_mana > red_mana:
                    self.winner = "blue"
                elif red_mana > blue_mana:
                    self.winner = "red"
                else:
                    self.winner = "draw"
        
        snapshot = {
            "tick": self.tick_count,
            "entities": [asdict(e) for e in self.entities],
            "players": {
                k: {"mana": v.mana, "hp": v.base.hp} for k, v in self.players.items()
            }
        }
        self.replay_log.append(snapshot)

    def tick(self, blue_agent, red_agent):
        """Advances the game by one tick, including agent decisions."""
        # 1. Agents Decide
        state_blue = self.get_state("blue")
        action_blue = blue_agent.decide(state_blue)
        self.process_action("blue", action_blue)
        
        state_red = self.get_state("red")
        action_red = red_agent.decide(state_red)
        self.process_action("red", action_red)
        
        # 2. Engine Update
        self.run_tick()

    def get_replay_data(self):
        return {
            "match_id": f"battle_{int(time.time())}",
            "ticks": self.replay_log,
            "winner": self.winner
        }
