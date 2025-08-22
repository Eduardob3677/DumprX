import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
import sys
from pathlib import Path

from dumprx.core.firmware_processor import FirmwareProcessor
from dumprx.core import setup_directories, cleanup_temp

console = Console()

def show_banner():
    banner_text = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
    """
    
    panel = Panel(
        Text(banner_text, style="bold green"),
        title="[bold blue]DumprX - Modern Firmware Dumper[/bold blue]",
        border_style="green"
    )
    console.print(panel)

def show_usage():
    usage_text = """
[bold green]🔧 Usage:[/bold green] dumprx <firmware_file_or_url>

[bold blue]📁 Supported File Formats:[/bold blue]
  • *.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5
  • *.ozip | *.ofp | *.ops | *.kdz | ruu_*.exe
  • system.new.dat | system.new.dat.br | system.new.dat.xz
  • system.new.img | system.img | system-sign.img | UPDATE.APP
  • *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin
  • *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin

[bold blue]🌐 Supported Websites:[/bold blue]
  • Direct download links from any website
  • File hosters: mega.nz | mediafire | gdrive | onedrive | androidfilehost

[bold yellow]⚠️  Note:[/bold yellow] Wrap website URLs in quotes when using as arguments
    """
    console.print(Panel(usage_text, border_style="blue"))

@click.command()
@click.argument('target', required=False)
@click.option('--url', '-u', help='🌐 Firmware download URL')
@click.option('--config', '-c', help='⚙️  Configuration file path')
@click.option('--output', '-o', help='📤 Output directory')
@click.option('--verbose', '-v', is_flag=True, help='🔍 Verbose output')
@click.option('--github-token', help='🔐 GitHub token for uploads')
@click.option('--telegram-token', help='📱 Telegram bot token')
@click.option('--chat-id', help='💬 Telegram chat ID')
def main(target, url, config, output, verbose, github_token, telegram_token, chat_id):
    show_banner()
    
    if not target and not url:
        show_usage()
        console.print("[bold red]❌ Error:[/bold red] Please provide a firmware file path or URL")
        sys.exit(1)
    
    setup_directories()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task("[green]🚀 Initializing firmware processor...", total=100)
            
            processor = FirmwareProcessor(
                console=console,
                progress=progress,
                github_token=github_token,
                telegram_token=telegram_token,
                chat_id=chat_id,
                verbose=verbose
            )
            
            progress.update(task, advance=20)
            
            firmware_source = target or url
            progress.update(task, description=f"[blue]📥 Processing: {firmware_source}")
            
            result = processor.process_firmware(firmware_source, output)
            
            progress.update(task, completed=100)
            
            if result:
                console.print("\n[bold green]✅ Firmware dump completed successfully![/bold green]")
            else:
                console.print("\n[bold red]❌ Firmware dump failed![/bold red]")
                sys.exit(1)
                
    except KeyboardInterrupt:
        console.print("\n[bold yellow]⚠️  Operation cancelled by user[/bold yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {str(e)}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)
    finally:
        cleanup_temp()

if __name__ == "__main__":
    main()