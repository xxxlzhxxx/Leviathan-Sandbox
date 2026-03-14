import typer
import sys
import yaml
import json
import time
import os
from pathlib import Path
from rich.console import Console
from rich.progress import track
from leviathan_sandbox.core.game import Game
from leviathan_sandbox.core.agent import RandomAgent, ScriptedAgent, VolcAgent, AggressiveAgent, SiegeAgent
from leviathan_sandbox.core.renderer import HeadlessRenderer
from leviathan_sandbox.core.roster import OPPONENTS, get_opponent_by_id

app = typer.Typer()
console = Console()

@app.command()
def init(name: str = "my_bot"):
    """Initialize a new strategy file in strategies/ directory."""
    config = {
        "name": name,
        "type": "volc",
        "system_prompt": "You are a strategic genius.",
        "api_key": "YOUR_API_KEY_HERE" 
    }
    
    # Ensure strategies dir exists
    Path("strategies").mkdir(exist_ok=True)
    
    filename = f"strategies/{name}.yaml"
    with open(filename, "w") as f:
        yaml.dump(config, f)
    console.print(f"[green]Created {filename}[/green]")

@app.command()
def list_opponents():
    """List all available predefined opponents."""
    from rich.table import Table
    table = Table(title="Opponent Roster")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Difficulty", style="green")
    table.add_column("Description")
    
    for oid, data in OPPONENTS.items():
        table.add_row(oid, data["name"], data.get("difficulty", "Unknown"), data.get("description", ""))
    
    console.print(table)

@app.command()
def battle(
    my_prompt: str = typer.Option(None, help="Your strategy prompt string"),
    opponent: str = typer.Option("aggressive", help="Opponent type or prompt string (Legacy)"),
    opponent_id: str = typer.Option(None, help="ID of the opponent from 'list-opponents'"),
    api_key: str = typer.Option(None, help="VolcEngine API Key (env: ARK_API_KEY)"),
    render: bool = typer.Option(True, help="Render battle to video"),
    debug: bool = False
):
    """Start a battle directly with prompts or opponent IDs."""
    
    # Resolve API Key
    final_api_key = api_key or os.environ.get("ARK_API_KEY")
    
    # Resolve Opponent
    red_agent = None
    opponent_name = opponent
    
    if opponent_id:
        data = get_opponent_by_id(opponent_id)
        if not data:
            console.print(f"[red]Error: Opponent ID {opponent_id} not found![/red]")
            raise typer.Exit(1)
        
        opponent_name = data["name"]
        opp_type = data.get("type", "random")
        
        if opp_type == "volc":
             if not final_api_key:
                 console.print("[red]Error: API Key required for AI opponent. Set ARK_API_KEY[/red]")
                 raise typer.Exit(1)
             red_agent = VolcAgent(team="red", system_prompt=data.get("prompt", ""), api_key=final_api_key, debug=debug)
        elif opp_type == "aggressive":
             red_agent = AggressiveAgent(team="red")
        elif opp_type == "siege":
             red_agent = SiegeAgent(team="red")
        elif opp_type == "scripted":
             red_agent = ScriptedAgent(team="red")
        elif opp_type == "random":
             red_agent = RandomAgent(team="red")
    
    # Fallback to string opponent if no ID
    if not red_agent:
        if opponent == "aggressive":
            red_agent = AggressiveAgent(team="red")
        elif opponent == "siege":
            red_agent = SiegeAgent(team="red")
        elif opponent == "scripted":
            red_agent = ScriptedAgent(team="red")
        elif opponent == "random":
            red_agent = RandomAgent(team="red")
        else:
            # Assume opponent string is a prompt
            if not final_api_key:
                 console.print("[red]Error: API Key required for AI opponent. Set ARK_API_KEY[/red]")
                 raise typer.Exit(1)
            red_agent = VolcAgent(team="red", system_prompt=opponent, api_key=final_api_key, debug=debug)

    console.print(f"[bold blue]Starting simulation: You vs {opponent_name}[/bold blue]")
    
    game = Game()
    
    # Blue Agent (You)
    if my_prompt:
        if not final_api_key:
            console.print("[red]Error: API Key required for custom prompt agent. Set ARK_API_KEY or use --api-key[/red]")
            raise typer.Exit(1)
        blue_agent = VolcAgent(team="blue", system_prompt=my_prompt, api_key=final_api_key, debug=debug)
    else:
        # Default to Aggressive if no prompt
        blue_agent = AggressiveAgent(team="blue")

    # Run Game Loop
    for _ in track(range(game.max_turns * 10), description="Simulating..."):
        game.tick(blue_agent, red_agent)
        if game.winner:
            break
            
    winner = game.winner.upper() if game.winner else "DRAW"
    console.print(f"[bold green]Game Over! Winner: {winner}[/bold green]")
    
    # Save Replay
    Path("replays").mkdir(exist_ok=True)
    timestamp = int(time.time())
    filename = f"replays/battle_{timestamp}.json"
    
    replay_data = game.get_replay_data()
    with open(filename, "w") as f:
        json.dump(replay_data, f)
    console.print(f"Replay saved to: {filename}")
    
    # Render Video
    if render:
        console.print("[bold cyan]Rendering video...[/bold cyan]")
        try:
            renderer = HeadlessRenderer(Path(filename), Path(f"replays/battle_{timestamp}.mp4"))
            video_path = renderer.render()
            console.print(f"[bold green]Video available at: {video_path}[/bold green]")
        except Exception as e:
            console.print(f"[red]Rendering failed: {e}[/red]")

