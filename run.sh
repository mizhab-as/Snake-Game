#!/bin/bash
# Snake Game - macOS/Linux launcher
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check for virtual environment, offer to create it if missing
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Setting up now..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo "Setup complete!"
else
    source venv/bin/activate
fi

echo "Starting Snake Game..."
python src/main.py
