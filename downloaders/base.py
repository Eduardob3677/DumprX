from abc import ABC, abstractmethod
from pathlib import Path


class BaseDownloader(ABC):
    @abstractmethod
    def download(self, url: str, output_dir: Path) -> str:
        pass