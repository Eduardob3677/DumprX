import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

class SdatExtractor:
    def __init__(self, config):
        self.config = config
        self.sdat2img = Path(__file__).parent / "sdat2img.py"
        
    def extract(self, sdat_file, output_dir):
        sdat_path = Path(sdat_file)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        base_name = sdat_path.stem
        if base_name.endswith('.new'):
            base_name = base_name[:-4]
        
        transfer_list = sdat_path.parent / f"{base_name}.transfer.list"
        new_dat = sdat_path
        output_img = output_path / f"{base_name}.img"
        
        if not transfer_list.exists():
            raise Exception(f"Transfer list not found: {transfer_list}")
        
        cmd = f'python3 "{self.sdat2img}" "{transfer_list}" "{new_dat}" "{output_img}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"SDAT extraction failed: {result.stderr}")
        
        console.print(f"Extracted {base_name}.img")
        return [str(output_img)]