import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

class OpsExtractor:
    def __init__(self, config):
        self.config = config
        self.utils_dir = Path(__file__).parent.parent / "utils"
        
    def extract(self, ops_file, output_dir):
        console.print("OPS file detected")
        
        ops_decrypt = self.utils_dir / "oppo_decrypt" / "opscrypto.py"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        cmd = f'uv run --with-requirements "{self.utils_dir}/oppo_decrypt/requirements.txt" "{ops_decrypt}" "{ops_file}" "{output_dir}"'
        result = subprocess.run(cmd, shell=True, cwd=output_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"OPS extraction failed: {result.stderr}")
        
        console.print("OPS extraction completed")
        return [str(output_dir)]