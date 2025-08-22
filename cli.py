import click
import sys
from pathlib import Path

from core.config import Config
from core.device import DeviceInfo
from core.processor import FirmwareProcessor
from utils.console import Console
from utils.git import GitManager
from modules.banner import display_banner


@click.group()
@click.version_option(version="2.0.0")
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)
    display_banner()


@cli.command()
@click.argument('firmware_path')
@click.option('--output', '-o', default='out', help='Output directory')
@click.option('--config', '-c', help='Config file path')
@click.pass_context
def extract(ctx, firmware_path, output, config):
    console = Console()
    config_obj = Config(config)
    
    console.info(f"Processing firmware: {firmware_path}")
    
    processor = FirmwareProcessor(
        firmware_path=firmware_path,
        output_dir=output,
        config=config_obj
    )
    
    try:
        processor.process()
        console.success("Firmware processing completed successfully")
    except Exception as e:
        console.error(f"Processing failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('url')
@click.option('--output', '-o', default='input', help='Download directory')
@click.pass_context
def download(ctx, url, output):
    console = Console()
    console.info(f"Downloading from: {url}")
    
    from downloaders.manager import DownloadManager
    
    manager = DownloadManager(output_dir=output)
    try:
        downloaded_file = manager.download(url)
        console.success(f"Downloaded: {downloaded_file}")
    except Exception as e:
        console.error(f"Download failed: {e}")
        sys.exit(1)


@cli.group()
def config():
    pass


@config.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    console = Console()
    config_obj = Config()
    config_obj.set(key, value)
    console.success(f"Set {key} = {value}")


@config.command()
@click.argument('key', required=False)
def show(key):
    console = Console()
    config_obj = Config()
    if key:
        value = config_obj.get(key)
        console.info(f"{key} = {value}")
    else:
        config_obj.show_all()


@cli.command()
def setup():
    console = Console()
    console.info("Setting up dependencies...")
    
    from core.setup import DependencyManager
    
    manager = DependencyManager()
    try:
        manager.setup_all()
        console.success("Setup completed successfully")
    except Exception as e:
        console.error(f"Setup failed: {e}")
        sys.exit(1)


@cli.command()
def test():
    console = Console()
    console.info("Running integration tests...")
    
    from core.test import TestRunner
    
    runner = TestRunner()
    try:
        results = runner.run_all()
        if results['success']:
            console.success("All tests passed")
        else:
            console.error(f"Tests failed: {results['failures']}")
            sys.exit(1)
    except Exception as e:
        console.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()