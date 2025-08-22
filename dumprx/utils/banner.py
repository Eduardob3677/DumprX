from rich.console import Console
from rich.text import Text

console = Console()

BANNER_TEXT = """
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
"""

def show_banner():
    text = Text(BANNER_TEXT)
    text.stylize("bold green")
    console.print(text)

def show_usage():
    console.print("  [bold green]⚓ Usage:[/bold green] dumprx <Firmware File/Extracted Folder -OR- Supported Website Link>")
    console.print("    [bold green]→[/bold green] Firmware File: The .zip/.rar/.7z/.tar/.bin/.ozip/.kdz etc. file\n")
    
    console.print(" [bold blue]>> Supported Websites:[/bold blue]")
    console.print("[cyan]  1. Directly Accessible Download Link From Any Website[/cyan]")
    console.print("[cyan]  2. Filehosters like - mega.nz | mediafire | gdrive | onedrive | androidfilehost[/cyan]")
    console.print("  [yellow]>> Must Wrap Website Link Inside Single-quotes ('')[/yellow]\n")
    
    console.print(" [bold blue]>> Supported File Formats For Direct Operation:[/bold blue]")
    console.print("[cyan]   *.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5[/cyan]")
    console.print("[cyan]   *.ozip | *.ofp | *.ops | *.kdz | ruu_*exe[/cyan]")
    console.print("[cyan]   system.new.dat | system.new.dat.br | system.new.dat.xz[/cyan]")
    console.print("[cyan]   system.new.img | system.img | system-sign.img | UPDATE.APP[/cyan]")
    console.print("[cyan]   *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin[/cyan]")
    console.print("[cyan]   *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin[/cyan]\n")