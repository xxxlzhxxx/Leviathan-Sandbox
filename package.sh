#!/bin/bash
# Create a redistributable zip package (excluding venv and heavy caches)

ZIP_NAME="leviathan-sandbox-dist.zip"

echo "📦 Packaging project into $ZIP_NAME..."

# Exclude venv, __pycache__, .git, replays
zip -r $ZIP_NAME . \
    -x "*.venv*" \
    -x "*venv*" \
    -x "*.git*" \
    -x "*__pycache__*" \
    -x "replays/*" \
    -x ".DS_Store"

echo "✅ Created $ZIP_NAME"
echo "Distribute this file. Users just need to run ./install.sh inside."
