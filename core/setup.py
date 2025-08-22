import os
import subprocess
import platform
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def setup_dependencies():
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        task = progress.add_task("Setting up dependencies...", total=4)
        
        progress.update(task, description="Detecting system...")
        system = platform.system().lower()
        progress.advance(task)
        
        progress.update(task, description="Installing system packages...")
        _install_system_packages(system)
        progress.advance(task)
        
        progress.update(task, description="Installing Python packages...")
        _install_python_packages()
        progress.advance(task)
        
        progress.update(task, description="Installing UV package manager...")
        _install_uv()
        progress.advance(task)
        
        console.print("[bold green]✅ Setup completed successfully![/bold green]")

def _install_system_packages(system):
    if system == "linux":
        _install_linux_packages()
    elif system == "darwin":
        _install_macos_packages()
    else:
        console.print(f"[yellow]Warning: Unsupported system: {system}[/yellow]")
        console.print("Please install dependencies manually")

def _install_linux_packages():
    distro = _detect_linux_distro()
    
    if distro == "debian":
        packages = [
            "unace", "unrar", "zip", "unzip", "p7zip-full", "p7zip-rar",
            "sharutils", "rar", "uudeview", "mpack", "arj", "cabextract",
            "device-tree-compiler", "liblzma-dev", "python3-pip", "brotli",
            "liblz4-tool", "axel", "gawk", "aria2", "detox", "cpio", "rename",
            "liblz4-dev", "jq", "git-lfs"
        ]
        
        _run_command("sudo apt -y update")
        _run_command(f"sudo apt install -y {' '.join(packages)}")
        
    elif distro == "fedora":
        packages = [
            "unace", "unrar", "zip", "unzip", "p7zip", "p7zip-plugins",
            "sharutils", "uudeview", "arj", "cabextract", "dtc", "xz-devel",
            "python3-pip", "brotli", "lz4", "axel", "gawk", "aria2", "detox",
            "cpio", "lz4-devel", "jq", "git-lfs"
        ]
        
        _run_command(f"sudo dnf install -y {' '.join(packages)}")
        
    elif distro == "arch":
        packages = [
            "unace", "unrar", "zip", "unzip", "p7zip", "sharutils", "uudeview",
            "arj", "cabextract", "dtc", "xz", "python-pip", "brotli", "lz4",
            "aria2", "detox", "cpio", "jq", "git-lfs"
        ]
        
        _run_command(f"sudo pacman -S --noconfirm {' '.join(packages)}")
        
    else:
        console.print(f"[yellow]Warning: Unsupported Linux distro: {distro}[/yellow]")

def _install_macos_packages():
    packages = [
        "protobuf", "xz", "brotli", "lz4", "aria2", "detox",
        "coreutils", "p7zip", "gawk", "git-lfs"
    ]
    
    _run_command(f"brew install {' '.join(packages)}")

def _detect_linux_distro():
    try:
        if _command_exists("apt"):
            return "debian"
        elif _command_exists("dnf"):
            return "fedora"
        elif _command_exists("pacman"):
            return "arch"
        else:
            return "unknown"
    except:
        return "unknown"

def _install_python_packages():
    _run_command("pip3 install --user -e .")

def _install_uv():
    try:
        _run_command('bash -c "$(curl -sL https://astral.sh/uv/install.sh)"')
    except Exception as e:
        console.print(f"[yellow]Warning: UV installation failed: {e}[/yellow]")

def _command_exists(command):
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except:
        return False

def _run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Command failed: {command}[/red]")
        console.print(f"[red]Error: {e.stderr}[/red]")
        raise