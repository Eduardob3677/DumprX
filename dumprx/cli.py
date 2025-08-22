#!/usr/bin/env python3

import sys
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .banner import show_banner, show_usage
from .utils import get_project_dir, ensure_directories, cleanup_directory, ProgressManager
from .external_tools import ExternalToolManager
from .firmware_extractor import FirmwareExtractor
from .boot_unpacker import BootImageUnpacker

console = Console()

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, version):
    if version:
        from . import __version__
        console.print(f"[green]DumprX v{__version__}[/green]")
        return
    
    if ctx.invoked_subcommand is None:
        show_banner()
        show_usage()

@cli.command()
@click.argument('firmware_path', type=click.Path())
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--setup-tools', is_flag=True, help='Setup external tools before extraction')
def dump(firmware_path: str, output: Optional[str], setup_tools: bool):
    show_banner()
    
    project_dir = get_project_dir()
    firmware_path = Path(firmware_path).resolve()
    
    if not firmware_path.exists():
        console.print(f"[red]Error: File or directory not found: {firmware_path}[/red]")
        sys.exit(1)
    
    # Setup output directory
    if output:
        output_dir = Path(output).resolve()
    else:
        output_dir = project_dir / "out"
    
    console.print(f"[blue]Extracting firmware to: {output_dir}[/blue]")
    
    # Setup tool manager
    tool_manager = ExternalToolManager(project_dir / "utils")
    
    if setup_tools:
        console.print("[blue]Setting up external tools...[/blue]")
        tool_manager.setup_external_tools()
        tool_manager.ensure_uv_available()
    
    # Create extractor and extract firmware
    extractor = FirmwareExtractor(project_dir)
    
    with ProgressManager() as progress:
        task = progress.add_task("Extracting firmware...", total=100)
        
        success = extractor.extract_firmware(firmware_path, output_dir)
        progress.update(task, completed=100)
    
    if success:
        console.print("[green]✅ Firmware extraction completed successfully![/green]")
        
        # Show extracted files
        _show_extraction_summary(output_dir)
    else:
        console.print("[red]❌ Firmware extraction failed![/red]")
        sys.exit(1)

@cli.command()
@click.argument('boot_image', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory for unpacked boot image')
def unpack_boot(boot_image: str, output: Optional[str]):
    show_banner()
    
    boot_img_path = Path(boot_image).resolve()
    
    if output:
        output_dir = Path(output).resolve()
    else:
        output_dir = boot_img_path.parent / f"{boot_img_path.stem}_unpacked"
    
    console.print(f"[blue]Unpacking boot image: {boot_img_path}[/blue]")
    console.print(f"[blue]Output directory: {output_dir}[/blue]")
    
    unpacker = BootImageUnpacker()
    success = unpacker.unpack_boot_image(boot_img_path, output_dir)
    
    if success:
        console.print("[green]✅ Boot image unpacked successfully![/green]")
    else:
        console.print("[red]❌ Boot image unpacking failed![/red]")
        sys.exit(1)

@cli.command()
def setup():
    show_banner()
    console.print("[blue]Setting up DumprX environment...[/blue]")
    
    project_dir = get_project_dir()
    
    # Ensure directories exist
    ensure_directories(
        project_dir / "input",
        project_dir / "out", 
        project_dir / "utils"
    )
    
    # Setup external tools
    tool_manager = ExternalToolManager(project_dir / "utils")
    tool_manager.setup_external_tools()
    tool_manager.ensure_uv_available()
    
    console.print("[green]✅ Setup completed successfully![/green]")

@cli.command()
@click.argument('path', type=click.Path(), required=False)
def info(path: Optional[str]):
    show_banner()
    
    if not path:
        _show_project_info()
        return
    
    file_path = Path(path).resolve()
    
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        return
    
    project_dir = get_project_dir()
    tool_manager = ExternalToolManager(project_dir / "utils")
    
    from .firmware_detector import FirmwareDetector
    detector = FirmwareDetector(tool_manager)
    
    try:
        firmware_info = detector.detect_firmware_type(file_path)
        _show_firmware_info(file_path, firmware_info)
    except Exception as e:
        console.print(f"[red]Error analyzing file: {e}[/red]")

@cli.command()
def clean():
    show_banner()
    console.print("[yellow]Cleaning temporary files...[/yellow]")
    
    project_dir = get_project_dir()
    
    # Clean output and temp directories
    cleanup_dirs = [
        project_dir / "out" / "tmp",
        project_dir / "input"
    ]
    
    for cleanup_dir in cleanup_dirs:
        if cleanup_dir.exists():
            cleanup_directory(cleanup_dir)
            console.print(f"[green]Cleaned: {cleanup_dir}[/green]")
    
    console.print("[green]✅ Cleanup completed![/green]")

def _show_project_info():
    project_dir = get_project_dir()
    
    table = Table(title="DumprX Project Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Path", style="blue")
    
    # Check directories
    dirs = [
        ("Project Directory", project_dir),
        ("Utils Directory", project_dir / "utils"),
        ("Input Directory", project_dir / "input"),
        ("Output Directory", project_dir / "out")
    ]
    
    for name, dir_path in dirs:
        status = "✅ Exists" if dir_path.exists() else "❌ Missing"
        table.add_row(name, status, str(dir_path))
    
    console.print(table)

def _show_firmware_info(file_path: Path, info: dict):
    panel_title = f"Firmware Analysis: {file_path.name}"
    
    info_text = f"""
[bold]File:[/bold] {file_path}
[bold]Type:[/bold] {info.get('type', 'unknown')}
[bold]Format:[/bold] {info.get('format', 'Unknown')}
[bold]Size:[/bold] {file_path.stat().st_size / (1024*1024):.2f} MB
    """
    
    if 'needs_decryption' in info:
        info_text += f"\n[yellow]⚠️  Requires decryption[/yellow]"
    
    if 'archive_type' in info:
        info_text += f"\n[bold]Archive Type:[/bold] {info['archive_type']}"
    
    if 'contains' in info:
        info_text += f"\n[bold]Contains:[/bold] {info['contains']}"
    
    if 'archives' in info:
        info_text += f"\n[bold]Archives:[/bold] {', '.join(info['archives'])}"
    
    panel = Panel(info_text, title=panel_title, border_style="blue")
    console.print(panel)

def _show_extraction_summary(output_dir: Path):
    if not output_dir.exists():
        return
    
    table = Table(title="Extracted Files")
    table.add_column("File", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Type", style="blue")
    
    for item in output_dir.iterdir():
        if item.is_file():
            size_mb = item.stat().st_size / (1024 * 1024)
            file_type = "Image" if item.suffix in ['.img', '.bin'] else "File"
            table.add_row(item.name, f"{size_mb:.2f} MB", file_type)
    
    console.print(table)

if __name__ == '__main__':
    cli()