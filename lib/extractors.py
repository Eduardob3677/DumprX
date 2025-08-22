import asyncio
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from abc import ABC, abstractmethod
from .ui import UI
from .config import config
from .boot_extractor import BootImageExtractor

class BaseExtractor(ABC):
    def __init__(self, utils_dir: Path):
        self.utils_dir = utils_dir
        self.partitions = config.get('partitions.supported', [])
        self.ext4_partitions = config.get('partitions.ext4_partitions', [])
    
    @abstractmethod
    async def can_extract(self, file_path: Path) -> bool:
        pass
    
    @abstractmethod
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        pass
    
    async def run_command(self, cmd: List[str], cwd: Optional[Path] = None) -> bool:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(cwd) if cwd else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception as e:
            UI.error(f"Command failed: {' '.join(cmd)}: {e}")
            return False

class ArchiveExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in ['.zip', '.rar', '.7z', '.tar', '.gz', '.tgz']
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing(f"Extracting archive: {file_path.name}")
        
        seven_zip = self.utils_dir / "bin" / "7zz"
        if not seven_zip.exists():
            seven_zip = "7zz"
        
        cmd = [str(seven_zip), "x", "-y", str(file_path), f"-o{output_dir}"]
        return await self.run_command(cmd)

class KDZExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        if file_path.suffix.lower() == '.kdz':
            return True
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                return b"LGE" in header or file_path.name.endswith('.kdz')
        except:
            return False
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("LG KDZ firmware detected")
        
        kdz_tool = self.utils_dir / "kdztools" / "unkdz.py"
        if not kdz_tool.exists():
            UI.error("KDZ extraction tool not found")
            return False
        
        cmd = ["python3", str(kdz_tool), "-f", str(file_path), "-x", "-o", str(output_dir)]
        success = await self.run_command(cmd, output_dir)
        
        if success:
            dz_files = list(output_dir.glob("*.dz"))
            if dz_files:
                UI.processing("Extracting DZ partitions")
                dz_tool = self.utils_dir / "kdztools" / "undz.py"
                for dz_file in dz_files:
                    cmd = ["python3", str(dz_tool), "-f", str(dz_file), "-s", "-o", str(output_dir)]
                    await self.run_command(cmd, output_dir)
        
        return success

class OZipExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        if file_path.suffix.lower() == '.ozip':
            return True
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12).replace(b'\0', b'')
                return header == b"OPPOENCRYPT!"
        except:
            return False
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Oppo/Realme OZIP firmware detected")
        
        ozip_tool = self.utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py"
        if not ozip_tool.exists():
            UI.error("OZIP decryption tool not found")
            return False
        
        requirements = self.utils_dir / "oppo_decrypt" / "requirements.txt"
        cmd = ["uv", "run", "--with-requirements", str(requirements), str(ozip_tool), str(file_path)]
        return await self.run_command(cmd, output_dir)

class OPSExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.ops'
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Oppo/OnePlus OPS firmware detected")
        
        ops_tool = self.utils_dir / "oppo_decrypt" / "opscrypto.py"
        if not ops_tool.exists():
            UI.error("OPS decryption tool not found")
            return False
        
        requirements = self.utils_dir / "oppo_decrypt" / "requirements.txt"
        cmd = ["uv", "run", "--with-requirements", str(requirements), str(ops_tool), "decrypt", str(file_path)]
        return await self.run_command(cmd, output_dir)

class PayloadExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return file_path.name == "payload.bin"
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Android OTA payload detected")
        
        payload_tool = self.utils_dir / "bin" / "payload-dumper-go"
        if not payload_tool.exists():
            UI.error("Payload dumper not found")
            return False
        
        cmd = [str(payload_tool), "-o", str(output_dir), str(file_path)]
        return await self.run_command(cmd)

class SuperImageExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return "super" in file_path.name.lower() and file_path.suffix == '.img'
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Super image detected")
        
        simg2img = self.utils_dir / "bin" / "simg2img"
        lpunpack = self.utils_dir / "lpunpack"
        
        if not lpunpack.exists():
            UI.error("lpunpack tool not found")
            return False
        
        super_raw = output_dir / "super.img.raw"
        
        if simg2img.exists():
            cmd = [str(simg2img), str(file_path), str(super_raw)]
            await self.run_command(cmd)
        else:
            super_raw = file_path
        
        for partition in self.partitions:
            for suffix in ["_a", ""]:
                part_name = f"{partition}{suffix}"
                cmd = [str(lpunpack), f"--partition={part_name}", str(super_raw)]
                await self.run_command(cmd, output_dir)
        
        return True

class HuaweiExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return file_path.name == "UPDATE.APP"
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Huawei UPDATE.APP detected")
        
        splituapp = self.utils_dir / "splituapp.py"
        if not splituapp.exists():
            UI.error("SplitUApp tool not found")
            return False
        
        cmd = ["python3", str(splituapp), str(file_path)]
        return await self.run_command(cmd, output_dir)

class SonyExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.sin'
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Sony SIN firmware detected")
        
        unsin = self.utils_dir / "unsin"
        if not unsin.exists():
            UI.error("unsin tool not found")
            return False
        
        cmd = [str(unsin), "-i", str(file_path), "-o", str(output_dir)]
        return await self.run_command(cmd)

class NB0Extractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.nb0'
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Nokia/Sharp/Essential NB0 firmware detected")
        
        nb0_extract = self.utils_dir / "nb0-extract"
        if not nb0_extract.exists():
            UI.error("nb0-extract tool not found")
            return False
        
        cmd = [str(nb0_extract), str(file_path)]
        return await self.run_command(cmd, output_dir)

class PACExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pac'
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Spreadtrum PAC firmware detected")
        
        pac_tool = self.utils_dir / "pacextractor" / "python" / "pacExtractor.py"
        if not pac_tool.exists():
            UI.error("PAC extractor not found")
            return False
        
        cmd = ["python3", str(pac_tool), str(file_path)]
        return await self.run_command(cmd, output_dir)

class BootExtractor(BaseExtractor):
    async def can_extract(self, file_path: Path) -> bool:
        return file_path.name in ['boot.img', 'recovery.img', 'vendor_boot.img'] or 'boot' in file_path.name.lower()
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.processing("Boot/Recovery image detected")
        
        boot_extractor = BootImageExtractor(self.utils_dir)
        return await boot_extractor.extract(file_path, output_dir)

class FirmwareExtractor:
    def __init__(self, utils_dir: Path):
        self.utils_dir = utils_dir
        self.extractors: List[BaseExtractor] = [
            KDZExtractor(utils_dir),
            OZipExtractor(utils_dir),
            OPSExtractor(utils_dir),
            PayloadExtractor(utils_dir),
            SuperImageExtractor(utils_dir),
            HuaweiExtractor(utils_dir),
            SonyExtractor(utils_dir),
            NB0Extractor(utils_dir),
            PACExtractor(utils_dir),
            BootExtractor(utils_dir),
            ArchiveExtractor(utils_dir)
        ]
    
    async def extract(self, file_path: Path, output_dir: Path) -> bool:
        UI.section(f"Extracting firmware: {file_path.name}")
        
        for extractor in self.extractors:
            if await extractor.can_extract(file_path):
                UI.info(f"Using {extractor.__class__.__name__}")
                return await extractor.extract(file_path, output_dir)
        
        UI.warning(f"No suitable extractor found for {file_path.name}")
        return False