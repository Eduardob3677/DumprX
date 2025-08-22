import click
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.table import Table

from dumprx.core.config import Config
from dumprx.utils.banner import show_banner, show_usage
from dumprx.utils.detection import FileDetector
from dumprx.utils.tools import ToolManager
from dumprx.core.dumper import FirmwareDumper

console = Console()

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, version):
    if version:
        from dumprx import __version__
        console.print(f"[bold green]DumprX v{__version__}[/bold green]")
        return
    
    if ctx.invoked_subcommand is None:
        show_banner()
        show_usage()

@cli.command()
@click.argument('firmware_path', type=str)
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory for extracted files')
@click.option('--no-upload', is_flag=True, help='Skip uploading to Git repository')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def dump(firmware_path, output_dir, no_upload, verbose):
    console.clear()
    show_banner()
    
    try:
        config = Config()
        if output_dir:
            config.output_dir = Path(output_dir)
            config.tmp_dir = config.output_dir / "tmp"
            config._setup_directories()
        
        detector = FileDetector(config)
        tool_manager = ToolManager(config)
        
        missing_deps = tool_manager.check_dependencies()
        if missing_deps:
            console.print(f"[red]Missing dependencies: {', '.join(missing_deps)}[/red]")
            console.print("[yellow]Please run the setup script first[/yellow]")
            sys.exit(1)
        
        firmware_input = Path(firmware_path) if os.path.exists(firmware_path) else firmware_path
        
        if isinstance(firmware_input, Path):
            if not firmware_input.exists():
                console.print(f"[red]File or directory not found: {firmware_input}[/red]")
                sys.exit(1)
            
            file_info = detector.get_file_info(firmware_input)
            
            if not detector.is_supported_format(firmware_input):
                console.print(f"[red]Unsupported firmware format: {file_info['type']}[/red]")
                console.print("[yellow]Supported formats:[/yellow]")
                show_usage()
                sys.exit(1)
                
            console.print(Panel(
                f"[green]Firmware detected:[/green] {file_info['description']}\n"
                f"[blue]File:[/blue] {file_info['name']}\n"
                f"[blue]Size:[/blue] {file_info['size']:,} bytes",
                title="📱 Firmware Information"
            ))
        else:
            console.print(Panel(
                f"[green]URL detected:[/green] {firmware_input}\n"
                f"[yellow]Will attempt to download firmware[/yellow]",
                title="🌐 Download Information"
            ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            
            setup_task = progress.add_task("Setting up tools...", total=100)
            tool_manager.setup_external_tools()
            progress.update(setup_task, completed=100)
            
            dumper = FirmwareDumper(config, tool_manager, detector, progress, console)
            
            dump_task = progress.add_task("Processing firmware...", total=100)
            
            success = dumper.process_firmware(firmware_input, verbose=verbose, no_upload=no_upload)
            
            progress.update(dump_task, completed=100)
        
        if success:
            console.print(Panel(
                f"[green]✅ Firmware extraction completed successfully![/green]\n"
                f"[blue]Output directory:[/blue] {config.output_dir}",
                title="🎉 Success"
            ))
        else:
            console.print(Panel(
                "[red]❌ Firmware extraction failed![/red]\n"
                "[yellow]Check the output above for error details[/yellow]",
                title="💥 Failed"
            ))
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]💥 Unexpected error: {str(e)}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)

@cli.command()
def setup():
    console.clear()
    show_banner()
    
    console.print("[blue]🔧 Setting up DumprX dependencies...[/blue]")
    
    try:
        config = Config()
        tool_manager = ToolManager(config)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            task = progress.add_task("Checking dependencies...", total=100)
            missing_deps = tool_manager.check_dependencies()
            progress.update(task, completed=50)
            
            if missing_deps:
                progress.update(task, description=f"Missing: {', '.join(missing_deps)}")
                console.print(f"[red]Missing dependencies: {', '.join(missing_deps)}[/red]")
                console.print("[yellow]Please install them using your system package manager[/yellow]")
            else:
                progress.update(task, description="All dependencies available")
                progress.update(task, completed=100)
            
            tool_task = progress.add_task("Setting up external tools...", total=100)
            tool_manager.setup_external_tools()
            progress.update(tool_task, completed=100)
        
        console.print(Panel(
            "[green]✅ Setup completed successfully![/green]\n"
            "[blue]You can now use dumprx to extract firmware[/blue]",
            title="🎉 Setup Complete"
        ))
        
    except Exception as e:
        console.print(f"[red]💥 Setup failed: {str(e)}[/red]")
        sys.exit(1)

@cli.command()
@click.argument('firmware_path', type=click.Path(exists=True))
def info(firmware_path):
    console.clear()
    show_banner()
    
    try:
        config = Config()
        detector = FileDetector(config)
        
        firmware_file = Path(firmware_path)
        file_info = detector.get_file_info(firmware_file)
        
        table = Table(title="📱 Firmware Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("File Name", file_info['name'])
        table.add_row("File Path", str(file_info['path']))
        table.add_row("File Size", f"{file_info['size']:,} bytes")
        table.add_row("File Type", file_info['type'])
        table.add_row("Description", file_info['description'])
        if file_info['extension']:
            table.add_row("Extension", file_info['extension'])
        table.add_row("Supported", "✅ Yes" if detector.is_supported_format(firmware_file) else "❌ No")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]💥 Error getting file info: {str(e)}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    cli()