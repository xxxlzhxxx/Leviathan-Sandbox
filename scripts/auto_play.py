import json
import time
import os
import random
import subprocess
import sys
from pathlib import Path

def run_battle(opponent_id, strategy_name):
    print(f"\n[COMMANDER TRAE] Battle Start! Strategy: {strategy_name} vs Opponent: {opponent_id}")
    
    state_file = Path("current_state.json")
    action_file = Path("current_action.json")
    if state_file.exists(): state_file.unlink()
    if action_file.exists(): action_file.unlink()

    cmd = ["leviathan-sandbox", "battle", "--interactive", "--opponent-id", str(opponent_id), "--no-render"]
    process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, text=True)

    all_actions = []

    try:
        while process.poll() is None:
            if state_file.exists():
                try:
                    with open(state_file, "r") as f:
                        state = json.load(f)
                    
                    turn = state.get("turn", 0)
                    mana = state["me"].get("mana", 0)
                    
                    # LOGIC & LOGGING
                    print(f"\n--- Turn {turn} Decision ---")
                    print(f"Status: Mana={mana}, BlueHP={state['me']['base_hp']}, RedHP={state['opponent']['base_hp']}")
                    
                    action = {"type": "pass", "card_id": "", "y": 0, "commands": []}
                    
                    # 1. Micro-commands
                    my_units = [e for e in state['entities'] if e['team'] == state['my_team'] and e['type'] == 'unit']
                    for u in my_units[:3]:
                        action["commands"].append({
                            "unit_id": u["id"],
                            "type": "move",
                            "target_x": 210
                        })

                    # 2. Strategy (Defend & Counter)
                    lane = random.randint(0, 2)
                    if turn == 0:
                        action.update({"type": "spawn", "card_id": "knight", "y": 1})
                        print(">> Opening: Spawn Knight in Lane 1")
                    elif mana >= 8:
                        action.update({"type": "spawn", "card_id": "catapult", "y": lane})
                        print(f">> Heavy Fire: Deploying Catapult in Lane {lane}")
                    elif any(e['x'] < 100 for e in state['entities'] if e['team'] != state['my_team']) and mana >= 2:
                        action.update({"type": "build", "card_id": "wall", "x": 5, "y": lane})
                        print(f">> Emergency: Building Wall in Lane {lane}")
                    elif mana >= 6:
                        action.update({"type": "spawn", "card_id": "archer", "y": lane})
                        print(f">> Support: Deploying Archer in Lane {lane}")
                    else:
                        print(">> Strategic Saving: Mana too low, passing...")

                    all_actions.append({"turn": turn, "action": action})

                    with open(action_file, "w") as f:
                        json.dump(action, f)
                    
                    state_file.unlink()
                    
                except Exception as e:
                    time.sleep(0.1)
            
            time.sleep(0.2)

    except KeyboardInterrupt:
        process.terminate()
    
    print("\n[BATTLE FINISHED]")
    with open("commander_trae_log.json", "w") as f:
        json.dump(all_actions, f, indent=2)
    print("Full action log saved to: commander_trae_log.json")

if __name__ == "__main__":
    run_battle(sys.argv[1], sys.argv[2])
