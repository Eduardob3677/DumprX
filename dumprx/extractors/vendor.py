import os
import subprocess
import sys
from pathlib import Path
from dumprx.core.config import Config
from dumprx.utils.console import console, info, warning

class VendorExtractor:
    def __init__(self, config: Config):
        self.config = config
        self.utils_dir = Path(__file__).parent.parent.parent / "utils"
    
    def extract(self, input_path: str, output_dir: str) -> str:
        """Extract vendor-specific firmware formats"""
        filename = os.path.basename(input_path).lower()
        extension = Path(input_path).suffix.lower()
        
        if extension == '.kdz':
            return self._extract_kdz(input_path, output_dir)
        elif extension == '.dz':
            return self._extract_dz(input_path, output_dir)
        elif extension == '.ozip':
            return self._extract_ozip(input_path, output_dir)
        elif extension in ['.ofp', '.ops']:
            return self._extract_ofp_ops(input_path, output_dir, extension)
        elif extension == '.nb0':
            return self._extract_nb0(input_path, output_dir)
        elif extension == '.pac':
            return self._extract_pac(input_path, output_dir)
        elif filename.startswith('ruu_') and filename.endswith('.exe'):
            return self._extract_ruu(input_path, output_dir)
        elif 'update.app' in filename:
            return self._extract_update_app(input_path, output_dir)
        else:
            warning(f"Unknown vendor format: {filename}")
            return output_dir
    
    def _extract_kdz(self, kdz_path: str, output_dir: str) -> str:
        """Extract LG KDZ files"""
        kdz_extract = self.utils_dir / "kdztools" / "unkdz.py"
        
        if not kdz_extract.exists():
            raise FileNotFoundError("unkdz.py not found")
        
        info("Extracting LG KDZ file")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(output_dir)
            
            cmd = [sys.executable, str(kdz_extract), '-f', kdz_path, '-x', '-o', './']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"KDZ extraction failed: {result.stderr}")
            
            # Extract DZ files if found
            dz_files = list(Path(output_dir).glob("*.dz"))
            for dz_file in dz_files:
                self._extract_dz(str(dz_file), output_dir)
            
            return output_dir
        
        finally:
            os.chdir(original_cwd)
    
    def _extract_dz(self, dz_path: str, output_dir: str) -> str:
        """Extract LG DZ files"""
        dz_extract = self.utils_dir / "kdztools" / "undz.py"
        
        if not dz_extract.exists():
            raise FileNotFoundError("undz.py not found")
        
        info("Extracting LG DZ file")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(output_dir)
            
            cmd = [sys.executable, str(dz_extract), '-f', dz_path, '-s', '-o', './']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"DZ extraction failed: {result.stderr}")
            
            return output_dir
        
        finally:
            os.chdir(original_cwd)
    
    def _extract_ozip(self, ozip_path: str, output_dir: str) -> str:
        """Extract Oppo/OnePlus OZIP files"""
        ozip_decrypt = self.utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py"
        
        if not ozip_decrypt.exists():
            raise FileNotFoundError("ozipdecrypt.py not found")
        
        info("Extracting OZIP file")
        
        cmd = [sys.executable, str(ozip_decrypt), '-f', ozip_path, '-o', output_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"OZIP extraction failed: {result.stderr}")
        
        return output_dir
    
    def _extract_ofp_ops(self, firmware_path: str, output_dir: str, extension: str) -> str:
        """Extract Oppo OFP/OPS files"""
        if extension == '.ofp':
            if self._is_qualcomm_firmware(firmware_path):
                script = self.utils_dir / "oppo_decrypt" / "ofp_qc_decrypt.py"
            else:
                script = self.utils_dir / "oppo_decrypt" / "ofp_mtk_decrypt.py"
        else:  # .ops
            script = self.utils_dir / "oppo_decrypt" / "opscrypto.py"
        
        if not script.exists():
            raise FileNotFoundError(f"{script.name} not found")
        
        info(f"Extracting {extension.upper()} file")
        
        cmd = [sys.executable, str(script), firmware_path, output_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"{extension.upper()} extraction failed: {result.stderr}")
        
        return output_dir
    
    def _extract_nb0(self, nb0_path: str, output_dir: str) -> str:
        """Extract Nokia NB0 files"""
        nb0_extract = self.utils_dir / "nb0-extract"
        
        if not nb0_extract.exists():
            raise FileNotFoundError("nb0-extract not found")
        
        info("Extracting NB0 file")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(output_dir)
            
            cmd = [str(nb0_extract), nb0_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"NB0 extraction failed: {result.stderr}")
            
            return output_dir
        
        finally:
            os.chdir(original_cwd)
    
    def _extract_pac(self, pac_path: str, output_dir: str) -> str:
        """Extract SpreadTrum PAC files"""
        pac_extractor = self.utils_dir / "pacextractor" / "python" / "pacExtractor.py"
        
        if not pac_extractor.exists():
            raise FileNotFoundError("pacExtractor.py not found")
        
        info("Extracting PAC file")
        
        cmd = [sys.executable, str(pac_extractor), pac_path, output_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"PAC extraction failed: {result.stderr}")
        
        return output_dir
    
    def _extract_ruu(self, ruu_path: str, output_dir: str) -> str:
        """Extract HTC RUU files"""
        ruu_decrypt = self.utils_dir / "RUU_Decrypt_Tool"
        
        if not ruu_decrypt.exists():
            raise FileNotFoundError("RUU_Decrypt_Tool not found")
        
        info("Extracting RUU file")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(output_dir)
            
            cmd = [str(ruu_decrypt), '-f', ruu_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"RUU extraction failed: {result.stderr}")
            
            return output_dir
        
        finally:
            os.chdir(original_cwd)
    
    def _extract_update_app(self, update_app_path: str, output_dir: str) -> str:
        """Extract Huawei UPDATE.APP files"""
        splituapp = self.utils_dir / "splituapp.py"
        
        if not splituapp.exists():
            raise FileNotFoundError("splituapp.py not found")
        
        info("Extracting UPDATE.APP file")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(output_dir)
            
            cmd = [sys.executable, str(splituapp), '-f', update_app_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"UPDATE.APP extraction failed: {result.stderr}")
            
            return output_dir
        
        finally:
            os.chdir(original_cwd)
    
    def _is_qualcomm_firmware(self, firmware_path: str) -> bool:
        """Detect if firmware is Qualcomm-based"""
        try:
            with open(firmware_path, 'rb') as f:
                header = f.read(1024)
                return b'QCOM' in header or b'qualcomm' in header.lower()
        except Exception:
            return True  # Default to Qualcomm