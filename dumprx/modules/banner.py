"""
Banner creation and display utilities.

Provides ASCII art banners and welcome messages for DumprX.
"""

from rich.text import Text
from rich.panel import Panel
from rich.align import Align


def create_banner() -> Panel:
    """
    Create the main DumprX banner.
    
    Returns:
        Rich Panel containing the banner
    """
    banner_text = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
"""
    
    subtitle = "Professional Firmware Extraction & Analysis Toolkit"
    version_info = "v2.0.0 - Python Edition"
    
    # Create rich text with styling
    text = Text()
    text.append(banner_text.strip(), style="bold cyan")
    text.append(f"\n\n{subtitle}", style="bold white")
    text.append(f"\n{version_info}", style="dim yellow")
    
    # Center the text and create panel
    centered_text = Align.center(text)
    
    return Panel(
        centered_text,
        border_style="bright_cyan",
        padding=(1, 2)
    )


def create_usage_banner() -> Panel:
    """
    Create usage information banner.
    
    Returns:
        Rich Panel containing usage information
    """
    usage_text = Text()
    usage_text.append("✰ Usage Examples:\n\n", style="bold green")
    
    examples = [
        "dumprx dump firmware.zip                    # Extract local firmware",
        "dumprx dump 'https://mega.nz/file/...'     # Download and extract from URL", 
        "dumprx download 'https://...' -o downloads # Download only",
        "dumprx config show                         # Show configuration",
        "dumprx config set git.github_token TOKEN   # Set GitHub token",
        "dumprx setup                               # Setup dependencies",
        "dumprx test --download --git               # Test integrations",
    ]
    
    for example in examples:
        usage_text.append(f"  {example}\n", style="cyan")
    
    usage_text.append("\n", style="")
    usage_text.append("Supported Formats: ", style="bold yellow")
    usage_text.append("*.zip, *.rar, *.7z, *.tar, *.ozip, *.kdz, *.ofp, *.ops, ", style="white")
    usage_text.append("system.new.dat, payload.bin, *.nb0, *.pac, *super*.img\n\n", style="white")
    
    usage_text.append("Supported Services: ", style="bold yellow") 
    usage_text.append("mega.nz, mediafire.com, Google Drive, AndroidFileHost", style="white")
    
    return Panel(
        usage_text,
        title="Usage Information",
        border_style="green"
    )


def create_error_banner(error_message: str) -> Panel:
    """
    Create error message banner.
    
    Args:
        error_message: Error message to display
        
    Returns:
        Rich Panel containing error information
    """
    error_text = Text()
    error_text.append("☠ Error: ", style="bold red")
    error_text.append(error_message, style="red")
    
    return Panel(
        error_text,
        title="Error",
        border_style="red"
    )


def create_success_banner(success_message: str) -> Panel:
    """
    Create success message banner.
    
    Args:
        success_message: Success message to display
        
    Returns:
        Rich Panel containing success information
    """
    success_text = Text()
    success_text.append("✅ Success: ", style="bold green")
    success_text.append(success_message, style="green")
    
    return Panel(
        success_text,
        title="Success",
        border_style="green"
    )