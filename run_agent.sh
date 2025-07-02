#!/bin/bash

# Check for exactly one argument
if [ $# -ne 1 ]; then
  echo "Usage: $0 <python_script_path>" >&2
  exit 1
fi
PYTHON_SCRIPT="$1"

# Determine script directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")

# Ensure write permissions for script directory
chmod u+w "$SCRIPT_DIR" || {
  echo "Error: Could not set write permissions for $SCRIPT_DIR" >&2
  exit 1
}

PROJECT_DIR="$SCRIPT_DIR"
echo "Project directory: $PROJECT_DIR"
echo "Python script to run: $PYTHON_SCRIPT"

# Change to project directory
cd "$PROJECT_DIR" || {
  echo "Error: Could not change to directory $PROJECT_DIR" >&2
  exit 1
}

# Set and activate virtual environment
echo "Activating virtual environment..."
VENV_ACTIVATE="$([[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]] && echo "$PROJECT_DIR/.venv/Scripts/activate" || echo "$PROJECT_DIR/.venv/bin/activate")"
[ ! -f "$VENV_ACTIVATE" ] && { echo "Error: Virtual environment activation script $VENV_ACTIVATE not found" >&2; exit 1; }
source "$VENV_ACTIVATE" || { echo "Error: Failed to activate virtual environment" >&2; exit 1; }
 
# Run Python script
echo "Running $PYTHON_SCRIPT..."
uv run "$PYTHON_SCRIPT" || { echo "Error: Failed to run $PYTHON_SCRIPT" >&2; exit 1; }