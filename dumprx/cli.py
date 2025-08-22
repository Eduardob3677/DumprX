#!/usr/bin/env python3

import click
from rich.console import Console
from rich.panel import Panel

from dumprx.core.config import Config
from dumprx.core.device import DeviceInfo
from dumprx.utils.console import banner, console
from dumprx.utils.telegram import TelegramNotifier
from dumprx.downloaders.manager import DownloadManager
from dumprx.extractors.manager import ExtractionManager

@click.group()
@click.version_option("2.0.0", prog_name="DumprX")
@click.pass_context
def cli(ctx):
    """Modern Firmware Extraction and Analysis Tool"""
    ctx.ensure_object(dict)
    console.print(banner())

@cli.command()
@click.argument('input_path', required=True)
@click.option('--output', '-o', default='out', help='Output directory')
@click.option('--config', '-c', help='Configuration file path')
def extract(input_path, output, config):
    """Extract firmware from file or URL"""
    config_manager = Config(config)
    
    download_manager = DownloadManager(config_manager)
    extraction_manager = ExtractionManager(config_manager)
    telegram = TelegramNotifier(config_manager)
    
    console.print(f"[blue]Processing: {input_path}[/blue]")
    
    try:
        # Send start notification
        firmware_info = {
            'filename': input_path,
            'device_name': 'Unknown',
            'start_time': 'Now'
        }
        telegram.send_extraction_start(firmware_info)
        
        if input_path.startswith(('http://', 'https://', 'ftp://')):
            local_path = download_manager.download(input_path)
        else:
            local_path = input_path
        
        extraction_manager.extract(local_path, output)
        
        # Send completion notification
        result_info = {
            'success': True,
            'device_name': 'Unknown',
            'duration': 'Unknown',
            'partitions_count': 0,
            'files_count': 0
        }
        telegram.send_extraction_complete(result_info)
        
        console.print("[green]Extraction completed successfully![/green]")
        
    except Exception as e:
        telegram.send_error(str(e), f"Extracting {input_path}")
        console.print(f"[red]Extraction failed: {e}[/red]")
        raise

@cli.command()
@click.argument('url', required=True)
@click.option('--output', '-o', default='input', help='Download directory')
def download(url, output):
    """Download firmware from supported sources"""
    config_manager = Config()
    download_manager = DownloadManager(config_manager)
    
    console.print(f"[blue]Downloading: {url}[/blue]")
    local_path = download_manager.download(url, output)
    console.print(f"[green]Downloaded to: {local_path}[/green]")

@cli.group()
def config():
    """Configuration management"""
    pass

@config.command('show')
def config_show():
    """Show current configuration"""
    config_manager = Config()
    config_manager.show()

@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """Set configuration value"""
    config_manager = Config()
    config_manager.set(key, value)
    console.print(f"[green]Set {key} = {value}[/green]")

@cli.command()
def setup():
    """Setup dependencies and external tools"""
    from dumprx.core.setup import setup_dependencies
    setup_dependencies()

@cli.command()
def test():
    """Test integrations and dependencies"""
    from dumprx.core.test import run_tests
    from dumprx.utils.telegram import TelegramNotifier
    
    config_manager = Config()
    telegram = TelegramNotifier(config_manager)
    
    # Run standard tests
    run_tests()
    
    # Test Telegram if enabled
    if config_manager.get('telegram.enabled', False):
        console.print("\n[bold]Testing Telegram Integration:[/bold]")
        if telegram.test_connection():
            telegram.send_notification("🧪 DumprX test notification - all systems operational!")
        else:
            console.print("[red]Telegram integration test failed[/red]")

@cli.command()
def version():
    """Show version information"""
    from dumprx import __version__, __description__
    console.print(Panel(f"DumprX v{__version__}\n{__description__}", title="Version Info"))

if __name__ == '__main__':
    cli()