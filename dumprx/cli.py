"""
DumprX CLI - Modern command-line interface for firmware extraction.

Provides Click-based CLI with multiple commands for different operations.
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from dumprx.core.config import Config
from dumprx.utils.console import print_banner, print_error, print_success, print_info
from dumprx.utils.git import GitManager
from dumprx.modules.formatter import format_device_info

console = Console()


@click.group(invoke_without_command=True)
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Path to configuration file'
)
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def main(ctx, config, verbose):
    """
    DumprX - Professional firmware extraction and analysis toolkit.
    
    A modern Python-based firmware dumper with CLI interface.
    """
    if ctx.invoked_subcommand is None:
        print_banner()
        click.echo()
        click.echo("Use 'dumprx --help' for available commands.")
        click.echo("Use 'dumprx dump <firmware>' to extract firmware.")
        return
    
    # Store configuration in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose


@main.command()
@click.argument('firmware', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output directory for extracted files'
)
@click.option(
    '--download-only', '-d',
    is_flag=True,
    help='Only download, do not extract'
)
@click.option(
    '--extract-only', '-e', 
    is_flag=True,
    help='Only extract, do not download'
)
@click.option(
    '--no-git', 
    is_flag=True,
    help='Skip git repository creation'
)
@click.option(
    '--no-upload',
    is_flag=True, 
    help='Skip uploading to git hosting'
)
@click.pass_context
def dump(ctx, firmware, output, download_only, extract_only, no_git, no_upload):
    """
    Extract firmware files from various formats.
    
    FIRMWARE can be:
    - Local firmware file (.zip, .rar, .7z, .tar, .bin, .ozip, .kdz, etc.)
    - Extracted firmware folder
    - Supported website URL (mega.nz, mediafire, gdrive, androidfilehost)
    """
    from dumprx.core.main import FirmwareDumper
    
    try:
        config = Config.load(ctx.obj.get('config_path'))
        
        if output:
            config.output_dir = output
            
        dumper = FirmwareDumper(config)
        
        print_banner()
        print_info(f"Starting firmware extraction: {firmware}")
        
        result = dumper.process_firmware(
            firmware,
            download_only=download_only,
            extract_only=extract_only,
            create_git_repo=not no_git,
            upload_to_git=not no_upload
        )
        
        if result.success:
            print_success("Firmware extraction completed successfully!")
            if result.output_dir:
                print_info(f"Output directory: {result.output_dir}")
            if result.git_repo_url:
                print_info(f"Git repository: {result.git_repo_url}")
        else:
            print_error(f"Firmware extraction failed: {result.error}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Error: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('url', type=str)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output directory for downloaded files'
)
@click.option(
    '--service', '-s',
    type=click.Choice(['auto', 'mega', 'mediafire', 'gdrive', 'androidfilehost']),
    default='auto',
    help='Specify download service (auto-detect by default)'
)
@click.pass_context
def download(ctx, url, output, service):
    """
    Download firmware from supported hosting services.
    
    Supports: mega.nz, mediafire.com, Google Drive, AndroidFileHost
    """
    from dumprx.downloaders import get_downloader
    
    try:
        config = Config.load(ctx.obj.get('config_path'))
        
        if output:
            config.input_dir = output
        
        print_banner()
        print_info(f"Downloading from: {url}")
        
        downloader = get_downloader(url, service)
        if not downloader:
            print_error(f"Unsupported URL or service: {url}")
            sys.exit(1)
        
        result = downloader.download(url, config.input_dir)
        
        if result.success:
            print_success(f"Download completed: {result.filepath}")
        else:
            print_error(f"Download failed: {result.error}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Error: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.group()
def config():
    """Configuration management commands."""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    try:
        config = Config.load(ctx.obj.get('config_path'))
        
        print_banner()
        
        # Display configuration in a nice format
        config_panel = Panel(
            _format_config_display(config),
            title="DumprX Configuration",
            border_style="blue"
        )
        console.print(config_panel)
        
    except Exception as e:
        print_error(f"Error loading configuration: {e}")
        sys.exit(1)


@config.command('set')
@click.argument('key', type=str)
@click.argument('value', type=str)
@click.pass_context
def config_set(ctx, key, value):
    """Set configuration value."""
    try:
        config = Config.load(ctx.obj.get('config_path'))
        
        # Parse key path (e.g., "git.github_token")
        parts = key.split('.')
        if len(parts) != 2:
            print_error("Key must be in format 'section.key' (e.g., 'git.github_token')")
            sys.exit(1)
        
        section, setting = parts
        
        # Set the value
        if section == 'git':
            if hasattr(config.git, setting):
                setattr(config.git, setting, value)
            else:
                print_error(f"Unknown git setting: {setting}")
                sys.exit(1)
        elif section == 'telegram':
            if hasattr(config.telegram, setting):
                # Handle boolean values
                if setting == 'enabled':
                    value = value.lower() in ('true', '1', 'yes', 'on')
                setattr(config.telegram, setting, value)
            else:
                print_error(f"Unknown telegram setting: {setting}")
                sys.exit(1)
        elif section == 'download':
            if hasattr(config.download, setting):
                # Handle numeric values
                if setting in ('timeout', 'retry_count', 'chunk_size'):
                    try:
                        value = int(value)
                    except ValueError:
                        print_error(f"Setting {setting} requires a numeric value")
                        sys.exit(1)
                setattr(config.download, setting, value)
            else:
                print_error(f"Unknown download setting: {setting}")
                sys.exit(1)
        elif section == 'extraction':
            if hasattr(config.extraction, setting):
                # Handle boolean values
                if setting in ('preserve_permissions', 'create_structure_info', 'extract_recovery', 'extract_dtbo'):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                setattr(config.extraction, setting, value)
            else:
                print_error(f"Unknown extraction setting: {setting}")
                sys.exit(1)
        else:
            print_error(f"Unknown configuration section: {section}")
            sys.exit(1)
        
        # Save configuration
        config.save()
        print_success(f"Configuration updated: {key} = {value}")
        
    except Exception as e:
        print_error(f"Error setting configuration: {e}")
        sys.exit(1)


@main.command()
@click.option(
    '--force', '-f',
    is_flag=True,
    help='Force reinstall dependencies'
)
@click.pass_context  
def setup(ctx, force):
    """Setup dependencies and external tools."""
    from dumprx.core.setup import SetupManager
    
    try:
        config = Config.load(ctx.obj.get('config_path'))
        
        print_banner()
        print_info("Setting up DumprX dependencies...")
        
        setup_manager = SetupManager(config)
        result = setup_manager.setup_all(force=force)
        
        if result.success:
            print_success("Setup completed successfully!")
        else:
            print_error(f"Setup failed: {result.error}")
            sys.exit(1)
            
    except Exception as e:
        print_error(f"Setup error: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.option(
    '--download', '-d',
    is_flag=True,
    help='Test download functionality'
)
@click.option(
    '--extract', '-e',
    is_flag=True, 
    help='Test extraction functionality'
)
@click.option(
    '--git', '-g',
    is_flag=True,
    help='Test git integration'
)
@click.option(
    '--telegram', '-t',
    is_flag=True,
    help='Test telegram notifications'
)
@click.pass_context
def test(ctx, download, extract, git, telegram):
    """Test various integrations and functionality."""
    from dumprx.core.testing import TestRunner
    
    try:
        config = Config.load(ctx.obj.get('config_path'))
        
        print_banner()
        print_info("Running DumprX tests...")
        
        test_runner = TestRunner(config)
        
        if download:
            test_runner.test_downloads()
        if extract:
            test_runner.test_extraction()
        if git:
            test_runner.test_git_integration()
        if telegram:
            test_runner.test_telegram()
        
        if not any([download, extract, git, telegram]):
            # Run all tests
            test_runner.test_all()
        
        print_success("All tests completed!")
        
    except Exception as e:
        print_error(f"Test error: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
def version():
    """Show version information."""
    from dumprx import __version__, __description__
    
    print_banner()
    
    version_text = Text()
    version_text.append("DumprX ", style="bold cyan")
    version_text.append(f"v{__version__}", style="bold green")
    version_text.append(f"\n{__description__}", style="dim")
    
    version_panel = Panel(
        version_text,
        title="Version Information",
        border_style="green"
    )
    console.print(version_panel)


def _format_config_display(config: Config) -> str:
    """Format configuration for display."""
    lines = []
    
    lines.append("[bold cyan]Directories:[/bold cyan]")
    lines.append(f"  Project: {config.project_dir}")
    lines.append(f"  Input:   {config.input_dir}")
    lines.append(f"  Output:  {config.output_dir}")
    lines.append(f"  Utils:   {config.utils_dir}")
    lines.append(f"  Bin:     {config.bin_dir}")
    lines.append("")
    
    lines.append("[bold cyan]Git Configuration:[/bold cyan]")
    lines.append(f"  GitHub Token:    {'[SET]' if config.git.github_token else '[NOT SET]'}")
    lines.append(f"  GitHub Org:      {config.git.github_org or '[NOT SET]'}")
    lines.append(f"  GitLab Token:    {'[SET]' if config.git.gitlab_token else '[NOT SET]'}")
    lines.append(f"  GitLab Group:    {config.git.gitlab_group or '[NOT SET]'}")
    lines.append(f"  GitLab Instance: {config.git.gitlab_instance or '[NOT SET]'}")
    lines.append(f"  Push to GitLab:  {config.git.push_to_gitlab}")
    lines.append("")
    
    lines.append("[bold cyan]Telegram Configuration:[/bold cyan]")
    lines.append(f"  Token:   {'[SET]' if config.telegram.token else '[NOT SET]'}")
    lines.append(f"  Chat ID: {config.telegram.chat_id or '[NOT SET]'}")
    lines.append(f"  Enabled: {config.telegram.enabled}")
    lines.append("")
    
    lines.append("[bold cyan]Download Configuration:[/bold cyan]")
    lines.append(f"  Timeout:     {config.download.timeout}s")
    lines.append(f"  Retry Count: {config.download.retry_count}")
    lines.append(f"  Chunk Size:  {config.download.chunk_size}")
    lines.append(f"  User Agent:  {config.download.user_agent}")
    lines.append("")
    
    lines.append("[bold cyan]Extraction Configuration:[/bold cyan]")
    lines.append(f"  Preserve Permissions:  {config.extraction.preserve_permissions}")
    lines.append(f"  Create Structure Info: {config.extraction.create_structure_info}")
    lines.append(f"  Extract Recovery:      {config.extraction.extract_recovery}")
    lines.append(f"  Extract DTBO:          {config.extraction.extract_dtbo}")
    
    return "\n".join(lines)


if __name__ == '__main__':
    main()