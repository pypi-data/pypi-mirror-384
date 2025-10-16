#!/bin/bash
# Helper script to run examples with proper PYTHONPATH

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Set PYTHONPATH to include src directory
export PYTHONPATH="$SCRIPT_DIR/src:$PYTHONPATH"

# Run the example
python "$@"

