import logging
import sys
from datetime import datetime
from typing import Optional
from enum import Enum
from .config import Config

class Logger:
    def __init__(self, name: str = "DumprX", level: str = "INFO", config: Optional[Config] = None):
        self.name = name
        self.level = getattr(logging, level.upper(), logging.INFO)
        
        if config:
            self.colors = config.ui.colors
            self.emojis = config.ui.emojis
        else:
            self.colors = {
                'primary': '\033[1;36m',
                'success': '\033[1;32m', 
                'warning': '\033[1;33m',
                'error': '\033[1;31m',
                'info': '\033[1;34m',
                'reset': '\033[0m'
            }
            self.emojis = {
                'success': '✅',
                'error': '❌',
                'warning': '⚠️',
                'info': 'ℹ️',
                'progress': '📋',
                'download': '⬇️',
                'extract': '📦',
                'detection': '🔍'
            }
        
        self._reset = self.colors.get('reset', '\033[0m')
        self._bold = "\033[1m"
        self._dim = "\033[2m"
        
        logging.basicConfig(
            level=self.level,
            format="%(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(name)
    
    def _format_message(self, emoji: str, color: str, message: str, details: Optional[str] = None) -> str:
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"{color}{emoji} {self._bold}{message}{self._reset}"
        
        if details:
            formatted += f" {self._dim}({details}){self._reset}"
        
        return formatted
    
    def debug(self, message: str, details: Optional[str] = None):
        if self.level <= logging.DEBUG:
            print(self._format_message("🔍", self.colors.get('info', '\033[1;34m'), message, details))
    
    def info(self, message: str, details: Optional[str] = None):
        print(self._format_message(self.emojis.get('info', 'ℹ️'), self.colors.get('info', '\033[1;34m'), message, details))
    
    def success(self, message: str, details: Optional[str] = None):
        print(self._format_message(self.emojis.get('success', '✅'), self.colors.get('success', '\033[1;32m'), message, details))
    
    def warning(self, message: str, details: Optional[str] = None):
        print(self._format_message(self.emojis.get('warning', '⚠️'), self.colors.get('warning', '\033[1;33m'), message, details))
    
    def error(self, message: str, details: Optional[str] = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = self._format_message(self.emojis.get('error', '❌'), self.colors.get('error', '\033[1;31m'), message, details)
        formatted += f" {self._dim}[{timestamp}]{self._reset}"
        print(formatted)
    
    def critical(self, message: str, details: Optional[str] = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = self._format_message("💥", self.colors.get('error', '\033[1;31m'), message, details)
        formatted += f" {self._dim}[{timestamp}]{self._reset}"
        print(formatted)
    
    def banner(self, text: str):
        lines = text.strip().split('\n')
        max_length = max(len(line) for line in lines) if lines else 0
        
        border_color = self.colors.get('primary', '\033[1;36m')
        print(f"\n{self._bold}{border_color}" + "═" * (max_length + 4) + f"{self._reset}")
        for line in lines:
            padding = max_length - len(line)
            print(f"{self._bold}{border_color}║ {line}{' ' * padding} ║{self._reset}")
        print(f"{self._bold}{border_color}" + "═" * (max_length + 4) + f"{self._reset}\n")
    
    def progress(self, message: str, current: int, total: int):
        if total == 0:
            percentage = 100
        else:
            percentage = int((current / total) * 100)
        
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else bar_length
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        progress_color = self.colors.get('primary', '\033[1;36m')
        print(f"\r{progress_color}⏳ {message}: [{bar}] {percentage}%{self._reset}", end="", flush=True)
        
        if current >= total:
            print()
    
    def step(self, step_num: int, total_steps: int, message: str):
        step_emoji = self.emojis.get('progress', '📋')
        step_color = self.colors.get('info', '\033[1;34m')
        print(f"{step_color}{step_emoji} Step {step_num}/{total_steps}: {self._bold}{message}{self._reset}")
    
    def download(self, message: str, details: Optional[str] = None):
        download_emoji = self.emojis.get('download', '⬇️')
        download_color = self.colors.get('primary', '\033[1;36m')
        print(self._format_message(download_emoji, download_color, message, details))
    
    def extract(self, message: str, details: Optional[str] = None):
        extract_emoji = self.emojis.get('extract', '📦')
        extract_color = self.colors.get('primary', '\033[1;36m')
        print(self._format_message(extract_emoji, extract_color, message, details))
    
    def detect(self, message: str, details: Optional[str] = None):
        detect_emoji = self.emojis.get('detection', '🔍')
        detect_color = self.colors.get('info', '\033[1;34m')
        print(self._format_message(detect_emoji, detect_color, message, details))