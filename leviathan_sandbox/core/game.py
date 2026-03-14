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

    def _is_occupied(self, x: int, y: int, width: int = 1, height: int = 1, exclude_id: str = None, ignore_team: str = None) -> bool:
        for e in self.entities:
            if e.id == exclude_id or e.hp <= 0: continue
            if ignore_team and e.team == ignore_team: continue
            if (x < e.x + e.width and x + width > e.x and
                y < e.y + e.height and y + height > e.y):
                return True
        return False

    def spawn_unit(self, team: str, unit_type: str, lane: int, x: float = None):
        player = self.players[team]
        costs = {"knight": 3, "archer": 4, "goblin": 2, "orc": 5, "catapult": 5}
        cost = costs.get(unit_type, 3)
        if player.mana < cost: return False
            
        # Default spawn outside base
        default_x = 3.0 if team == "blue" else float(GRID_WIDTH - 4)
        spawn_x = default_x
        
        # Allow spawning anywhere in own territory (half map)
        # Blue: [0, 12)
        # Red: [12, 24)
        if x is not None:
            if team == "blue":
                if 0 <= x < (GRID_WIDTH / 2): spawn_x = float(x)
            else:
                if (GRID_WIDTH / 2) <= x < GRID_WIDTH: spawn_x = float(x)
        
        spawn_y = float(lane)
        if not (0 <= spawn_y < GRID_HEIGHT): return False
            
        if self._is_occupied_float(spawn_x, int(spawn_y), 1, 1, ignore_team=team): return False

        player.mana -= cost
        unit_id = f"{team}_u_{self.tick_count}_{random.randint(1000,9999)}"
        unit = None
        
        if unit_type == "knight":
            unit = Knight(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 0.5
        elif unit_type == "archer":
            unit = Archer(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 0.5
        elif unit_type == "goblin":
            unit = Goblin(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 1.0
        elif unit_type == "orc":
            unit = Orc(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 0.33
        elif unit_type == "catapult":
            unit = Catapult(id=unit_id, team=team, x=spawn_x, y=spawn_y); unit.move_speed = 0.33
            
        if unit:
            self.entities.append(unit)
            return True
        return False

    def build_structure(self, team: str, building_type: str, x: int, y: int):
        player = self.players[team]
        valid_zone = False
        # Fix: Build zone must not block spawn points (x=3 and x=16)
        # Blue Spawn=3. Build Zone: 4-8
        # Red Spawn=16. Build Zone: 11-15 (left of spawn)
        if team == "blue" and 4 <= x <= 8: valid_zone = True
        elif team == "red" and (GRID_WIDTH - 13) <= x <= (GRID_WIDTH - 9): valid_zone = True
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

    def _is_occupied_float(self, x: float, y: int, width: int = 1, height: int = 1, exclude_id: str = None, ignore_team: str = None) -> bool:
        for e in self.entities:
            if e.id == exclude_id or e.hp <= 0: continue
            if ignore_team and e.team == ignore_team: continue
            if (x < e.x + e.width and x + width > e.x and
                y < e.y + e.height and y + height > e.y):
                return True
        return False

    def _dist(self, e1, e2):
        import math
        return math.sqrt((e1.x - e2.x)**2 + (e1.y - e2.y)**2)

    def _move_towards(self, entity, tx, ty, delta):
        import math
        dx = tx - entity.x
        dy = ty - entity.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist <= delta:
            # Reached (or overshot, just snap)
            # Check collision at target
            if not self._is_occupied_float(tx, ty, entity.width, entity.height, exclude_id=entity.id):
                entity.x = tx
                entity.y = ty
                return True
            return False # Blocked at target
        
        ratio = delta / dist
        next_x = entity.x + dx * ratio
        next_y = entity.y + dy * ratio
        
        # Check collision
        if 0 <= next_x < GRID_WIDTH and 0 <= next_y < GRID_HEIGHT:
             if not self._is_occupied_float(next_x, next_y, entity.width, entity.height, exclude_id=entity.id):
                 entity.x = next_x
                 entity.y = next_y
                 return False 
        return False

    def run_tick(self):
        from copy import deepcopy
        self.last_turn_snapshot = deepcopy(self.entities)
        self.tick_count += 1
        
        for p in self.players.values():
            p.mana = min(p.mana + MANA_REGEN, 10.0) 
            if p.base.hp <= 0: p.base.hp = 0

        active_units = [e for e in self.entities if e.hp > 0 and e.type == "unit"]
        # Buildings also attack but don't move
        active_buildings = [e for e in self.entities if e.hp > 0 and e.type == "building" and getattr(e, 'function', '') == 'attack']
        
        # Process Buildings (Simple Auto-Attack)
        for b in active_buildings:
            attack_cooldown = getattr(b, 'attack_speed', 1)
            if (self.tick_count - getattr(b, 'last_attack_tick', 0)) < attack_cooldown: continue
            
            enemies = [e for e in self.entities if e.team != b.team and e.hp > 0]
            target = None
            min_dist = 999
            rng = getattr(b, 'range', 3)
            
            for e in enemies:
                d = self._dist(b, e)
                if d <= rng and d < min_dist:
                    min_dist = d
                    target = e
            
            if target:
                damage = getattr(b, 'damage', 5)
                target.hp -= damage
                b.last_attack_tick = self.tick_count

        # Process Units (Move & Attack)
        for unit in active_units:
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
                        unit.command = None # Target dead/gone
                elif cmd.type == "stop":
                    unit.command = None
                    continue

            # B. Default AI
            if not unit.command:
                # Find closest enemy
                enemies = [e for e in self.entities if e.team != unit.team and e.hp > 0]
                closest = None
                min_dist = 999
                
                # Simple AI: Look for enemies in agro range (e.g. 8)
                agro_range = 8.0
                
                for e in enemies:
                    d = self._dist(unit, e)
                    if d <= agro_range and d < min_dist:
                        min_dist = d
                        closest = e
                
                if closest:
                    target_unit = closest
                    intent = "attack"
                else:
                    # Move to enemy base
                    enemy_base_x = GRID_WIDTH - 2 if unit.team == "blue" else 1
                    # Stay in lane if moving to base
                    target_pos = (enemy_base_x, unit.y)
                    intent = "move"

            # Execute Intent
            speed = getattr(unit, 'move_speed', 0.5)
            # Override speed for specific units if not set correctly in spawn
            # (Ideally set in spawn_unit)
            
            atk_range = getattr(unit, 'range', 1)
            atk_cooldown = getattr(unit, 'attack_speed', 1)
            
            if intent == "attack" and target_unit:
                # Robust Edge Distance Check
                x_dist = 0
                if unit.x + unit.width <= target_unit.x:
                    x_dist = target_unit.x - (unit.x + unit.width)
                elif target_unit.x + target_unit.width <= unit.x:
                    x_dist = unit.x - (target_unit.x + target_unit.width)
                
                y_dist = 0
                if unit.y + unit.height <= target_unit.y:
                    y_dist = target_unit.y - (unit.y + unit.height)
                elif target_unit.y + target_unit.height <= unit.y:
                    y_dist = unit.y - (target_unit.y + target_unit.height)
                
                import math
                edge_dist = math.sqrt(x_dist**2 + y_dist**2)
                
                if edge_dist <= atk_range + 0.1:
                    # Attack
                    if (self.tick_count - getattr(unit, 'last_attack_tick', 0)) >= atk_cooldown:
                        damage = getattr(unit, 'damage', 1)
                        # Bonus logic
                        bonus = getattr(unit, 'bonus_vs_building', 0)
                        if target_unit.type in ["building", "base"]: damage += bonus
                        
                        target_unit.hp -= damage
                        unit.last_attack_tick = self.tick_count
                        
                        if target_unit.hp <= 0:
                             self.players[unit.team].mana = min(self.players[unit.team].mana + 1.0, 10.0)
                else:
                    # Move towards target
                    self._move_towards(unit, target_unit.x, target_unit.y, speed)
            
            elif intent == "move" and target_pos:
                reached = self._move_towards(unit, target_pos[0], target_pos[1], speed)
                if reached and unit.command:
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
