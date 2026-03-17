"""
Log-based Synchronization Protocol for Leviathan Sandbox

The game log serves as the message bus. Both players read from and write to the same log file.

Log Format (JSON Lines - one JSON per line):
- LOG_ENTRY types: "state", "action", "tick", "game_over"

Turn Flow:
1. Engine writes STATE (contains game state visible to a player)
2. Player Blue reads STATE, writes ACTION
3. Player Red reads STATE, writes ACTION
4. Engine reads both ACTIONS, runs tick, writes TICK result
5. Repeat until game over
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
from leviathan_sandbox.core.protocol import GameState, Action


class LogEntryType(str, Enum):
    STATE = "state"      # Game state (per player, with hidden info)
    ACTION = "action"    # Player action submission
    TICK = "tick"        # Tick result (state after processing)
    GAME_OVER = "game_over"


class GameLog:
    """
    Game log that serves as the message bus for P2P synchronization.
    Both players read/write to the same log file.
    """

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self._entry_index = 0

    def clear(self):
        """Clear the log file for a new game."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'w') as f:
            f.write("")
        self._entry_index = 0

    def write_entry(self, entry_type: LogEntryType, data: Dict[str, Any]):
        """Append a new entry to the log."""
        entry = {
            "index": self._entry_index,
            "type": entry_type.value,
            "timestamp": time.time(),
            "data": data
        }
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._entry_index += 1

    def read_all(self) -> List[Dict[str, Any]]:
        """Read all entries from the log."""
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries

    def read_new_entries(self, since_index: int = -1) -> List[Dict[str, Any]]:
        """Read entries newer than since_index."""
        all_entries = self.read_all()
        return [e for e in all_entries if e["index"] > since_index]

    def get_latest_state_for_team(self, team: str) -> Optional[GameState]:
        """Get the most recent state for a specific team."""
        entries = self.read_all()

        # First check TICK entries (most recent state after processing)
        for entry in reversed(entries):
            if entry["type"] == LogEntryType.TICK.value:
                data = entry["data"]
                state_key = f"{team}_state"
                if state_key in data:
                    state_data = data[state_key]
                    if state_data.get("target_team") == team:
                        return GameState(**state_data["state"])

        # Fallback to STATE entries (state before actions)
        for entry in reversed(entries):
            if entry["type"] == LogEntryType.STATE.value:
                data = entry["data"]
                if data.get("target_team") == team:
                    return GameState(**data["state"])

        return None

    def get_actions_for_turn(self, turn: int) -> Dict[str, Any]:
        """Get actions for a specific turn."""
        entries = self.read_all()
        blue_action = None
        red_action = None

        for entry in entries:
            if entry["type"] == LogEntryType.ACTION.value:
                data = entry["data"]
                if data.get("turn") == turn:
                    if data.get("team") == "blue":
                        blue_action = data.get("action")
                    elif data.get("team") == "red":
                        red_action = data.get("action")

        return {"blue": blue_action, "red": red_action}

    def wait_for_actions(self, turn: int, timeout: int = 300) -> Dict[str, Action]:
        """
        Wait for both players to submit their actions for a turn.
        Returns dict with blue and red actions (or None if timeout).
        """
        from leviathan_sandbox.core.protocol import Action

        start_time = time.time()
        while time.time() - start_time < timeout:
            actions = self.get_actions_for_turn(turn)
            if actions["blue"] is not None and actions["red"] is not None:
                # Both actions received
                blue_act = Action(**actions["blue"]) if actions["blue"] else Action(type="pass")
                red_act = Action(**actions["red"]) if actions["red"] else Action(type="pass")
                return {"blue": blue_act, "red": red_act}
            time.sleep(0.5)

        # Return what we have (may be None)
        blue_act = Action(**actions["blue"]) if actions.get("blue") else Action(type="pass")
        red_act = Action(**actions["red"]) if actions.get("red") else Action(type="pass")
        return {"blue": blue_act, "red": red_act}

    def write_state(self, team: str, state: GameState):
        """Write a state entry for a specific team."""
        # For opponent, hide sensitive info
        if team == "opponent":
            # Convert to dict and hide opponent data
            state_dict = state.model_dump()
            state_dict["opponent"] = {
                "team": state.opponent_team,
                "mana": 0,
                "base_hp": state.opponent.base_hp,
                "deck": []
            }
            state_dict["target_team"] = "opponent"
        else:
            state_dict = state.model_dump()
            state_dict["target_team"] = team

        self.write_entry(LogEntryType.STATE, {
            "turn": state.turn,
            "target_team": team,
            "state": state_dict
        })

    def write_action(self, team: str, turn: int, action: Action):
        """Write a player's action to the log."""
        self.write_entry(LogEntryType.ACTION, {
            "turn": turn,
            "team": team,
            "action": action.model_dump()
        })

    def write_tick_result(self, turn: int, blue_state: GameState, red_state: GameState, winner: Optional[str]):
        """Write the tick result after processing both actions."""
        self.write_entry(LogEntryType.TICK, {
            "turn": turn,
            "blue_state": {
                "target_team": "blue",
                "state": blue_state.model_dump()
            },
            "red_state": {
                "target_team": "red",
                "state": red_state.model_dump()
            }
        })

        if winner:
            self.write_entry(LogEntryType.GAME_OVER, {
                "winner": winner,
                "final_turn": turn
            })

    def get_game_status(self) -> Dict[str, Any]:
        """Get current game status."""
        entries = self.read_all()
        if not entries:
            return {"status": "not_started", "turn": 0}

        # Find latest turn
        latest_turn = 0
        winner = None
        for entry in reversed(entries):
            if entry["type"] == LogEntryType.TICK.value:
                latest_turn = entry["data"].get("turn", 0)
            elif entry["type"] == LogEntryType.GAME_OVER.value:
                winner = entry["data"].get("winner")
                break

        return {
            "status": "finished" if winner else "running",
            "turn": latest_turn,
            "winner": winner
        }


class LogBasedAgent:
    """
    Agent that reads game state from log and writes actions to log.
    Designed for coding agents (Cursor/Kiro/Claude Code) to interact with.
    """

    def __init__(self, team: str, log_path: str):
        self.team = team
        self.log = GameLog(log_path)
        self.last_read_index = -1

    def get_state(self) -> Optional[GameState]:
        """Read the latest game state from log."""
        state = self.log.get_latest_state_for_team(self.team)
        if state:
            # Update index to track new entries
            entries = self.log.read_all()
            if entries:
                self.last_read_index = entries[-1]["index"]
        return state

    def submit_action(self, turn: int, action: Action):
        """Write action to log."""
        self.log.write_action(self.team, turn, action)

    def wait_for_turn(self, current_turn: int, timeout: int = 300) -> Optional[GameState]:
        """
        Wait for the next turn's state to be available.
        Returns the new state when available, or None on timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if there's a new state for our turn
            new_entries = self.log.read_new_entries(self.last_read_index)
            for entry in new_entries:
                if entry["type"] == LogEntryType.STATE.value:
                    data = entry["data"]
                    if data.get("target_team") == self.team:
                        if data.get("turn") > current_turn:
                            self.last_read_index = entry["index"]
                            return GameState(**data["state"])
                elif entry["type"] == LogEntryType.TICK.value:
                    data = entry["data"]
                    state_key = f"{self.team}_state"
                    if state_key in data:
                        state_data = data[state_key]
                        if state_data.get("target_team") == self.team:
                            if data.get("turn") > current_turn:
                                self.last_read_index = entry["index"]
                                return GameState(**state_data["state"])
            time.sleep(0.5)
        return None