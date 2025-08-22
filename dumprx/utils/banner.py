from rich.console import Console
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
    console.print(text)
    
def show_usage():
    usage_text = """
[bold green]🌟 Usage:[/bold green] [cyan]dumprx <Firmware File/Extracted Folder -OR- Supported Website Link>[/cyan]

[bold blue]📁 Firmware File:[/bold blue] The .zip/.rar/.7z/.tar/.bin/.ozip/.kdz etc. file

[bold blue]🌐 Supported Websites:[/bold blue]
    [cyan]1. Directly Accessible Download Link From Any Website
    2. Filehosters like - mega.nz | mediafire | gdrive | onedrive | androidfilehost[/cyan]
    [yellow]>> Must Wrap Website Link Inside Single-quotes ('')[/yellow]

[bold blue]📋 Supported File Formats For Direct Operation:[/bold blue]
    [cyan]*.zip | *.rar | *.7z | *.tar | *.tar.gz | *.tgz | *.tar.md5
    *.ozip | *.ofp | *.ops | *.kdz | ruu_*exe
    system.new.dat | system.new.dat.br | system.new.dat.xz
    system.new.img | system.img | system-sign.img | UPDATE.APP
    *.emmc.img | *.img.ext4 | system.bin | system-p | payload.bin
    *.nb0 | .*chunk* | *.pac | *super*.img | *system*.sin[/cyan]
    """
    console.print(usage_text)