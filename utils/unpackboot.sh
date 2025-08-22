#!/bin/bash

# unpackboot.sh - Backward compatibility wrapper for DumprX v2.0
# This script provides compatibility with the old unpackboot.sh interface

echo -e "\033[0;33mWarning: unpackboot.sh is deprecated. The boot unpacking functionality"
echo -e "has been integrated into the main DumprX Python CLI.\033[0m"
echo

if [ $# -lt 2 ]; then
    echo -e "\033[0;31mUsage: $0 [boot.img] [output_dir]\033[0m"
    echo -e "\033[0;33mFor the new interface, use: dumprx extract [firmware_file]\033[0m"
    exit 1
fi

BOOT_IMG="$1"
OUTPUT_DIR="$2"

if [ ! -f "$BOOT_IMG" ]; then
    echo -e "\033[0;31mError: Boot image not found: $BOOT_IMG\033[0m"
    exit 1
fi

# Use Python to unpack the boot image
python3 -c "
from dumprx.utils.boot import BootUnpacker
from dumprx.core.config import config
from pathlib import Path
import sys

unpacker = BootUnpacker(config)
result = unpacker.unpack(Path('$BOOT_IMG'), Path('$OUTPUT_DIR'))
sys.exit(0 if result else 1)
"