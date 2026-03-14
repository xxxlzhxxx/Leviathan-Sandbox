---
name: "leviathan-setup"
description: "Setup guide for Leviathan Sandbox: dependencies, environment variables, and frontend. Invoke when user asks about installation or setup."
---

# Leviathan Sandbox Setup Guide

This skill helps you set up the environment for the Leviathan Sandbox RTS game project.

## 1. Prerequisites

- Python 3.8+
- Node.js (Optional, only if modifying frontend build, otherwise plain HTML/JS works)
- VolcEngine Ark Runtime API Key (for Asset Pipeline and VolcAgent)

## 2. Install Dependencies

Install the required Python packages:

```bash
pip install typer rich pyyaml volcenginesdkarkruntime openai rembg opencv-python-headless pillow numpy requests
```

Or if `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

## 3. Environment Variables

To use the AI features (Asset Generation, AI Bot), you need to set the `ARK_API_KEY`:

```bash
export ARK_API_KEY="your-api-key-here"
```

## 4. Run the Frontend Viewer

The game replay viewer is a static HTML page. To view replays, start a local HTTP server:

```bash
cd leviathan_sandbox/web
python3 -m http.server 8001
```

Then open your browser at: `http://localhost:8001/`

## 5. Quick Test

To verify everything is working, run a simple battle between two scripted bots:

```bash
python3 -m leviathan_sandbox.cli.main fight strategies/blue_assault.yaml strategies/red_siege.yaml
```

This should generate a `.json` replay file in the `replays/` directory.
