import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

class PacExtractor:
    def __init__(self, config):
        self.config = config
        self.utils_dir = Path(__file__).parent.parent / "utils"
        
    def extract(self, pac_file, output_dir):
        console.print("PAC file detected")
        
        pac_extractor = self.utils_dir / "pacextractor" / "python" / "pacExtractor.py"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        cmd = f'python3 "{pac_extractor}" "{pac_file}" "{output_dir}"'
        result = subprocess.run(cmd, shell=True, cwd=output_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"PAC extraction failed: {result.stderr}")
        
        console.print("PAC extraction completed")
        return [str(output_dir)]