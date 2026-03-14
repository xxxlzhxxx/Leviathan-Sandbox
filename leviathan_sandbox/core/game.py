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
            start_x = int(e.x)
            start_y = int(e.y)
            for dy in range(e.height):
                for dx in range(e.width):
                    cx, cy = start_x + dx, start_y + dy
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
            action_state = getattr(e, 'action_state', 'idle')
            target_id = getattr(e, 'target_id', None)
            
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
                move_speed=speed,
                action_state=action_state,
                target_id=target_id
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
                mana=0, # HIDDEN for fog of war / information asymmetry
                base_hp=opponent.base.hp,
                deck=[] # HIDDEN
            ),
            grid_view=self.get_grid_view(team),
            last_turn_changes=self.get_diff_logs()
        )

    def process_action(self, team: str, action: Action):
        """Processes an action bundle from an agent."""
        # 1. Process Micro Commands (Max 3 per turn)
        if action.commands:
            commands_processed = 0
            processed_units = set()
            
            for cmd in action.commands:
                if commands_processed >= 3:
                    break # Hard limit: max 3 micro-commands per turn
                    
                if cmd.unit_id in processed_units:
                    continue # One action per object rule
                    
                unit = next((e for e in self.entities if e.id == cmd.unit_id and e.team == team), None)
                if not unit:
                    continue
                    
                # Validation
                is_valid = False
                if cmd.type == "move":
                    if cmd.target_x is not None and cmd.target_y is not None:
                        if 0 <= cmd.target_x < GRID_WIDTH and 0 <= cmd.target_y < GRID_HEIGHT:
                            is_valid = True
                elif cmd.type == "attack":
                    if cmd.target_unit_id:
                        target = next((e for e in self.entities if e.id == cmd.target_unit_id), None)
                        if target and target.hp > 0:
                            # Check Range (Strict validation)
                            dist = self._dist(unit, target)
                            atk_range = getattr(unit, 'range', 1)
                            if dist <= atk_range + 0.5: # Small buffer for float precision
                                is_valid = True
                elif cmd.type == "stop":
                    is_valid = True
                    
                if is_valid:
                    unit.command = cmd
                    processed_units.add(unit.id)
                    commands_processed += 1

        # 2. Process Macro Action
        if action.type == "pass":
            return True
            
        if action.type == "spawn":
            # Pass action.x (optional)
            return self.spawn_unit(team, action.card_id, action.y, action.x)
            
        if action.type == "build":
            if action.x is None:
                return False
            return self.build_structure(team, action.card_id, action.x, action.y)
            
        return False

    def _is_occupied(self, x: int, y: int, width: int = 1, height: int = 1, exclude_id: str = None, ignore_team: str = None, pass_friendly_units: bool = False, mover_team: str = None) -> bool:
        for e in self.entities:
            if e.id == exclude_id or e.hp <= 0: continue
            if ignore_team and e.team == ignore_team: continue
            
            if pass_friendly_units and mover_team:
                if e.team == mover_team and e.type == "unit":
                    continue
            
            if (x < e.x + e.width and x + width > e.x and
                y < e.y + e.height and y + height > e.y):
                return True
        return False

    def spawn_unit(self, team: str, unit_type: str, lane: int, x: int = None):
        player = self.players[team]
        costs = {"knight": 3, "archer": 4, "goblin": 2, "orc": 5, "catapult": 5}
        cost = costs.get(unit_type, 3)
        if player.mana < cost: return False
            
        # Default spawn outside base
        default_x = 3 if team == "blue" else (GRID_WIDTH - 4)
        spawn_x = default_x
        
        # Allow spawning near base (Home Zone)
        if x is not None:
            if team == "blue":
                if 0 <= x < 8: spawn_x = int(x)
            else:
                if (GRID_WIDTH - 8) <= x < GRID_WIDTH: spawn_x = int(x)
        
        spawn_y = int(lane)
        if not (0 <= spawn_y < GRID_HEIGHT): return False
            
        if self._is_occupied(spawn_x, spawn_y, 1, 1, ignore_team=team): return False

        player.mana -= cost
        unit_id = f"{team}_u_{self.tick_count}_{random.randint(1000,9999)}"
        unit = None
        
        # Speed: Ticks per move (Lower is faster)
        if unit_type == "knight":
            unit = Knight(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 2
        elif unit_type == "archer":
            unit = Archer(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 2
        elif unit_type == "goblin":
            unit = Goblin(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 1
        elif unit_type == "orc":
            unit = Orc(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 3
        elif unit_type == "catapult":
            unit = Catapult(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 3
            
        if unit:
            self.entities.append(unit)
            return True
        return False

    def build_structure(self, team: str, building_type: str, x: int, y: int):
        player = self.players[team]
        valid_zone = False
        # Build Zone (Defensive Area)
        # Blue: 4-8 (Base 0-3)
        # Red: 16-20 (Base 21-24)
        if team == "blue" and 4 <= x <= 8: valid_zone = True
        elif team == "red" and (GRID_WIDTH - 8) <= x <= (GRID_WIDTH - 4): valid_zone = True
        if not valid_zone: return False
        
        costs = {"wall": 2, "turret": 5}
        cost = costs.get(building_type, 5)
        if player.mana < cost: return False

        if self._is_occupied(x, y): return False
        player.mana -= cost
        build_id = f"{team}_b_{self.tick_count}_{random.randint(1000,9999)}"
        building = None
        if building_type == "wall": building = Wall(id=build_id, team=team, x=x, y=y)
        elif building_type == "turret": building = Turret(id=build_id, team=team, x=x, y=y)
        if building:
            self.entities.append(building)
            return True
        return False

    def _edge_dist(self, e1, e2):
        import math
        x_dist = 0
        if e1.x + e1.width <= e2.x: x_dist = e2.x - (e1.x + e1.width)
        elif e2.x + e2.width <= e1.x: x_dist = e1.x - (e2.x + e2.width)
        
        y_dist = 0
        if e1.y + e1.height <= e2.y: y_dist = e2.y - (e1.y + e1.height)
        elif e2.y + e2.height <= e1.y: y_dist = e1.y - (e2.y + e2.height)
        
        return x_dist + y_dist # Manhattan distance (Integer)

    def _move_step(self, unit, tx, ty):
        dx = 0
        if tx > unit.x: dx = 1
        elif tx < unit.x: dx = -1
        
        dy = 0
        if ty > unit.y: dy = 1
        elif ty < unit.y: dy = -1
        
        # Prioritize X (Lane Push)
        if dx != 0:
            next_x = unit.x + dx
            if 0 <= next_x < GRID_WIDTH:
                if not self._is_occupied(next_x, unit.y, unit.width, unit.height, exclude_id=unit.id, pass_friendly_units=True, mover_team=unit.team):
                    unit.x = next_x
                    return True
        
        if dy != 0:
            next_y = unit.y + dy
            if 0 <= next_y < GRID_HEIGHT:
                if not self._is_occupied(unit.x, next_y, unit.width, unit.height, exclude_id=unit.id, pass_friendly_units=True, mover_team=unit.team):
                    unit.y = next_y
                    return True
        return False

    def _smart_move_or_attack(self, unit, target, speed, atk_range, atk_cooldown):
        # 1. Attack Check
        edge_dist = self._edge_dist(unit, target)
        if edge_dist <= atk_range:
            if (self.tick_count - getattr(unit, 'last_attack_tick', 0)) >= atk_cooldown:
                damage = getattr(unit, 'damage', 1)
                bonus = getattr(unit, 'bonus_vs_building', 0)
                if target.type in ["building", "base"]: damage += bonus
                
                target.hp -= damage
                unit.last_attack_tick = self.tick_count
                unit.action_state = "attack"
                unit.target_id = target.id
                if target.hp <= 0:
                     self.players[unit.team].mana = min(self.players[unit.team].mana + 1, 10)
            return

        # 2. Move Check
        last_move = getattr(unit, 'last_move_tick', 0)
        if (self.tick_count - last_move) >= speed:
            prev_x, prev_y = unit.x, unit.y
            self._move_step(unit, target.x, target.y)
            
            if unit.x != prev_x or unit.y != prev_y:
                unit.action_state = "move"
                unit.last_move_tick = self.tick_count

    def run_tick(self):
        from copy import deepcopy
        self.last_turn_snapshot = deepcopy(self.entities)
        self.tick_count += 1
        
        for p in self.players.values():
            p.mana = min(p.mana + 1, 10) # +1 Integer Mana per turn
            if p.base.hp <= 0: p.base.hp = 0

        active_units = [e for e in self.entities if e.hp > 0 and e.type == "unit"]
        active_buildings = [e for e in self.entities if e.hp > 0 and e.type == "building" and getattr(e, 'function', '') == 'attack']
        
        # Process Buildings
        for b in active_buildings:
            b.action_state = "idle"
            attack_cooldown = getattr(b, 'attack_speed', 1)
            if (self.tick_count - getattr(b, 'last_attack_tick', 0)) < attack_cooldown: continue
            
            enemies = [e for e in self.entities if e.team != b.team and e.hp > 0]
            target = None
            min_dist = 999
            rng = getattr(b, 'range', 3)
            
            for e in enemies:
                d = self._edge_dist(b, e)
                if d <= rng and d < min_dist:
                    min_dist = d
                    target = e
            
            if target:
                damage = getattr(b, 'damage', 5)
                target.hp -= damage
                b.last_attack_tick = self.tick_count
                b.action_state = "attack"
                b.target_id = target.id

        # Process Units
        for unit in active_units:
            unit.action_state = "idle"
            target_pos = None
            target_unit = None
            intent = "idle"
            
            # A. Check Command
            cmd = getattr(unit, 'command', None)
            if cmd:
                if cmd.type == "move":
                    if cmd.target_x is not None and cmd.target_y is not None:
                        target_pos = (cmd.target_x, cmd.target_y)
                        intent = "move"
                elif cmd.type == "attack":
                    t_unit = next((e for e in self.entities if e.id == cmd.target_unit_id), None)
                    if t_unit and t_unit.hp > 0:
                        target_unit = t_unit
                        intent = "attack"
                    else:
                        unit.command = None
                elif cmd.type == "stop":
                    unit.command = None
                    continue

            # B. Default AI (Nearest Enemy)
            if not unit.command:
                enemies = [e for e in self.entities if e.team != unit.team and e.hp > 0]
                closest = None
                min_dist = 999
                
                for e in enemies:
                    d = self._edge_dist(unit, e)
                    if d < min_dist:
                        min_dist = d
                        closest = e
                
                if closest:
                    target_unit = closest
                    intent = "attack"
                else:
                    enemy_base_x = GRID_WIDTH - 2 if unit.team == "blue" else 1
                    target_pos = (enemy_base_x, unit.y)
                    intent = "move"

            # Execute Intent
            speed = getattr(unit, 'move_speed', 1)
            atk_range = getattr(unit, 'range', 1)
            atk_cooldown = getattr(unit, 'attack_speed', 1)
            
            # Update Facing
            if target_unit:
                unit.facing = "right" if target_unit.x >= unit.x else "left"
            elif target_pos:
                unit.facing = "right" if target_pos[0] >= unit.x else "left"
            
            if intent == "attack" and target_unit:
                self._smart_move_or_attack(unit, target_unit, speed, atk_range, atk_cooldown)
            elif intent == "move" and target_pos:
                last_move = getattr(unit, 'last_move_tick', 0)
                if (self.tick_count - last_move) >= speed:
                    prev_x, prev_y = unit.x, unit.y
                    self._move_step(unit, target_pos[0], target_pos[1])
                    if unit.x != prev_x or unit.y != prev_y:
                        unit.action_state = "move"
                        unit.last_move_tick = self.tick_count
                if unit.x == target_pos[0] and unit.y == target_pos[1] and unit.command:
                    unit.command = None

        self.entities = [e for e in self.entities if e.hp > 0 or e.type == "base"]
        
        # Win Condition Logic
        blue_hp = self.players["blue"].base.hp
        red_hp = self.players["red"].base.hp
        
        if blue_hp <= 0 or red_hp <= 0 or self.tick_count >= GAME_DURATION:
            if blue_hp > red_hp: self.winner = "blue"
            elif red_hp > blue_hp: self.winner = "red"
            else:
                if self.players["blue"].mana > self.players["red"].mana: self.winner = "blue"
                elif self.players["red"].mana > self.players["blue"].mana: self.winner = "red"
                else: self.winner = "draw"
        
        snapshot = {
            "tick": self.tick_count,
            "entities": [asdict(e) for e in self.entities],
            "players": {k: {"mana": v.mana, "hp": v.base.hp} for k, v in self.players.items()}
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
