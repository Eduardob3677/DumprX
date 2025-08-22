import click
import sys
from pathlib import Path
from dumprx.utils.banner import show_banner, show_usage
from dumprx.utils.logging import logger
from dumprx.core.config import config
from dumprx.core.device import DeviceDetector
from dumprx.core.extractor import FirmwareExtractor

@click.command()
@click.argument('input_path', required=False)
@click.option('--output', '-o', help='Output directory')
@click.option('--github-token', help='GitHub token for uploading dumps')
@click.option('--telegram-token', help='Telegram bot token')
@click.option('--chat-id', help='Telegram chat ID')
@click.option('--version', '-v', is_flag=True, help='Show version')
def main(input_path, output, github_token, telegram_token, chat_id, version):
    if version:
        from dumprx import __version__
        click.echo(f"DumprX version {__version__}")
        return
        
    show_banner()
    
    if not input_path:
        logger.error("No Input Is Given.")
        show_usage()
        sys.exit(1)
        
    try:
        config.ensure_directories()
        if output:
            config.output_dir = Path(output)
            config.output_dir.mkdir(parents=True, exist_ok=True)
            
        device_detector = DeviceDetector()
        extractor = FirmwareExtractor(config, device_detector)
        
        result = extractor.extract(input_path)
        if result:
            logger.success("Firmware extraction completed successfully!")
        else:
            logger.error("Firmware extraction failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()