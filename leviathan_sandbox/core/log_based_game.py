"""
Log-based Game Runner for P2P synchronization.

This module provides a game runner that uses the log as the message bus.
Both players read state from and write actions to the shared log file.
"""

import time
from pathlib import Path
from typing import Optional, Callable
from leviathan_sandbox.core.game import Game
from leviathan_sandbox.core.protocol import Action
from leviathan_sandbox.core.sync_protocol import GameLog, LogEntryType


class LogBasedGameRunner:
    """
    Game runner that uses a log file as the synchronization mechanism.

    Flow:
    1. Initialize game and clear log
    2. For each turn:
       a. Write state for both players
       b. Wait for both players to submit actions
       c. Execute actions and write tick result
    3. Write game over when done
    """

    def __init__(self, log_path: str, game: Optional[Game] = None):
        self.log = GameLog(log_path)
        self.game = game if game else Game()

    def start(self, max_wait_per_action: int = 300):
        """
        Start the game and run until completion.

        Args:
            max_wait_per_action: Seconds to wait for each player's action
        """
        # Clear log for new game
        self.log.clear()

        # Write initial state (turn 0)
        self._write_initial_state()

        turn = 0
        while not self.game.winner and turn < self.game.max_turns:
            turn += 1

            # Wait for both players to submit actions
            actions = self.log.wait_for_actions(turn, timeout=max_wait_per_action)

            # Execute actions
            self.game.process_action("blue", actions["blue"])
            self.game.process_action("red", actions["red"])

            # Run game tick
            self.game.run_tick()

            # Write tick result to log
            blue_state = self.game.get_state("blue")
            red_state = self.game.get_state("red")
            self.log.write_tick_result(
                turn,
                blue_state,
                red_state,
                self.game.winner
            )

            # Check for game over
            if self.game.winner:
                self._write_game_over()

            print(f"Turn {turn}: Blue HP={int(self.game.players['blue'].base.hp)}, "
                  f"Red HP={int(self.game.players['red'].base.hp)}, "
                  f"Winner={self.game.winner}")

        return self.game.winner

    def _write_initial_state(self):
        """Write initial state for turn 0."""
        blue_state = self.game.get_state("blue")
        red_state = self.game.get_state("red")

        # Write initial state for both players
        self.log.write_state("blue", blue_state)
        self.log.write_state("red", red_state)

    def _write_game_over(self):
        """Write game over entry."""
        self.log.write_entry(LogEntryType.GAME_OVER, {
            "winner": self.game.winner,
            "final_turn": self.game.tick_count,
            "blue_hp": int(self.game.players["blue"].base.hp),
            "red_hp": int(self.game.players["red"].base.hp)
        })


class InteractiveGameRunner:
    """
    Interactive game runner where a human/agent plays via the log.

    This is designed for the coding agent scenario where:
    - The agent reads state from log
    - The agent writes action to log
    - This runner monitors the log and advances the game
    """

    def __init__(self, log_path: str):
        self.log_path = log_path
        self.log = GameLog(log_path)
        self.game = Game()
        self.last_processed_turn = 0
        self.action_wait_timeout = 300  # 5 minutes default

    def initialize(self):
        """Initialize a new game."""
        self.game = Game()
        self.last_processed_turn = 0
        self.log.clear()
        self._write_initial_state()
        print(f"Game initialized. Log: {self.log_path}")
        return self.game.tick_count

    def _write_initial_state(self):
        """Write initial state for turn 0."""
        blue_state = self.game.get_state("blue")
        red_state = self.game.get_state("red")
        self.log.write_state("blue", blue_state)
        self.log.write_state("red", red_state)

    def poll_and_advance(self) -> dict:
        """
        Poll for new actions and advance the game if ready.

        Returns:
            dict with status: "waiting", "turn_complete", "game_over"
        """
        # Check if we already processed this turn
        current_turn = self.game.tick_count

        # Get actions for current turn
        actions = self.log.get_actions_for_turn(current_turn)

        # Check if both actions are present
        if actions["blue"] is not None and actions["red"] is not None:
            # Both actions received, process them
            blue_action = Action(**actions["blue"]) if actions["blue"] else Action(type="pass")
            red_action = Action(**actions["red"]) if actions["red"] else Action(type="pass")

            # Execute actions
            self.game.process_action("blue", blue_action)
            self.game.process_action("red", red_action)

            # Run game tick
            self.game.run_tick()

            # Write new state
            blue_state = self.game.get_state("blue")
            red_state = self.game.get_state("red")
            self.log.write_tick_result(
                current_turn,
                blue_state,
                red_state,
                self.game.winner
            )

            self.last_processed_turn = current_turn

            if self.game.winner:
                return {
                    "status": "game_over",
                    "winner": self.game.winner,
                    "turn": current_turn
                }

            return {
                "status": "turn_complete",
                "turn": current_turn,
                "blue_hp": int(self.game.players["blue"].base.hp),
                "red_hp": int(self.game.players["red"].base.hp)
            }

        # Check if we need to write state for new turn
        entries = self.log.read_all()
        latest_turn = 0
        has_state_for_current = False

        for entry in entries:
            if entry["type"] in [LogEntryType.STATE.value, LogEntryType.TICK.value]:
                entry_turn = entry["data"].get("turn", 0)
                if entry_turn >= current_turn:
                    has_state_for_current = True

        if not has_state_for_current:
            # Write state for current turn
            blue_state = self.game.get_state("blue")
            red_state = self.game.get_state("red")
            self.log.write_state("blue", blue_state)
            self.log.write_state("red", red_state)

        # Check whose action is missing
        missing = []
        if actions["blue"] is None:
            missing.append("blue")
        if actions["red"] is None:
            missing.append("red")

        return {
            "status": "waiting",
            "turn": current_turn,
            "waiting_for": missing,
            "blue_hp": int(self.game.players["blue"].base.hp),
            "red_hp": int(self.game.players["red"].base.hp)
        }

    def get_state_for_team(self, team: str):
        """Get current game state for a specific team."""
        return self.game.get_state(team)

    def get_game_status(self) -> dict:
        """Get current game status."""
        return self.log.get_game_status()


def create_p2p_battle(
    log_path: str,
    blue_strategy: str,
    red_strategy: str,
    api_key: str,
    model: str = "ep-20260224155825-66kc4"
) -> str:
    """
    Create a P2P battle log that both players can participate in.

    Args:
        log_path: Path to the shared log file
        blue_strategy: Strategy prompt for blue player
        red_strategy: Strategy prompt for red player
        api_key: API key for LLM calls
        model: Model to use

    Returns:
        Initial turn number
    """
    from leviathan_sandbox.core.agent import VolcAgent

    runner = InteractiveGameRunner(log_path)
    turn = runner.initialize()

    # Store strategies in log metadata for agents to read
    runner.log.write_entry(LogEntryType.STATE, {
        "turn": 0,
        "metadata": {
            "blue_strategy": blue_strategy,
            "red_strategy": red_strategy,
            "api_key": api_key,
            "model": model
        }
    })

    return turn