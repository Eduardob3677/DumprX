#!/usr/bin/env python3

import os
from pathlib import Path
from typing import List, Dict

from rich.console import Console

from .utils import run_command, console, ProgressManager

class ExternalToolManager:
    def __init__(self, utils_dir: Path):
        self.utils_dir = Path(utils_dir)
        self.console = Console()
        
        self.external_tools = [
            "bkerler/oppo_ozip_decrypt",
            "bkerler/oppo_decrypt", 
            "marin-m/vmlinux-to-elf",
            "ShivamKumarJha/android_tools",
            "HemanthJabalpuri/pacextractor"
        ]
        
        self.tool_paths = self._setup_tool_paths()
    
    def _setup_tool_paths(self) -> Dict[str, Path]:
        tools = {}
        
        # Binary tools
        bin_dir = self.utils_dir / "bin"
        tools.update({
            "7zz": self._find_binary("7zz", bin_dir / "7zz"),
            "simg2img": bin_dir / "simg2img",
            "packsparseimg": bin_dir / "packsparseimg", 
            "payload_extractor": bin_dir / "payload-dumper-go",
            "afptool": bin_dir / "afptool",
            "rk_extract": bin_dir / "rkImageMaker",
            "transfer": bin_dir / "transfer",
            "fsck_erofs": bin_dir / "fsck.erofs"
        })
        
        # Python tools
        tools.update({
            "sdat2img": self.utils_dir / "sdat2img.py",
            "splituapp": self.utils_dir / "splituapp.py",
            "ozipdecrypt": self.utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py",
            "ofp_qc_decrypt": self.utils_dir / "oppo_decrypt" / "ofp_qc_decrypt.py",
            "ofp_mtk_decrypt": self.utils_dir / "oppo_decrypt" / "ofp_mtk_decrypt.py",
            "opsdecrypt": self.utils_dir / "oppo_decrypt" / "opscrypto.py",
            "kdz_extract": self.utils_dir / "kdztools" / "unkdz.py",
            "dz_extract": self.utils_dir / "kdztools" / "undz.py",
            "pacextractor": self.utils_dir / "pacextractor" / "python" / "pacExtractor.py"
        })
        
        # Other tools
        tools.update({
            "lpunpack": self.utils_dir / "lpunpack",
            "unsin": self.utils_dir / "unsin", 
            "dtc": self.utils_dir / "dtc",
            "vmlinux2elf": self.utils_dir / "vmlinux-to-elf" / "vmlinux-to-elf",
            "kallsyms_finder": self.utils_dir / "vmlinux-to-elf" / "kallsyms-finder",
            "nb0_extract": self.utils_dir / "nb0-extract",
            "ruu_decrypt": self.utils_dir / "RUU_Decrypt_Tool",
            "extract_ikconfig": self.utils_dir / "extract-ikconfig",
            "aml_extract": self.utils_dir / "aml-upgrade-package-extract"
        })
        
        return tools
    
    def _find_binary(self, cmd_name: str, fallback_path: Path) -> Path:
        import shutil
        system_path = shutil.which(cmd_name)
        return Path(system_path) if system_path else fallback_path
    
    def setup_external_tools(self):
        with ProgressManager() as progress:
            task = progress.add_task("Setting up external tools...", total=len(self.external_tools))
            
            for tool_slug in self.external_tools:
                tool_name = tool_slug.split("/")[1]
                tool_dir = self.utils_dir / tool_name
                
                if not tool_dir.exists():
                    self.console.print(f"[blue]Cloning {tool_slug}...[/blue]")
                    run_command([
                        "git", "clone", "-q", 
                        f"https://github.com/{tool_slug}.git",
                        str(tool_dir)
                    ])
                else:
                    self.console.print(f"[blue]Updating {tool_name}...[/blue]")
                    run_command(["git", "pull"], cwd=tool_dir)
                
                progress.advance(task)
    
    def get_tool_path(self, tool_name: str) -> Path:
        if tool_name not in self.tool_paths:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self.tool_paths[tool_name]
    
    def ensure_uv_available(self):
        uv_path = Path.home() / ".local" / "bin"
        if uv_path.exists():
            os.environ["PATH"] = f"{uv_path}:{os.environ.get('PATH', '')}"