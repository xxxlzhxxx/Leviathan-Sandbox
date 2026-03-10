import typer
import sys
import yaml
import json
import time
from pathlib import Path
from rich.console import Console
from rich.progress import track
from clash_of_agents.core.game import Game
from clash_of_agents.core.agent import RandomAgent, ScriptedAgent, VolcAgent

app = typer.Typer()
console = Console()

@app.command()
def init(name: str = "my_bot"):
    """Initialize a new strategy file in strategies/ directory."""
    config = {
        "name": name,
        "api_key": "sk-placeholder",
        "system_prompt": "You are a strategic genius.",
        "deck": ["knight", "archer"]
    }
    
    # Ensure strategies dir exists
    Path("strategies").mkdir(exist_ok=True)
    
    filename = f"strategies/{name}.yaml"
    with open(filename, "w") as f:
        yaml.dump(config, f)
    console.print(f"[green]Created {filename}[/green]")

@app.command()
def fight(
    strategy_path: str, 
    opponent_path: str = typer.Argument(None, help="Path to opponent strategy file. If not provided, uses scripted_bot."), 
    use_volc: bool = False,
    debug: bool = False
):
    """Start a battle simulation."""
    if not Path(strategy_path).exists():
        console.print(f"[red]Strategy file {strategy_path} not found![/red]")
        raise typer.Exit(code=1)
        
    # Load Blue Strategy
    with open(strategy_path) as f:
        blue_strategy = yaml.safe_load(f)
        
    # Load Red Strategy (Opponent)
    red_strategy = {}
    opponent_name = "Scripted Bot"
    
    if opponent_path:
        if not Path(opponent_path).exists():
            console.print(f"[red]Opponent file {opponent_path} not found![/red]")
            raise typer.Exit(code=1)
        with open(opponent_path) as f:
            red_strategy = yaml.safe_load(f)
        opponent_name = red_strategy.get("name", "Opponent")
    
    console.print(f"[bold blue]Starting simulation: {blue_strategy.get('name', 'Blue')} vs {opponent_name}[/bold blue]")
    if use_volc:
        console.print("[bold yellow]Using VolcEngine Agent[/bold yellow]")
    
    game = Game()
    
    # Initialize Agents
    
    # Blue Agent
    if use_volc or "api_key" in blue_strategy:
        blue_agent = VolcAgent(
            team="blue", 
            system_prompt=blue_strategy.get("system_prompt", ""),
            api_key=blue_strategy.get("api_key", ""),
            debug=debug
        )
    else:
        blue_agent = RandomAgent(team="blue", system_prompt=blue_strategy.get("system_prompt", ""))
        
    # Red Agent
    if opponent_path:
        # If yaml provided, use VolcAgent (if key present) or Scripted
        if "api_key" in red_strategy:
             red_agent = VolcAgent(
                team="red",
                system_prompt=red_strategy.get("system_prompt", ""),
                api_key=red_strategy.get("api_key", ""),
                debug=debug
            )
        else:
            red_agent = ScriptedAgent(team="red")
    else:
        # Default fallback
        red_agent = ScriptedAgent(team="red")
    
    ticks = []
    
    # We use Game's own log system now
    # The Game class internally logs to self.replay_log
    
    for _ in track(range(300), description="Simulating battle..."):
        # 1. Ask Agents for Actions (Every 10 ticks = 1 second)
        # In a real turn-based game, this might be every tick or phased.
        # User said "Turn Based", so let's say every 10 ticks is a "Round" where they can act.
        
        if game.tick % 10 == 0:
            # Blue Turn
            blue_state = game.get_state("blue")
            blue_action = blue_agent.decide(blue_state)
            game.process_action("blue", blue_action)
            
            # Red Turn
            red_state = game.get_state("red")
            red_action = red_agent.decide(red_state)
            game.process_action("red", red_action)

        # 2. Run Engine Physics/Logic
        game.run_tick()
        
        if game.winner:
            break
            
    # Save replay using game's method which produces cleaner output
    
    # Generate filename: p1_p2_timestamp.json
    p1_name = blue_strategy.get("name", "Blue").replace(" ", "")
    p2_name = red_strategy.get("name", opponent_name).replace(" ", "")
    timestamp = int(time.time())
    
    # Create replays directory if not exists (although we did mkdir, good to be safe)
    Path("replays").mkdir(exist_ok=True)
    
    replay_filename = f"replays/{p1_name}_{p2_name}_{timestamp}.json"
    
    game.save_replay(replay_filename)
        
    console.print(f"[green]Simulation complete! Winner: {game.winner}[/green]")
    console.print(f"[green]Saved to {replay_filename}[/green]")
    
    # Mock Upload
    console.print("[yellow]Uploading battle results to server...[/yellow]")
    # In reality: requests.post("https://api.coa.com/upload", files=...)
    time.sleep(1) 
    mock_url = f"https://viewer.coa.com/?id={game.winner}_victory_{timestamp}"
    console.print(f"[bold blue]Battle Replay Available at:[/bold blue] {mock_url}")
    
    console.print("Open web/index.html to view the battle locally.")

if __name__ == "__main__":
    app()
