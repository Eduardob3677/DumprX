import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

class OfpExtractor:
    def __init__(self, config):
        self.config = config
        self.utils_dir = Path(__file__).parent.parent / "utils"
        
    def extract(self, ofp_file, output_dir):
        console.print("Decrypting OFP & extracting...")
        
        ofp_qc_decrypt = self.utils_dir / "oppo_decrypt" / "ofp_qc_decrypt.py"
        ofp_mtk_decrypt = self.utils_dir / "oppo_decrypt" / "ofp_mtk_decrypt.py"
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        cmd = f'uv run --with-requirements "{self.utils_dir}/oppo_decrypt/requirements.txt" "{ofp_qc_decrypt}" "{ofp_file}" "{output_dir}/out"'
        result = subprocess.run(cmd, shell=True, cwd=output_dir, capture_output=True, text=True)
        
        if result.returncode != 0 or not self._check_extraction_success(output_dir):
            console.print("QC decryption failed, trying MTK...")
            cmd = f'uv run --with-requirements "{self.utils_dir}/oppo_decrypt/requirements.txt" "{ofp_mtk_decrypt}" "{ofp_file}" "{output_dir}/out"'
            result = subprocess.run(cmd, shell=True, cwd=output_dir, capture_output=True, text=True)
            
            if result.returncode != 0 or not self._check_extraction_success(output_dir):
                raise Exception("OFP decryption error")
        
        out_dir = output_path / "out"
        if out_dir.exists():
            for item in out_dir.iterdir():
                item.rename(output_path / item.name)
            out_dir.rmdir()
        
        console.print("OFP extraction completed")
        return [str(output_dir)]
    
    def _check_extraction_success(self, output_dir):
        out_dir = Path(output_dir) / "out"
        if not out_dir.exists():
            return False
        
        boot_img = out_dir / "boot.img"
        userdata_img = out_dir / "userdata.img"
        
        return boot_img.exists() or userdata_img.exists()