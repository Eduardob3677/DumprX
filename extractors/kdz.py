import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

class KdzExtractor:
    def __init__(self, config):
        self.config = config
        self.bin_dir = Path(__file__).parent.parent / "bin"
        self.utils_dir = Path(__file__).parent.parent / "utils"
        
    def extract(self, kdz_file, output_dir):
        console.print("LG KDZ Detected")
        
        kdz_extract = self.utils_dir / "kdztools" / "unkdz.py"
        dz_extract = self.utils_dir / "kdztools" / "undz.py"
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        cmd = f'python3 "{kdz_extract}" -f "{Path(kdz_file).name}" -x -o "./"'
        result = subprocess.run(cmd, shell=True, cwd=output_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"KDZ extraction failed: {result.stderr}")
        
        dz_files = list(output_path.glob("*.dz"))
        if dz_files:
            dz_file = dz_files[0]
            console.print("Extracting All Partitions As Individual Images")
            
            cmd = f'python3 "{dz_extract}" -f "{dz_file.name}" -s -o "./"'
            result = subprocess.run(cmd, shell=True, cwd=output_dir, capture_output=True, text=True)
            
            if result.returncode != 0:
                console.print(f"[yellow]Warning: DZ extraction had issues: {result.stderr}[/yellow]")
        
        return [str(output_dir)]