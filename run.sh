#!/bin/bash
# Navigate to the directory containing the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate the virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment 'venv' not found. Please create it first."
    exit 1
fi

# Run the game
python src/main.py
