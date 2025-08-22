import asyncio
from pathlib import Path
from typing import List, Dict, Any
from lib.extractors.extractors import BaseExtractor
from lib.core.logger import logger
from lib.core.exceptions import ExtractionError
from lib.utils.command import run_command
from lib.utils.filesystem import ensure_dir

class OFPExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        ofp_qc_decrypt = self.utils_dir / "oppo_decrypt" / "ofp_qc_decrypt.py"
        ofp_mtk_decrypt = self.utils_dir / "oppo_decrypt" / "ofp_mtk_decrypt.py"
        
        qc_result = await run_command(["python3", str(ofp_qc_decrypt), str(input_path)], cwd=output_path)
        
        if qc_result.returncode != 0:
            logger.processing("Trying MTK decryption")
            mtk_result = await run_command(["python3", str(ofp_mtk_decrypt), str(input_path)], cwd=output_path)
            if mtk_result.returncode != 0:
                raise ExtractionError("Both QC and MTK OFP decryption failed")
        
        logger.success(f"Extracted OFP file to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".ofp"

class OPSExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        ops_decrypt = self.utils_dir / "oppo_decrypt" / "opscrypto.py"
        cmd = ["python3", str(ops_decrypt), str(input_path)]
        
        result = await run_command(cmd, cwd=output_path)
        if result.returncode != 0:
            raise ExtractionError(f"OPS extraction failed: {result.stderr}")
        
        logger.success(f"Extracted OPS file to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".ops"

class PACExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        pac_extractor = self.utils_dir / "pacextractor" / "python" / "pacExtractor.py"
        cmd = ["python3", str(pac_extractor), str(input_path), str(output_path)]
        
        result = await run_command(cmd)
        if result.returncode != 0:
            raise ExtractionError(f"PAC extraction failed: {result.stderr}")
        
        logger.success(f"Extracted PAC file to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pac"

class NB0Extractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        nb0_extract = self.utils_dir / "nb0-extract"
        cmd = [str(nb0_extract), str(input_path)]
        
        result = await run_command(cmd, cwd=output_path)
        if result.returncode != 0:
            raise ExtractionError(f"NB0 extraction failed: {result.stderr}")
        
        logger.success(f"Extracted NB0 file to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".nb0"

class SINExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        unsin = self.utils_dir / "unsin"
        cmd = [str(unsin), "-d", str(output_path), str(input_path)]
        
        result = await run_command(cmd)
        if result.returncode != 0:
            raise ExtractionError(f"SIN extraction failed: {result.stderr}")
        
        logger.success(f"Extracted SIN file to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".sin" or "system" in file_path.name.lower()

class RUUExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        ruu_decrypt = self.utils_dir / "RUU_Decrypt_Tool"
        cmd = [str(ruu_decrypt), str(input_path)]
        
        result = await run_command(cmd, cwd=output_path)
        if result.returncode != 0:
            raise ExtractionError(f"RUU extraction failed: {result.stderr}")
        
        logger.success(f"Extracted RUU file to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return "ruu_" in file_path.name.lower() and file_path.suffix.lower() == ".exe"

class ChunkExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        chunk_files = list(input_path.parent.glob("*chunk*"))
        if not chunk_files:
            raise ExtractionError("No chunk files found")
        
        bin_7zz = self.utils_dir / "bin" / "7zz"
        if not bin_7zz.exists():
            bin_7zz = "7zz"
        
        for chunk_file in chunk_files:
            logger.processing(f"Extracting chunk: {chunk_file.name}")
            cmd = [str(bin_7zz), "e", "-y", str(chunk_file), f"-o{output_path}"]
            await run_command(cmd)
        
        logger.success(f"Extracted chunk files to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return "chunk" in file_path.name.lower()

class RockchipExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        rk_extract = self.utils_dir / "bin" / "rkImageMaker"
        cmd = [str(rk_extract), str(input_path), str(output_path)]
        
        result = await run_command(cmd)
        if result.returncode != 0:
            raise ExtractionError(f"Rockchip extraction failed: {result.stderr}")
        
        logger.success(f"Extracted Rockchip image to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".img" and "rockchip" in str(file_path).lower()

class AMLExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        aml_extract = self.utils_dir / "aml-upgrade-package-extract"
        cmd = [str(aml_extract), str(input_path)]
        
        result = await run_command(cmd, cwd=output_path)
        if result.returncode != 0:
            raise ExtractionError(f"AML extraction failed: {result.stderr}")
        
        logger.success(f"Extracted AML package to {output_path}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".img" and "amlogic" in str(file_path).lower()

class SparseImageExtractor(BaseExtractor):
    async def extract(self, input_path: Path, output_path: Path) -> bool:
        ensure_dir(output_path)
        
        simg2img = self.utils_dir / "bin" / "simg2img"
        output_file = output_path / f"{input_path.stem}_raw.img"
        
        cmd = [str(simg2img), str(input_path), str(output_file)]
        result = await run_command(cmd)
        
        if result.returncode != 0:
            raise ExtractionError(f"Sparse image conversion failed: {result.stderr}")
        
        logger.success(f"Converted sparse image to {output_file}")
        return True
    
    def can_handle(self, file_path: Path) -> bool:
        if file_path.suffix.lower() != ".img":
            return False
        
        try:
            with open(file_path, 'rb') as f:
                magic = f.read(4)
                return magic == b'\x3a\xff\x26\xed'
        except:
            return False