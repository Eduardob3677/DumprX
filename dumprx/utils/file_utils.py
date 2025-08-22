import os
import shutil
from pathlib import Path

class FileUtils:
    @staticmethod
    def copy_file(src, dst):
        shutil.copy2(src, dst)
    
    @staticmethod
    def move_file(src, dst):
        shutil.move(src, dst)
    
    @staticmethod
    def remove_file(filepath):
        Path(filepath).unlink(missing_ok=True)
    
    @staticmethod
    def create_directory(dirpath):
        Path(dirpath).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_file_size(filepath):
        return Path(filepath).stat().st_size
    
    @staticmethod
    def is_binary_file(filepath):
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return False