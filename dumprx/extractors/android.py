import os
import subprocess
import sys
from pathlib import Path
from dumprx.core.config import Config
from dumprx.utils.console import console, info, success, warning

class AndroidExtractor:
    def __init__(self, config: Config):
        self.config = config
        self.utils_dir = Path(__file__).parent.parent.parent / "utils"
    
    def extract(self, input_path: str, output_dir: str) -> str:
        """Extract Android-specific formats"""
        filename = os.path.basename(input_path).lower()
        
        if 'payload.bin' in filename:
            return self._extract_payload(input_path, output_dir)
        elif filename.endswith('.dat') or filename.endswith('.dat.br'):
            return self._extract_sdat(input_path, output_dir)
        elif 'super' in filename and filename.endswith('.img'):
            return self._extract_super(input_path, output_dir)
        elif filename.endswith('.img'):
            return self._extract_partition_image(input_path, output_dir)
        else:
            return output_dir
    
    def extract_partition(self, img_path: str, output_dir: str, partition_name: str) -> None:
        """Extract individual partition image"""
        info(f"Extracting {partition_name} partition")
        
        partition_dir = os.path.join(output_dir, partition_name)
        os.makedirs(partition_dir, exist_ok=True)
        
        # Try different extraction methods
        if self._is_ext4_image(img_path):
            self._extract_ext4_image(img_path, partition_dir)
        elif self._is_erofs_image(img_path):
            self._extract_erofs_image(img_path, partition_dir)
        elif self._is_sparse_image(img_path):
            # Convert sparse to raw first
            raw_img = img_path.replace('.img', '_raw.img')
            self._convert_sparse_to_raw(img_path, raw_img)
            if self._is_ext4_image(raw_img):
                self._extract_ext4_image(raw_img, partition_dir)
            os.remove(raw_img)
        else:
            warning(f"Unknown partition format: {partition_name}")
    
    def _extract_payload(self, payload_path: str, output_dir: str) -> str:
        """Extract payload.bin using payload-dumper-go"""
        payload_dumper = self.utils_dir / "bin" / "payload-dumper-go"
        
        if not payload_dumper.exists():
            raise FileNotFoundError("payload-dumper-go not found")
        
        info("Extracting payload.bin")
        cmd = [str(payload_dumper), '-o', output_dir, payload_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Payload extraction failed: {result.stderr}")
        
        return output_dir
    
    def _extract_sdat(self, sdat_path: str, output_dir: str) -> str:
        """Extract system.new.dat files"""
        sdat2img_script = self.utils_dir / "sdat2img.py"
        
        if not sdat2img_script.exists():
            raise FileNotFoundError("sdat2img.py not found")
        
        # Find corresponding transfer list
        base_name = sdat_path.replace('.new.dat', '').replace('.dat', '')
        transfer_list = f"{base_name}.transfer.list"
        
        if not os.path.exists(transfer_list):
            raise FileNotFoundError(f"Transfer list not found: {transfer_list}")
        
        output_img = os.path.join(output_dir, f"{os.path.basename(base_name)}.img")
        
        info(f"Converting {os.path.basename(sdat_path)} to img")
        cmd = [sys.executable, str(sdat2img_script), transfer_list, sdat_path, output_img]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"sdat2img failed: {result.stderr}")
        
        return output_dir
    
    def _extract_super(self, super_img: str, output_dir: str) -> str:
        """Extract super.img using lpunpack"""
        lpunpack = self.utils_dir / "lpunpack"
        
        if not lpunpack.exists():
            raise FileNotFoundError("lpunpack not found")
        
        info("Extracting super.img")
        cmd = [str(lpunpack), super_img, output_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"lpunpack failed: {result.stderr}")
        
        return output_dir
    
    def _extract_partition_image(self, img_path: str, output_dir: str) -> str:
        """Extract partition image"""
        partition_name = Path(img_path).stem
        self.extract_partition(img_path, output_dir, partition_name)
        return output_dir
    
    def _is_ext4_image(self, img_path: str) -> bool:
        """Check if image is ext4 format"""
        try:
            with open(img_path, 'rb') as f:
                f.seek(0x438)
                magic = f.read(2)
                return magic == b'\x53\xef'
        except Exception:
            return False
    
    def _is_erofs_image(self, img_path: str) -> bool:
        """Check if image is EROFS format"""
        try:
            with open(img_path, 'rb') as f:
                f.seek(0x400)
                magic = f.read(4)
                return magic == b'\xe2\xe1\xf5\xe0'
        except Exception:
            return False
    
    def _is_sparse_image(self, img_path: str) -> bool:
        """Check if image is sparse format"""
        try:
            with open(img_path, 'rb') as f:
                magic = f.read(4)
                return magic == b'\x3a\xff\x26\xed'
        except Exception:
            return False
    
    def _extract_ext4_image(self, img_path: str, output_dir: str) -> None:
        """Extract ext4 image using 7zz"""
        bin_7zz = self._get_7zz_binary()
        
        cmd = [bin_7zz, 'x', img_path, f'-o{output_dir}', '-y']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            warning(f"Failed to extract {img_path} as ext4")
    
    def _extract_erofs_image(self, img_path: str, output_dir: str) -> None:
        """Extract EROFS image"""
        fsck_erofs = self.utils_dir / "bin" / "fsck.erofs"
        
        if fsck_erofs.exists():
            cmd = [str(fsck_erofs), '--extract', output_dir, img_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                warning(f"Failed to extract EROFS image: {img_path}")
        else:
            warning("fsck.erofs not available for EROFS extraction")
    
    def _convert_sparse_to_raw(self, sparse_img: str, raw_img: str) -> None:
        """Convert sparse image to raw"""
        simg2img = self.utils_dir / "bin" / "simg2img"
        
        if not simg2img.exists():
            raise FileNotFoundError("simg2img not found")
        
        cmd = [str(simg2img), sparse_img, raw_img]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"simg2img failed: {result.stderr}")
    
    def _get_7zz_binary(self) -> str:
        """Get 7zz binary path"""
        try:
            subprocess.run(['7zz'], capture_output=True)
            return '7zz'
        except FileNotFoundError:
            bin_7zz = self.utils_dir / "bin" / "7zz"
            if bin_7zz.exists():
                return str(bin_7zz)
            else:
                raise FileNotFoundError("7zz binary not found")