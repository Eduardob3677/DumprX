import os
import subprocess
import platform
from pathlib import Path
from dumprx.utils.console import console, info, success, error, warning

def setup_dependencies():
    """Setup system dependencies"""
    system = platform.system().lower()
    
    info(f"Setting up dependencies for {system}")
    
    if system == "linux":
        _setup_linux_dependencies()
    elif system == "darwin":
        _setup_macos_dependencies()
    else:
        error(f"Unsupported system: {system}")
        return
    
    _setup_python_dependencies()
    _setup_external_tools()
    
    success("Dependencies setup completed!")

def _setup_linux_dependencies():
    """Setup Linux dependencies"""
    
    # Detect package manager
    if _command_exists("apt"):
        info("Ubuntu/Debian detected - installing packages with apt")
        packages = [
            "unace", "unrar", "zip", "unzip", "p7zip-full", "p7zip-rar",
            "sharutils", "rar", "uudeview", "mpack", "arj", "cabextract",
            "device-tree-compiler", "liblzma-dev", "python3-pip", "brotli",
            "liblz4-tool", "axel", "gawk", "aria2", "detox", "cpio", "rename",
            "liblz4-dev", "jq", "git-lfs"
        ]
        _run_command(["sudo", "apt", "-y", "update"])
        _run_command(["sudo", "apt", "install", "-y"] + packages)
        
    elif _command_exists("dnf"):
        info("Fedora detected - installing packages with dnf")
        packages = [
            "unace", "unrar", "zip", "unzip", "sharutils", "uudeview", "arj",
            "cabextract", "file-roller", "dtc", "python3-pip", "brotli", "axel",
            "aria2", "detox", "cpio", "lz4", "python3-devel", "xz-devel",
            "p7zip", "p7zip-plugins", "git-lfs"
        ]
        _run_command(["sudo", "dnf", "install", "-y"] + packages)
        
    elif _command_exists("pacman"):
        info("Arch Linux detected - installing packages with pacman")
        packages = [
            "unace", "unrar", "p7zip", "sharutils", "uudeview", "arj",
            "cabextract", "file-roller", "dtc", "brotli", "axel", "gawk",
            "aria2", "detox", "cpio", "lz4", "jq", "git-lfs"
        ]
        _run_command(["sudo", "pacman", "-Syyu", "--needed", "--noconfirm"])
        _run_command(["sudo", "pacman", "-Sy", "--noconfirm"] + packages)

def _setup_macos_dependencies():
    """Setup macOS dependencies"""
    info("macOS detected - installing packages with brew")
    
    if not _command_exists("brew"):
        error("Homebrew not found. Please install Homebrew first.")
        return
    
    packages = [
        "protobuf", "xz", "brotli", "lz4", "aria2", "detox",
        "coreutils", "p7zip", "gawk", "git-lfs"
    ]
    
    _run_command(["brew", "install"] + packages)

def _setup_python_dependencies():
    """Setup Python dependencies using uv"""
    info("Installing Python dependencies with uv")
    
    if not _command_exists("uv"):
        info("Installing uv...")
        _run_command(["bash", "-c", "curl -sL https://astral.sh/uv/install.sh | bash"])
        
        # Add uv to PATH
        uv_path = os.path.expanduser("~/.local/bin")
        current_path = os.environ.get("PATH", "")
        if uv_path not in current_path:
            os.environ["PATH"] = f"{uv_path}:{current_path}"
    
    # Install Python packages
    packages = [
        "click", "rich", "pyyaml", "requests", "gitpython",
        "humanize", "clint"
    ]
    
    for package in packages:
        _run_command(["uv", "tool", "install", package])

def setup_external_tools():
    """Setup external tools from GitHub"""
    project_dir = Path(__file__).parent.parent.parent
    utils_dir = project_dir / "utils"
    
    external_tools = [
        "bkerler/oppo_ozip_decrypt",
        "bkerler/oppo_decrypt", 
        "marin-m/vmlinux-to-elf",
        "ShivamKumarJha/android_tools",
        "HemanthJabalpuri/pacextractor"
    ]
    
    for tool_slug in external_tools:
        tool_name = tool_slug.split("/")[1]
        tool_dir = utils_dir / tool_name
        
        if tool_dir.exists():
            info(f"Updating {tool_name}")
            _run_command(["git", "-C", str(tool_dir), "pull"], cwd=str(tool_dir))
        else:
            info(f"Cloning {tool_name}")
            _run_command([
                "git", "clone", "-q", 
                f"https://github.com/{tool_slug}.git",
                str(tool_dir)
            ])

def _command_exists(command: str) -> bool:
    """Check if command exists in PATH"""
    try:
        subprocess.run([command], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def _run_command(cmd: list, cwd: str = None):
    """Run command and handle errors"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            warning(f"Command failed: {' '.join(cmd)}")
            warning(f"Error: {result.stderr}")
    except Exception as e:
        error(f"Failed to run command {' '.join(cmd)}: {e}")