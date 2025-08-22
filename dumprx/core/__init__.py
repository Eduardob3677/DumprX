import os
import sys
from pathlib import Path

def get_project_root():
    return Path(__file__).parent.parent

def get_bin_dir():
    return get_project_root() / "bin"

def get_utils_dir():
    return get_project_root() / "utils"

def get_input_dir():
    return get_project_root() / "input"

def get_output_dir():
    return get_project_root() / "out"

def get_temp_dir():
    return get_output_dir() / "tmp"

def setup_directories():
    for dir_path in [get_input_dir(), get_output_dir(), get_temp_dir()]:
        dir_path.mkdir(parents=True, exist_ok=True)

def cleanup_temp():
    import shutil
    temp_dir = get_temp_dir()
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)