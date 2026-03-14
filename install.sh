#!/bin/bash
set -e

echo "🐲 Leviathan Sandbox - AI-Friendly One-Click Setup"
echo "================================================"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python 3 detected."

# 2. Create Virtual Environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment in $VENV_DIR..."
    python3 -m venv $VENV_DIR
fi

# Activate venv
source $VENV_DIR/bin/activate
echo "✅ Virtual environment activated."

# 3. Install Dependencies
echo "⬇️  Installing dependencies..."
pip install --upgrade pip
# Install current directory as editable package
pip install -e .

echo "✅ Dependencies installed."

# 4. Verify Installation
if command -v leviathan-sandbox &> /dev/null; then
    echo ""
    echo "🎉 Installation Successful! You are ready to play."
    echo "================================================="
    echo ""
    echo "🎮 What can you do now?"
    echo ""
    echo "1. ⚔️  Run a Quick Battle (You vs Siege Bot):"
    echo "   ./start.sh battle --opponent siege --render"
    echo ""
    echo "2. 🧠  Command with AI (Requires API Key):"
    echo "   export ARK_API_KEY='your-key'"
    echo "   ./start.sh battle --my-prompt 'Rush with mass Knights!' --opponent 'aggressive' --render"
    echo ""
    echo "3. 📺  Watch Replays:"
    echo "   cd web && python3 -m http.server 8001"
    echo "   Then open http://localhost:8001"
    echo ""
    echo "💡 Tip: Video files are saved in the 'replays/' folder."
else
    echo "❌ Installation failed. 'leviathan-sandbox' command not found."
    exit 1
fi
