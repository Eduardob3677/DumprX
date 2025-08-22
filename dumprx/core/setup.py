"""
Setup manager for DumprX dependencies and external tools.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from dumprxconfig import Config
from dumprxutils.console import print_info, print_error, print_success, print_step, print_substep, print_warning


@dataclass
class SetupResult:
    """Result of setup operation."""
    success: bool
    message: str = ""
    error: Optional[str] = None


class SetupManager:
    """Manages setup of dependencies and external tools."""
    
    # External tools that need to be cloned from GitHub
    EXTERNAL_TOOLS = [
        "bkerler/oppo_ozip_decrypt",
        "bkerler/oppo_decrypt", 
        "marin-m/vmlinux-to-elf",
        "ShivamKumarJha/android_tools",
        "HemanthJabalpuri/pacextractor",
    ]
    
    # System packages required for different platforms
    SYSTEM_PACKAGES = {
        'ubuntu': [
            'unace', 'unrar', 'zip', 'unzip', 'p7zip-full', 'p7zip-rar',
            'sharutils', 'rar', 'uudeview', 'mpack', 'arj', 'cabextract',
            'device-tree-compiler', 'liblzma-dev', 'python3-pip', 'brotli',
            'liblz4-tool', 'axel', 'gawk', 'aria2', 'detox', 'cpio', 'rename',
            'liblz4-dev', 'jq', 'git-lfs'
        ],
        'fedora': [
            'unace', 'unrar', 'zip', 'unzip', 'sharutils', 'uudeview', 'arj',
            'cabextract', 'file-roller', 'dtc', 'python3-pip', 'brotli', 'axel',
            'aria2', 'detox', 'cpio', 'lz4', 'python3-devel', 'xz-devel',
            'p7zip', 'p7zip-plugins', 'git-lfs'
        ],
        'arch': [
            'unace', 'unrar', 'p7zip', 'sharutils', 'uudeview', 'arj',
            'cabextract', 'file-roller', 'dtc', 'brotli', 'axel', 'gawk',
            'aria2', 'detox', 'cpio', 'lz4', 'jq', 'git-lfs'
        ],
        'macos': [
            'protobuf', 'xz', 'brotli', 'lz4', 'aria2', 'detox',
            'coreutils', 'p7zip', 'gawk', 'git-lfs'
        ]
    }
    
    def __init__(self, config: Config):
        self.config = config
    
    def setup_all(self, force: bool = False) -> SetupResult:
        """
        Setup all dependencies and tools.
        
        Args:
            force: Force reinstall even if already present
            
        Returns:
            SetupResult with operation status
        """
        print_step("Setting up DumprX Dependencies")
        
        try:
            # Setup Python dependencies
            python_result = self._setup_python_dependencies(force)
            if not python_result.success:
                return python_result
            
            # Setup system packages
            system_result = self._setup_system_packages()
            if not system_result.success:
                print_warning(f"System packages setup failed: {system_result.error}")
            
            # Setup external tools
            tools_result = self._setup_external_tools(force)
            if not tools_result.success:
                print_warning(f"External tools setup failed: {tools_result.error}")
            
            # Setup binaries directory
            self._setup_binaries_directory()
            
            print_success("DumprX setup completed successfully!")
            return SetupResult(success=True, message="Setup completed")
            
        except Exception as e:
            error_msg = f"Setup failed: {e}"
            print_error(error_msg)
            return SetupResult(success=False, error=error_msg)
    
    def _setup_python_dependencies(self, force: bool = False) -> SetupResult:
        """Setup Python dependencies."""
        print_substep("Installing Python dependencies")
        
        try:
            # Try to use uv if available, otherwise pip
            uv_path = shutil.which('uv')
            if uv_path:
                print_info("Using uv for Python package installation")
                cmd = ['uv', 'pip', 'install', '-r', 'requirements.txt']
                if force:
                    cmd.append('--force-reinstall')
            else:
                print_info("Using pip for Python package installation")
                cmd = ['pip', 'install', '-r', 'requirements.txt']
                if force:
                    cmd.append('--force-reinstall')
            
            # Run from the project directory where requirements.txt is located
            result = subprocess.run(
                cmd,
                cwd=self.config.project_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                print_success("Python dependencies installed")
                return SetupResult(success=True, message="Python dependencies installed")
            else:
                error_msg = f"Failed to install Python dependencies: {result.stderr}"
                print_error(error_msg)
                return SetupResult(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"Python dependencies setup failed: {e}"
            return SetupResult(success=False, error=error_msg)
    
    def _setup_system_packages(self) -> SetupResult:
        """Setup system packages based on detected platform."""
        print_substep("Installing system packages")
        
        try:
            platform = self._detect_platform()
            if not platform:
                return SetupResult(success=False, error="Unsupported platform")
            
            print_info(f"Detected platform: {platform}")
            
            packages = self.SYSTEM_PACKAGES.get(platform, [])
            if not packages:
                return SetupResult(success=False, error=f"No package list for platform: {platform}")
            
            install_cmd = self._get_install_command(platform, packages)
            if not install_cmd:
                return SetupResult(success=False, error=f"No install command for platform: {platform}")
            
            print_info(f"Installing packages: {' '.join(packages)}")
            
            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                print_success("System packages installed")
                return SetupResult(success=True, message="System packages installed")
            else:
                error_msg = f"Failed to install system packages: {result.stderr}"
                print_warning(error_msg)
                return SetupResult(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"System packages setup failed: {e}"
            return SetupResult(success=False, error=error_msg)
    
    def _setup_external_tools(self, force: bool = False) -> SetupResult:
        """Setup external tools by cloning from GitHub."""
        print_substep("Setting up external tools")
        
        try:
            utils_dir = self.config.utils_dir
            
            for tool_slug in self.EXTERNAL_TOOLS:
                tool_name = tool_slug.split('/')[-1]
                tool_dir = utils_dir / tool_name
                
                if tool_dir.exists() and not force:
                    print_info(f"Updating {tool_name}...")
                    # Update existing repository
                    result = subprocess.run([
                        'git', '-C', str(tool_dir), 'pull'
                    ], capture_output=True, text=True, timeout=120)
                    
                    if result.returncode != 0:
                        print_warning(f"Failed to update {tool_name}: {result.stderr}")
                else:
                    print_info(f"Cloning {tool_name}...")
                    # Clone new repository
                    if tool_dir.exists():
                        shutil.rmtree(tool_dir)
                    
                    result = subprocess.run([
                        'git', 'clone', '-q', f'https://github.com/{tool_slug}.git', str(tool_dir)
                    ], capture_output=True, text=True, timeout=300)
                    
                    if result.returncode != 0:
                        print_warning(f"Failed to clone {tool_name}: {result.stderr}")
            
            print_success("External tools setup completed")
            return SetupResult(success=True, message="External tools setup completed")
            
        except Exception as e:
            error_msg = f"External tools setup failed: {e}"
            return SetupResult(success=False, error=error_msg)
    
    def _setup_binaries_directory(self):
        """Setup binaries directory structure."""
        print_substep("Setting up binaries directory")
        
        bin_dir = self.config.bin_dir
        bin_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of binaries
        subdirs = ['extractors', 'converters', 'tools']
        for subdir in subdirs:
            (bin_dir / subdir).mkdir(exist_ok=True)
        
        print_success("Binaries directory setup completed")
    
    def _detect_platform(self) -> Optional[str]:
        """Detect current platform."""
        import platform
        
        system = platform.system().lower()
        
        if system == 'linux':
            # Detect Linux distribution
            try:
                with open('/etc/os-release', 'r') as f:
                    os_release = f.read()
                
                if 'ubuntu' in os_release.lower() or 'debian' in os_release.lower():
                    return 'ubuntu'
                elif 'fedora' in os_release.lower() or 'rhel' in os_release.lower() or 'centos' in os_release.lower():
                    return 'fedora'
                elif 'arch' in os_release.lower() or 'manjaro' in os_release.lower():
                    return 'arch'
            except:
                pass
            
            # Fallback detection
            if shutil.which('apt'):
                return 'ubuntu'
            elif shutil.which('dnf') or shutil.which('yum'):
                return 'fedora'
            elif shutil.which('pacman'):
                return 'arch'
                
        elif system == 'darwin':
            return 'macos'
        
        return None
    
    def _get_install_command(self, platform: str, packages: List[str]) -> Optional[List[str]]:
        """Get package install command for platform."""
        if platform == 'ubuntu':
            return ['sudo', 'apt', 'install', '-y'] + packages
        elif platform == 'fedora':
            return ['sudo', 'dnf', 'install', '-y'] + packages
        elif platform == 'arch':
            return ['sudo', 'pacman', '-Sy', '--noconfirm'] + packages
        elif platform == 'macos':
            return ['brew', 'install'] + packages
        
        return None