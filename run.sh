#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --trusted-host pypi.org --trusted-host pypi.python.org \
        --trusted-host files.pythonhosted.org \
        dash plotly numpy kaleido
else
    source .venv/bin/activate
fi

echo "Starting PK Simulator at http://127.0.0.1:8050"
open "http://127.0.0.1:8050" &
python pharma_sim.py
