#!/usr/bin/env python3

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

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
    
    text = Text(banner_text, style="bold green")
    panel = Panel(text, border_style="green", padding=(1, 2))
    console.print(panel)

def show_usage():
    usage_text = """
[bold green]📱 Usage:[/bold green] dumprx <Firmware File/Directory/URL>

[bold blue]Supported Files:[/bold blue]
• Archive formats: .zip, .rar, .7z, .tar, .tar.gz, .tgz, .tar.md5
• Firmware formats: .ozip, .ofp, .ops, .kdz, ruu_*.exe
• Image formats: .img, .bin, system.new.dat, payload.bin, UPDATE.APP
• Partition files: *.nb0, *.chunk*, *.pac, *super*.img, *.sin

[bold blue]Supported Sources:[/bold blue]
• Local files and directories
• Direct download URLs
• File hosting services: mega.nz, mediafire, gdrive, onedrive, androidfilehost

[bold yellow]Note:[/bold yellow] Wrap URLs in quotes when using as arguments
    """
    
    console.print(usage_text)