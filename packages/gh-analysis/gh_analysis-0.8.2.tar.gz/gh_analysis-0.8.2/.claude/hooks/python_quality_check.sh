#!/bin/bash

# PostToolUse hook for running black, ruff, and mypy on Python file edits
# This script reads JSON input from stdin and processes Python files

# Read JSON input from stdin
input=$(cat)

# Extract file path from the JSON input
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Check if we got a valid file path
if [ -z "$file_path" ] || [ "$file_path" = "null" ]; then
    exit 0
fi

# Check if the file is a Python file
if [[ "$file_path" != *.py ]]; then
    exit 0
fi

# Check if the file exists
if [ ! -f "$file_path" ]; then
    exit 0
fi

# Get the directory containing the file to run commands from the correct location
file_dir=$(dirname "$file_path")
file_name=$(basename "$file_path")

# Change to the file directory
cd "$file_dir" || exit 0

# Run black (auto-formatting)
echo "Running black on $file_path..." >&2
uv run black "$file_name"

# Run ruff check with auto-fix but skip unused import removal (F401)
# This prevents the hook from removing imports that agents are still working on
echo "Running ruff on $file_path..." >&2
uv run ruff check --fix --unsafe-fixes --ignore F401 "$file_name"

# Run mypy (type checking) - this should not auto-fix, just report
echo "Running mypy on $file_path..." >&2
uv run mypy "$file_name"

exit 0