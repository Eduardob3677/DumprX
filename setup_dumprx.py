#!/usr/bin/env python3

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def print_banner():
    banner_text = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝

    DumprX Setup - Installing Dependencies and Tools
    """
    print(banner_text)


def run_command(cmd, check=True):
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def install_system_packages():
    system = platform.system().lower()
    
    if system == "linux":
        return install_linux_packages()
    elif system == "darwin":
        return install_macos_packages()
    else:
        print(f"Unsupported operating system: {system}")
        return False


def install_linux_packages():
    print("Detecting Linux distribution...")
    
    if shutil.which("apt"):
        print("Ubuntu/Debian Based Distro Detected")
        
        print(">> Updating apt repos...")
        success, _, stderr = run_command("sudo apt -y update")
        if not success:
            print(f"Failed to update apt repos: {stderr}")
            return False
        
        print(">> Installing Required Packages...")
        packages = [
            "unace", "unrar", "zip", "unzip", "p7zip-full", "p7zip-rar", 
            "sharutils", "rar", "uudeview", "mpack", "arj", "cabextract",
            "device-tree-compiler", "liblzma-dev", "python3-pip", "brotli",
            "liblz4-tool", "axel", "gawk", "aria2", "detox", "cpio", "rename",
            "liblz4-dev", "jq", "git-lfs", "python3-venv"
        ]
        
        cmd = f"sudo apt install -y {' '.join(packages)}"
        success, _, stderr = run_command(cmd)
        if not success:
            print(f"Failed to install packages: {stderr}")
            return False
            
    elif shutil.which("dnf"):
        print("Fedora Based Distro Detected")
        
        packages = [
            "unace", "unrar", "zip", "unzip", "sharutils", "uudeview", "arj",
            "cabextract", "file-roller", "dtc", "python3-pip", "brotli", "axel",
            "aria2", "detox", "cpio", "lz4", "python3-devel", "xz-devel",
            "p7zip", "p7zip-plugins", "git-lfs"
        ]
        
        cmd = f"sudo dnf install -y {' '.join(packages)}"
        success, _, stderr = run_command(cmd)
        if not success:
            print(f"Failed to install packages: {stderr}")
            return False
            
    elif shutil.which("pacman"):
        print("Arch or Arch Based Distro Detected")
        
        success, _, stderr = run_command("sudo pacman -Syyu --needed --noconfirm")
        if not success:
            print(f"Failed to update pacman: {stderr}")
            return False
        
        packages = [
            "unace", "unrar", "p7zip", "sharutils", "uudeview", "arj", 
            "cabextract", "file-roller", "dtc", "brotli", "axel", "gawk",
            "aria2", "detox", "cpio", "lz4", "jq", "git-lfs"
        ]
        
        cmd = f"sudo pacman -Sy --noconfirm {' '.join(packages)}"
        success, _, stderr = run_command(cmd)
        if not success:
            print(f"Failed to install packages: {stderr}")
            return False
    else:
        print("Unsupported Linux distribution")
        return False
    
    return True


def install_macos_packages():
    print("macOS Detected")
    
    if not shutil.which("brew"):
        print("Homebrew not found. Please install Homebrew first.")
        return False
    
    print(">> Installing Required Packages...")
    packages = [
        "protobuf", "xz", "brotli", "lz4", "aria2", "detox", "coreutils",
        "p7zip", "gawk", "git-lfs"
    ]
    
    cmd = f"brew install {' '.join(packages)}"
    success, _, stderr = run_command(cmd)
    if not success:
        print(f"Failed to install packages: {stderr}")
        return False
    
    return True


def install_uv():
    print(">> Installing uv for python packages...")
    
    cmd = 'bash -c "$(curl -sL https://astral.sh/uv/install.sh)"'
    success, _, stderr = run_command(cmd)
    if not success:
        print(f"Failed to install uv: {stderr}")
        return False
    
    # Add uv to PATH
    uv_path = Path.home() / ".local/bin"
    if str(uv_path) not in os.environ.get("PATH", ""):
        os.environ["PATH"] = f"{uv_path}:{os.environ.get('PATH', '')}"
    
    return True


def install_python_dependencies():
    print(">> Installing Python dependencies...")
    
    if shutil.which("uv"):
        cmd = "uv pip install -e ."
    else:
        cmd = "pip3 install -e ."
    
    success, _, stderr = run_command(cmd)
    if not success:
        print(f"Failed to install Python dependencies: {stderr}")
        return False
    
    return True


def main():
    print_banner()
    
    try:
        if not install_system_packages():
            print("System package installation failed!")
            sys.exit(1)
        
        if not install_uv():
            print("UV installation failed!")
            sys.exit(1)
        
        if not install_python_dependencies():
            print("Python dependency installation failed!")
            sys.exit(1)
        
        print("Setup Complete!")
        print("\nYou can now run: dumprx --help")
        
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()