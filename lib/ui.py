import sys
from typing import Optional

class UI:
    EMOJIS = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌',
        'processing': '🔄'
    }
    
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'purple': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m',
        'bold': '\033[1m'
    }
    
    @staticmethod
    def banner() -> None:
        banner_text = f"""{UI.COLORS['green']}
██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝{UI.COLORS['reset']}
        """
        print(banner_text)
    
    @staticmethod
    def info(message: str) -> None:
        print(f"{UI.EMOJIS['info']} {message}")
    
    @staticmethod
    def success(message: str) -> None:
        print(f"{UI.COLORS['green']}{UI.EMOJIS['success']} {message}{UI.COLORS['reset']}")
    
    @staticmethod
    def warning(message: str) -> None:
        print(f"{UI.COLORS['yellow']}{UI.EMOJIS['warning']} {message}{UI.COLORS['reset']}")
    
    @staticmethod
    def error(message: str, exit_code: Optional[int] = None) -> None:
        print(f"{UI.COLORS['red']}{UI.EMOJIS['error']} {message}{UI.COLORS['reset']}", file=sys.stderr)
        if exit_code is not None:
            sys.exit(exit_code)
    
    @staticmethod
    def processing(message: str) -> None:
        print(f"{UI.COLORS['blue']}{UI.EMOJIS['processing']} {message}{UI.COLORS['reset']}")
    
    @staticmethod
    def section(title: str) -> None:
        print(f"\n{UI.COLORS['bold']}{UI.COLORS['blue']}▶ {title}{UI.COLORS['reset']}")
        print("─" * (len(title) + 2))