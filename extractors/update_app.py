import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

class UpdateAppExtractor:
    def __init__(self, config):
        self.config = config
        self.splituapp = Path(__file__).parent / "splituapp.py"
        
    def extract(self, update_app_file, output_dir):
        console.print("Huawei UPDATE.APP Detected")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        partitions = self.config.get_partitions()
        
        cmd = f'python3 "{self.splituapp}" -f "{update_app_file}" -l super preas preavs'
        result = subprocess.run(cmd, shell=True, cwd=output_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            console.print("Trying individual partitions...")
            for partition in partitions:
                partition_name = partition.replace('.img', '')
                cmd = f'python3 "{self.splituapp}" -f "{update_app_file}" -l "{partition_name}"'
                result = subprocess.run(cmd, shell=True, cwd=output_dir, capture_output=True, text=True)
                if result.returncode != 0:
                    console.print(f"{partition} not found in UPDATE.APP")
        
        return [str(output_dir)]