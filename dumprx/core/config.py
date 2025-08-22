import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class Config:
    def __init__(self, project_dir: Optional[str] = None):
        if project_dir:
            self.project_dir = Path(project_dir).resolve()
        else:
            self.project_dir = Path(__file__).parent.parent.parent.resolve()
        
        self.input_dir = self.project_dir / "input"
        self.utils_dir = self.project_dir / "utils"
        self.out_dir = self.project_dir / "out"
        self.tmp_dir = self.out_dir / "tmp"
        
        self.external_tools = [
            "bkerler/oppo_ozip_decrypt",
            "bkerler/oppo_decrypt", 
            "marin-m/vmlinux-to-elf",
            "ShivamKumarJha/android_tools",
            "HemanthJabalpuri/pacextractor"
        ]
        
        self.partitions = [
            "system", "system_ext", "system_other", "systemex", "vendor", "cust", 
            "odm", "oem", "factory", "product", "xrom", "modem", "dtbo", "dtb", 
            "boot", "vendor_boot", "recovery", "tz", "oppo_product", "preload_common",
            "opproduct", "reserve", "india", "my_preload", "my_odm", "my_stock",
            "my_operator", "my_country", "my_product", "my_company", "my_engineering",
            "my_heytap", "my_custom", "my_manifest", "my_carrier", "my_region", 
            "my_bigball", "my_version", "special_preload", "system_dlkm", 
            "vendor_dlkm", "odm_dlkm", "init_boot", "vendor_kernel_boot", "odmko",
            "socko", "nt_log", "mi_ext", "hw_product", "product_h", "preas", "preavs"
        ]
        
        self.ext4_partitions = [
            "system", "vendor", "cust", "odm", "oem", "factory", "product", "xrom",
            "systemex", "oppo_product", "preload_common", "hw_product", "product_h",
            "preas", "preavs"
        ]
        
        self.other_partitions = {
            "tz.mbn": "tz",
            "tz.img": "tz", 
            "modem.img": "modem",
            "NON-HLOS": "modem",
            "boot-verified.img": "boot",
            "recovery-verified.img": "recovery", 
            "dtbo-verified.img": "dtbo"
        }
        
        self._setup_directories()
        
    def _setup_directories(self):
        self.out_dir.mkdir(exist_ok=True)
        self.input_dir.mkdir(exist_ok=True)
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
    
    def get_tool_paths(self) -> Dict[str, Path]:
        return {
            "sdat2img": self.utils_dir / "sdat2img.py",
            "simg2img": self.utils_dir / "bin/simg2img", 
            "packsparseimg": self.utils_dir / "bin/packsparseimg",
            "unsin": self.utils_dir / "unsin",
            "payload_extractor": self.utils_dir / "bin/payload-dumper-go",
            "dtc": self.utils_dir / "dtc",
            "vmlinux2elf": self.utils_dir / "vmlinux-to-elf/vmlinux-to-elf",
            "kallsyms_finder": self.utils_dir / "vmlinux-to-elf/kallsyms-finder",
            "ozipdecrypt": self.utils_dir / "oppo_ozip_decrypt/ozipdecrypt.py",
            "ofp_qc_decrypt": self.utils_dir / "oppo_decrypt/ofp_qc_decrypt.py",
            "ofp_mtk_decrypt": self.utils_dir / "oppo_decrypt/ofp_mtk_decrypt.py",
            "opsdecrypt": self.utils_dir / "oppo_decrypt/opscrypto.py",
            "lpunpack": self.utils_dir / "lpunpack",
            "splituapp": self.utils_dir / "splituapp.py",
            "pacextractor": self.utils_dir / "pacextractor/python/pacExtractor.py",
            "nb0_extract": self.utils_dir / "nb0-extract",
            "kdz_extract": self.utils_dir / "kdztools/unkdz.py",
            "dz_extract": self.utils_dir / "kdztools/undz.py",
            "ruudecrypt": self.utils_dir / "RUU_Decrypt_Tool",
            "extract_ikconfig": self.utils_dir / "extract-ikconfig",
            "unpackboot": self.utils_dir / "unpackboot.sh",
            "aml_extract": self.utils_dir / "aml-upgrade-package-extract",
            "afptool_extract": self.utils_dir / "bin/afptool",
            "rk_extract": self.utils_dir / "bin/rkImageMaker",
            "transfer": self.utils_dir / "bin/transfer",
            "fsck_erofs": self.utils_dir / "bin/fsck.erofs",
            "7zz": self._get_7zz_path(),
            "megamediadrive_dl": self.utils_dir / "downloaders/mega-media-drive_dl.sh",
            "afh_dl": self.utils_dir / "downloaders/afh_dl.py"
        }
    
    def _get_7zz_path(self) -> Path:
        if shutil.which("7zz"):
            return Path("7zz")
        return self.utils_dir / "bin/7zz"