from typing import Optional, Any
import time
import sys

class ProgressBar:
    def __init__(self, total: int, description: str = "", width: int = 50):
        self.total = total
        self.current = 0
        self.description = description
        self.width = width
        self.start_time = time.time()
    
    def update(self, amount: int = 1) -> None:
        self.current = min(self.current + amount, self.total)
        self.render()
    
    def render(self) -> None:
        percent = (self.current / self.total) * 100 if self.total > 0 else 0
        filled = int((self.current / self.total) * self.width) if self.total > 0 else 0
        bar = "█" * filled + "░" * (self.width - filled)
        
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        
        eta = (self.total - self.current) / rate if rate > 0 else 0
        eta_str = f"{int(eta)}s" if eta < 3600 else f"{int(eta/3600)}h{int((eta%3600)/60)}m"
        
        sys.stdout.write(f"\r🔄 {self.description} [{bar}] {percent:.1f}% ({self.current}/{self.total}) ETA: {eta_str}")
        sys.stdout.flush()
        
        if self.current >= self.total:
            print()  # New line when complete
    
    def finish(self) -> None:
        self.current = self.total
        self.render()

def create_progress_bar(total: int, description: str = "") -> ProgressBar:
    return ProgressBar(total, description)