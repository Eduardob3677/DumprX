import sys
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from dumprx.core.config import Config
from dumprx.core.tools import ExternalToolsManager
from dumprx.extractors.firmware import FirmwareExtractor


def print_banner(console: Console):
    banner_text = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
    """
    
    panel = Panel.fit(
        Text(banner_text, style="green bold"),
        title="DumprX v2.0",
        subtitle="Modern Firmware Extraction Toolkit"
    )
    console.print(panel)


def print_usage(console: Console):
    usage_text = """
[bold green]Usage:[/bold green] dumprx [OPTIONS] FIRMWARE_PATH

[bold blue]Supported Websites:[/bold blue]
• Direct download links from any website  
• Filehosters: mega.nz | mediafire | gdrive | onedrive | androidfilehost
• Website links must be wrapped in single quotes ('')

[bold blue]Supported File Formats:[/bold blue]
• Archives: *.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5
• Encrypted: *.ozip | *.ofp | *.ops | *.kdz | ruu_*.exe  
• Android: system.new.dat | system.new.dat.br | system.new.dat.xz
• Images: system.new.img | system.img | system-sign.img | UPDATE.APP
• Others: *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin
• Device: *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin
    """
    console.print(usage_text)


@click.command()
@click.argument('firmware_path', required=False)
@click.option('--setup-tools', is_flag=True, help='Setup external tools only')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--config-dir', help='Custom configuration directory')
def main(firmware_path: str, setup_tools: bool, verbose: bool, config_dir: str):
    console = Console()
    
    print_banner(console)
    
    if not firmware_path and not setup_tools:
        console.print("[red]Error: No input provided[/red]\n")
        print_usage(console)
        sys.exit(1)
    
    if ' ' in str(Path.cwd()):
        console.print("[red]Error: Project directory path contains spaces.[/red]")
        console.print("Please move the script to a proper UNIX-formatted folder.")
        sys.exit(1)
    
    try:
        config = Config(config_dir)
        tools_manager = ExternalToolsManager(config, console)
        
        if setup_tools:
            console.print("[blue]Setting up external tools...[/blue]")
            if tools_manager.setup_external_tools():
                console.print("[green]✓ External tools setup complete[/green]")
            else:
                console.print("[red]✗ External tools setup failed[/red]")
                sys.exit(1)
            return
        
        console.print(f"[blue]Processing firmware: {firmware_path}[/blue]")
        
        tools_manager.setup_external_tools()
        
        extractor = FirmwareExtractor(config, console, verbose)
        success = extractor.extract(firmware_path)
        
        if success:
            console.print("[green]✓ Firmware extraction completed successfully[/green]")
        else:
            console.print("[red]✗ Firmware extraction failed[/red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()