import os
import subprocess
from pathlib import Path
from typing import List, Optional
from dumprx.utils.logging import logger

class KDZTools:
    def __init__(self, config):
        self.config = config
        self.kdz_extract_script = config.python_tools['kdz_extract']
        self.dz_extract_script = config.python_tools['dz_extract']
        
    def extract_kdz(self, kdz_file: Path, output_dir: Path) -> bool:
        try:
            logger.info("Extracting KDZ file...")
            
            result = subprocess.run([
                'python3', str(self.kdz_extract_script),
                '-f', str(kdz_file),
                '-x', '-o', str(output_dir)
            ], capture_output=True, text=True, cwd=output_dir)
            
            if result.returncode != 0:
                logger.error(f"KDZ extraction failed: {result.stderr}")
                return False
                
            dz_files = list(output_dir.glob('*.dz'))
            if not dz_files:
                logger.error("No DZ files found after KDZ extraction")
                return False
                
            for dz_file in dz_files:
                if not self.extract_dz(dz_file, output_dir):
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"KDZ extraction failed: {e}")
            return False
    
    def extract_dz(self, dz_file: Path, output_dir: Path) -> bool:
        try:
            logger.info(f"Extracting DZ file: {dz_file.name}")
            
            result = subprocess.run([
                'python3', str(self.dz_extract_script),
                '-f', str(dz_file),
                '-s', '-o', str(output_dir)
            ], capture_output=True, text=True, cwd=output_dir)
            
            if result.returncode != 0:
                logger.error(f"DZ extraction failed: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"DZ extraction failed: {e}")
            return False

def extract_kdz_file(kdz_file: str, output_dir: str) -> bool:
    from dumprx.core.config import config
    tools = KDZTools(config)
    return tools.extract_kdz(Path(kdz_file), Path(output_dir))