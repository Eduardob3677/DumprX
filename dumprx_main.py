#!/usr/bin/env python3

import sys
from pathlib import Path

# Add current directory to Python path to allow importing dumprx
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from dumprx.cli import cli
    
    if __name__ == '__main__':
        cli()
except ImportError as e:
    print(f"Error: {e}")
    print("Please install DumprX dependencies:")
    print("  pip install -r requirements.txt")
    print("  pip install -e .")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)