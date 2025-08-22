#!/bin/bash

# DumprX v2.0 - Backward compatibility wrapper
# This script provides compatibility with the old dumper.sh interface
# while using the new Python implementation underneath

# Check if dumprx is installed
if ! command -v dumprx > /dev/null 2>&1; then
    # Try to use it from the local installation
    if [ -f "$(dirname "$0")/venv/bin/dumprx" ]; then
        DUMPRX_CMD="$(dirname "$0")/venv/bin/dumprx"
    elif [ -f "$(dirname "$0")/dumprx/cli.py" ]; then
        DUMPRX_CMD="python3 $(dirname "$0")/dumprx/cli.py"
    else
        echo -e "\033[0;31mError: DumprX not found. Please run setup.sh first.\033[0m"
        exit 1
    fi
else
    DUMPRX_CMD="dumprx"
fi

# Forward all arguments to the new Python CLI
exec $DUMPRX_CMD "$@"