@app.command()
def fight(
    strategy_path: str, 
    opponent_path: str = typer.Argument(None, help="Path to opponent strategy file. If not provided, uses scripted_bot."), 
    use_volc: bool = False,
    debug: bool = False
):
    """(Legacy) Start a battle using YAML strategy files."""
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
    blue_type = blue_strategy.get("type", "random")
    
    if use_volc or "api_key" in blue_strategy:
        blue_agent = VolcAgent(
            team="blue", 
            system_prompt=blue_strategy.get("system_prompt", ""),
            api_key=blue_strategy.get("api_key", ""),
            debug=debug
        )
    elif blue_type == "aggressive":
        blue_agent = AggressiveAgent(team="blue", system_prompt=blue_strategy.get("system_prompt", ""))
    elif blue_type == "siege":
        blue_agent = SiegeAgent(team="blue", system_prompt=blue_strategy.get("system_prompt", ""))
    else:
        blue_agent = RandomAgent(team="blue", system_prompt=blue_strategy.get("system_prompt", ""))
        
    # Red Agent
    if opponent_path:
        # If yaml provided, use VolcAgent (if key present) or Scripted
        red_type = red_strategy.get("type", "scripted")
        
        if "api_key" in red_strategy:
             red_agent = VolcAgent(
                team="red",
                system_prompt=red_strategy.get("system_prompt", ""),
                api_key=red_strategy.get("api_key", ""),
                debug=debug
            )
        elif red_type == "aggressive":
             red_agent = AggressiveAgent(team="red", system_prompt=red_strategy.get("system_prompt", ""))
        elif red_type == "siege":
             red_agent = SiegeAgent(team="red", system_prompt=red_strategy.get("system_prompt", ""))
        else:
            red_agent = ScriptedAgent(team="red")
    else:
        # Default fallback
        red_agent = ScriptedAgent(team="red")
    
    # Run Game Loop
    for _ in track(range(game.max_turns * 10), description="Simulating..."):
        game.tick(blue_agent, red_agent)
        if game.winner:
            break
            
    winner = game.winner.upper() if game.winner else "DRAW"
    console.print(f"[bold green]Game Over! Winner: {winner}[/bold green]")
    
    # Save Replay
    Path("replays").mkdir(exist_ok=True)
    timestamp = int(time.time())
    filename = f"replays/{blue_strategy.get('name', 'Blue')}_{opponent_name}_{timestamp}.json".replace(" ", "")
    
    replay_data = game.get_replay_data()
    with open(filename, "w") as f:
        json.dump(replay_data, f)
    console.print(f"Replay saved to: {filename}")

if __name__ == "__main__":
    app()
