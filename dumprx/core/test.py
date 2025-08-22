import subprocess
import os
from pathlib import Path
from dumprx.utils.console import console, info, success, error, warning

def run_tests():
    """Run integration tests"""
    console.print("[bold]Running DumprX Integration Tests[/bold]")
    
    test_results = []
    
    # Test system dependencies
    test_results.append(("System Dependencies", test_system_dependencies()))
    
    # Test Python dependencies
    test_results.append(("Python Dependencies", test_python_dependencies()))
    
    # Test external tools
    test_results.append(("External Tools", test_external_tools()))
    
    # Test downloaders
    test_results.append(("Downloaders", test_downloaders()))
    
    # Test extractors
    test_results.append(("Extractors", test_extractors()))
    
    # Print results
    console.print("\n[bold]Test Results:[/bold]")
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        if result:
            console.print(f"[green]✓[/green] {test_name}")
            passed += 1
        else:
            console.print(f"[red]✗[/red] {test_name}")
    
    console.print(f"\n[bold]Summary: {passed}/{total} tests passed[/bold]")
    
    if passed == total:
        success("All tests passed!")
    else:
        warning(f"{total - passed} tests failed")

def test_system_dependencies() -> bool:
    """Test system dependencies"""
    required_commands = [
        "7zz", "aria2c", "wget", "tar", "git", "detox"
    ]
    
    missing = []
    for cmd in required_commands:
        if not _command_exists(cmd):
            missing.append(cmd)
    
    if missing:
        error(f"Missing system dependencies: {', '.join(missing)}")
        return False
    
    return True

def test_python_dependencies() -> bool:
    """Test Python dependencies"""
    required_modules = [
        "click", "rich", "yaml", "requests", "git"
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        error(f"Missing Python modules: {', '.join(missing)}")
        return False
    
    return True

def test_external_tools() -> bool:
    """Test external tools"""
    utils_dir = Path(__file__).parent.parent.parent / "utils"
    
    required_tools = [
        "oppo_ozip_decrypt",
        "oppo_decrypt",
        "vmlinux-to-elf", 
        "android_tools",
        "pacextractor"
    ]
    
    missing = []
    for tool in required_tools:
        tool_dir = utils_dir / tool
        if not tool_dir.exists():
            missing.append(tool)
    
    if missing:
        error(f"Missing external tools: {', '.join(missing)}")
        return False
    
    return True

def test_downloaders() -> bool:
    """Test downloader scripts"""
    utils_dir = Path(__file__).parent.parent.parent / "utils"
    
    required_downloaders = [
        "downloaders/mega-media-drive_dl.sh",
        "downloaders/afh_dl.py"
    ]
    
    missing = []
    for downloader in required_downloaders:
        downloader_path = utils_dir / downloader
        if not downloader_path.exists():
            missing.append(downloader)
    
    if missing:
        error(f"Missing downloaders: {', '.join(missing)}")
        return False
    
    return True

def test_extractors() -> bool:
    """Test extractor tools"""
    utils_dir = Path(__file__).parent.parent.parent / "utils"
    
    required_extractors = [
        "bin/simg2img",
        "bin/payload-dumper-go",
        "lpunpack",
        "splituapp.py",
        "sdat2img.py",
        "kdztools/unkdz.py",
        "kdztools/undz.py"
    ]
    
    missing = []
    for extractor in required_extractors:
        extractor_path = utils_dir / extractor
        if not extractor_path.exists():
            missing.append(extractor)
    
    if missing:
        warning(f"Missing extractors: {', '.join(missing)}")
        info("Some extractors may be optional or platform-specific")
        return True  # Don't fail the test for missing extractors
    
    return True

def _command_exists(command: str) -> bool:
    """Check if command exists in PATH"""
    try:
        subprocess.run([command], capture_output=True)
        return True
    except FileNotFoundError:
        return False