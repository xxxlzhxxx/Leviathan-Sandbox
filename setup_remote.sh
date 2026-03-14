#!/bin/bash
set -e

REPO_URL="https://github.com/your-username/leviathan-sandbox"
ZIP_URL="$REPO_URL/archive/refs/heads/main.zip"
INSTALL_DIR="leviathan-sandbox"

echo "🐲 Leviathan Sandbox - Instant Setup"
echo "===================================="

# 1. Check Dependencies (Python & unzip)
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 required."
    exit 1
fi

# 2. Download & Unzip
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Directory '$INSTALL_DIR' already exists."
    read -p "Overwrite? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    rm -rf "$INSTALL_DIR"
fi

echo "⬇️  Downloading game files..."
# If curl exists
if command -v curl &> /dev/null; then
    curl -L -o repo.zip "$ZIP_URL"
elif command -v wget &> /dev/null; then
    wget -O repo.zip "$ZIP_URL"
else
    echo "❌ curl or wget required to download."
    exit 1
fi

echo "📦 Unpacking..."
unzip -q repo.zip
# GitHub zip usually extracts to repo-name-branch
mv leviathan-sandbox-main "$INSTALL_DIR" 2>/dev/null || mv leviathan-sandbox-master "$INSTALL_DIR" 2>/dev/null || true
rm repo.zip

cd "$INSTALL_DIR"

# 3. Run Install Script
if [ -f "install.sh" ]; then
    chmod +x install.sh start.sh
    ./install.sh
else
    echo "❌ Installer not found in downloaded files."
    exit 1
fi

echo ""
echo "🎉 Setup Complete!"
echo "================================================="
echo ""
echo "🎮 What can you do now?"
echo ""
echo "1. ⚔️  Run a Quick Battle (You vs Siege Bot):"
echo "   cd $INSTALL_DIR && ./start.sh battle --opponent siege --render"
echo ""
echo "2. 🧠  Command with AI (Requires API Key):"
echo "   export ARK_API_KEY='your-key'"
echo "   cd $INSTALL_DIR && ./start.sh battle --my-prompt 'Rush with mass Knights!' --opponent 'aggressive' --render"
echo ""
echo "3. 📺  Watch Replays:"
echo "   cd $INSTALL_DIR/web && python3 -m http.server 8001"
echo "   Then open http://localhost:8001"
