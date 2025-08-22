import click
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from dumprx import __version__
from core.config import Config
from core.dumper import FirmwareDumper

console = Console()

def show_banner():
    banner = Text.from_markup("""
[bold green]
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
[/bold green]
""")
    console.print(Panel(banner, title="DumprX v2.0", border_style="green"))

@click.group()
@click.version_option(version=__version__)
def main():
    show_banner()

@main.command()
@click.argument('firmware_input')
@click.option('--output', '-o', default='out', help='Output directory')
@click.option('--config', '-c', help='Config file path')
def dump(firmware_input, output, config):
    console.print(f"[bold blue]Starting firmware dump process...[/bold blue]")
    console.print(f"Input: {firmware_input}")
    console.print(f"Output: {output}")
    
    try:
        config_obj = Config(config)
        dumper = FirmwareDumper(config_obj, output)
        dumper.process_firmware(firmware_input)
        console.print("[bold green]✅ Firmware dump completed successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error: {str(e)}[/bold red]")
        raise click.Abort()

@main.command()
@click.argument('url')
@click.option('--output', '-o', default='input', help='Download directory')
def download(url, output):
    console.print(f"[bold blue]Downloading from: {url}[/bold blue]")
    from downloaders.manager import DownloadManager
    
    try:
        manager = DownloadManager(output)
        manager.download(url)
        console.print("[bold green]✅ Download completed![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Download failed: {str(e)}[/bold red]")
        raise click.Abort()

@main.group()
def config():
    pass

@config.command()
def show():
    config_obj = Config()
    config_obj.show()

@config.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    config_obj = Config()
    config_obj.set(key, value)
    console.print(f"[green]Set {key} = {value}[/green]")

@main.command()
def setup():
    console.print("[bold blue]Setting up DumprX dependencies...[/bold blue]")
    from core.setup import setup_dependencies
    
    try:
        setup_dependencies()
        console.print("[bold green]✅ Setup completed![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Setup failed: {str(e)}[/bold red]")
        raise click.Abort()

@main.command()
@click.option('--config-vars', help='Config variables as JSON')
@click.option('--firmware-url', required=True, help='Firmware URL to process')
@click.option('--output', '-o', default='out', help='Output directory')
def system_dump(config_vars, firmware_url, output):
    console.print("[bold blue]Starting system dump process...[/bold blue]")
    console.print(f"Firmware URL: {firmware_url}")
    
    try:
        config_obj = Config()
        if config_vars:
            import json
            vars_dict = json.loads(config_vars)
            for key, value in vars_dict.items():
                config_obj.set(key, value)
        
        dumper = FirmwareDumper(config_obj, output)
        dumper.process_firmware(firmware_url)
        console.print("[bold green]✅ System dump completed![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ System dump failed: {str(e)}[/bold red]")
        raise click.Abort()

if __name__ == '__main__':
    main()