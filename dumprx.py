#!/usr/bin/env python3

"""
DumprX - Modern Firmware Extraction and Analysis Tool

This is the new Python-based version of DumprX.
The original bash script (dumper.sh) is deprecated but still available.
"""

import sys
import os
from pathlib import Path

# Add the dumprx package to the Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from dumprx.cli import cli
    
    if __name__ == '__main__':
        cli()
        
except ImportError as e:
    print(f"Error importing DumprX modules: {e}")
    print("Please ensure all dependencies are installed:")
    print("  pip install -r requirements.txt")
    print("\nOr run the setup command:")
    print("  python3 dumprx.py setup")
    sys.exit(1)
except Exception as e:
    print(f"Error running DumprX: {e}")
    sys.exit(1)