#!/usr/bin/env python3

import sys
from pathlib import Path

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from dumprx.cli import sync_main

if __name__ == "__main__":
    sys.exit(sync_main())