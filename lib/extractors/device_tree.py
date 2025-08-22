import asyncio
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from lib.core.logger import logger
from lib.utils.command import run_command
from lib.utils.filesystem import ensure_dir

class DeviceTreeGenerator:
    def __init__(self, output_dir: Path, utils_dir: Path):
        self.output_dir = output_dir
        self.utils_dir = utils_dir
        self.device_info = {}
    
    async def generate_device_trees(self) -> Dict[str, Any]:
        logger.processing("Generating device trees and extracting device information")
        
        await self._extract_device_info()
        await self._generate_twrp_device_tree()
        
        if self.device_info.get('treble_support'):
            await self._generate_lineage_device_tree()
        
        await self._generate_proprietary_files()
        
        return self.device_info
    
    async def _extract_device_info(self) -> None:
        prop_files = list(self.output_dir.glob('**/build.prop'))
        prop_files.extend(list(self.output_dir.glob('**/system.prop')))
        prop_files.extend(list(self.output_dir.glob('**/prop.default')))
        
        for prop_file in prop_files:
            await self._parse_prop_file(prop_file)
        
        await self._extract_kernel_info()
        await self._check_treble_support()
        
        logger.info(f"Device: {self.device_info.get('model', 'Unknown')}")
        logger.info(f"Codename: {self.device_info.get('codename', 'Unknown')}")
        logger.info(f"Brand: {self.device_info.get('brand', 'Unknown')}")
        logger.info(f"Android Version: {self.device_info.get('android_version', 'Unknown')}")
    
    async def _parse_prop_file(self, prop_file: Path) -> None:
        try:
            with open(prop_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            properties = {
                'model': r'ro\.product\.model=(.+)',
                'brand': r'ro\.product\.brand=(.+)',
                'manufacturer': r'ro\.product\.manufacturer=(.+)',
                'codename': r'ro\.product\.device=(.+)',
                'android_version': r'ro\.build\.version\.release=(.+)',
                'sdk_version': r'ro\.build\.version\.sdk=(.+)',
                'build_type': r'ro\.build\.type=(.+)',
                'build_tags': r'ro\.build\.tags=(.+)',
                'security_patch': r'ro\.build\.version\.security_patch=(.+)',
                'fingerprint': r'ro\.build\.fingerprint=(.+)',
                'board': r'ro\.product\.board=(.+)',
                'platform': r'ro\.board\.platform=(.+)',
                'cpu_abi': r'ro\.product\.cpu\.abi=(.+)',
                'cpu_abi2': r'ro\.product\.cpu\.abi2=(.+)',
                'bootloader': r'ro\.bootloader=(.+)',
                'radio': r'ro\.baseband=(.+)'
            }
            
            for key, pattern in properties.items():
                match = re.search(pattern, content, re.MULTILINE)
                if match and not self.device_info.get(key):
                    self.device_info[key] = match.group(1).strip()
        
        except Exception as e:
            logger.warning(f"Failed to parse {prop_file}: {e}")
    
    async def _extract_kernel_info(self) -> None:
        kernel_files = list(self.output_dir.glob('**/kernel'))
        kernel_files.extend(list(self.output_dir.glob('**/zImage*')))
        kernel_files.extend(list(self.output_dir.glob('**/Image*')))
        
        for kernel_file in kernel_files:
            if kernel_file.is_file():
                try:
                    result = await run_command(['file', str(kernel_file)])
                    if 'Linux kernel' in result.stdout:
                        self.device_info['kernel_file'] = str(kernel_file)
                        
                        ikconfig_file = self.output_dir / 'bootRE' / 'ikconfig'
                        if ikconfig_file.exists():
                            with open(ikconfig_file) as f:
                                for line in f:
                                    if 'Kernel Configuration' in line:
                                        version = line.split()[2] if len(line.split()) > 2 else None
                                        if version:
                                            self.device_info['kernel_version'] = version
                        break
                except Exception as e:
                    logger.warning(f"Failed to analyze kernel file {kernel_file}: {e}")
    
    async def _check_treble_support(self) -> None:
        vndk_files = list(self.output_dir.glob('**/vndk*'))
        vintf_files = list(self.output_dir.glob('**/vintf*'))
        
        self.device_info['treble_support'] = bool(vndk_files or vintf_files)
        
        if self.device_info['treble_support']:
            logger.success("Project Treble support detected")
    
    async def _generate_twrp_device_tree(self) -> None:
        logger.processing("Generating TWRP device tree")
        
        twrp_output = self.output_dir / "twrp-device-tree"
        ensure_dir(twrp_output)
        
        boot_img = self._find_boot_image()
        if not boot_img:
            logger.warning("No boot image found for TWRP device tree generation")
            return
        
        try:
            cmd = [
                'uvx', '-p', '3.9',
                '--from', 'git+https://github.com/twrpdtgen/twrpdtgen@master',
                'twrpdtgen', str(boot_img), '-o', str(twrp_output)
            ]
            
            result = await run_command(cmd)
            if result.returncode == 0:
                logger.success("TWRP device tree generated successfully")
                
                readme_url = "https://raw.githubusercontent.com/wiki/SebaUbuntu/TWRP-device-tree-generator/4.-Build-TWRP-from-source.md"
                readme_file = twrp_output / "README.md"
                
                if not readme_file.exists():
                    readme_result = await run_command(['curl', '-o', str(readme_file), readme_url])
                    if readme_result.returncode == 0:
                        logger.info("Added TWRP build instructions")
                
                self._cleanup_git_dirs(twrp_output)
            else:
                logger.warning("TWRP device tree generation failed")
        
        except Exception as e:
            logger.warning(f"Failed to generate TWRP device tree: {e}")
    
    def _find_boot_image(self) -> Optional[Path]:
        boot_candidates = [
            'boot.img', 'recovery.img', 'vendor_boot.img'
        ]
        
        for candidate in boot_candidates:
            boot_path = self.output_dir / candidate
            if boot_path.exists():
                return boot_path
        
        boot_files = list(self.output_dir.glob('**/boot*.img'))
        boot_files.extend(list(self.output_dir.glob('**/recovery*.img')))
        
        if boot_files:
            return boot_files[0]
        
        return None
    
    async def _generate_lineage_device_tree(self) -> None:
        logger.processing("Generating LineageOS device tree")
        
        lineage_output = self.output_dir / "aosp-device-tree"
        ensure_dir(lineage_output)
        
        try:
            cmd = ['uvx', '-p', '3.9', 'aospdtgen', str(self.output_dir), '-o', str(lineage_output)]
            result = await run_command(cmd)
            
            if result.returncode == 0:
                logger.success("LineageOS device tree generated successfully")
                self._cleanup_git_dirs(lineage_output)
            else:
                logger.warning("LineageOS device tree generation failed")
        
        except Exception as e:
            logger.warning(f"Failed to generate LineageOS device tree: {e}")
    
    def _cleanup_git_dirs(self, directory: Path) -> None:
        git_dirs = list(directory.glob('**/.git'))
        for git_dir in git_dirs:
            if git_dir.is_dir():
                import shutil
                shutil.rmtree(git_dir)
    
    async def _generate_proprietary_files(self) -> None:
        logger.processing("Generating proprietary files list")
        
        all_files_list = self.output_dir / "all_files.txt"
        
        self._generate_file_list(all_files_list)
        
        android_tools = self.utils_dir / "android_tools"
        if android_tools.exists():
            try:
                prop_script = android_tools / "tools" / "proprietary-files.sh"
                if prop_script.exists():
                    await run_command(['bash', str(prop_script), str(all_files_list)])
                    
                    working_dir = android_tools / "working"
                    if working_dir.exists():
                        await self._copy_proprietary_files(working_dir)
                
            except Exception as e:
                logger.warning(f"Failed to generate proprietary files: {e}")
    
    def _generate_file_list(self, output_file: Path) -> None:
        try:
            with open(output_file, 'w') as f:
                for file_path in self.output_dir.rglob('*'):
                    if file_path.is_file() and '.git/' not in str(file_path):
                        relative_path = file_path.relative_to(self.output_dir)
                        f.write(f"{relative_path}\n")
            
            logger.success(f"Generated file list: {output_file}")
        
        except Exception as e:
            logger.error(f"Failed to generate file list: {e}")
    
    async def _copy_proprietary_files(self, working_dir: Path) -> None:
        prop_files = working_dir / "proprietary-files.txt"
        prop_sha1 = working_dir / "proprietary-files.sha1"
        
        if prop_files.exists():
            dest_files = self.output_dir / "proprietary-files.txt"
            dest_sha1 = self.output_dir / "proprietary-files.sha1"
            
            with open(dest_files, 'w') as f:
                f.write(f"# All blobs from {self.device_info.get('fingerprint', 'unknown')}, unless pinned\n")
                with open(prop_files) as source:
                    f.write(source.read())
            
            if prop_sha1.exists():
                with open(dest_sha1, 'w') as f:
                    f.write(f"# All blobs are from \"{self.device_info.get('fingerprint', 'unknown')}\" and are pinned with sha1sum values\n")
                    with open(prop_sha1) as source:
                        f.write(source.read())
            
            logger.success("Copied proprietary files lists")