"""
Base extractor class for all firmware extractors.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List, Optional
from dataclasses import dataclass

from ..utils.console import print_info, print_error


@dataclass
class ExtractionResult:
    """Result of extraction operation."""
    success: bool
    output_dir: Optional[Path] = None
    extracted_files: List[Path] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.extracted_files is None:
            self.extracted_files = []


class BaseExtractor(ABC):
    """Base class for all extractors."""
    
    def __init__(self):
        self.temp_dir: Optional[Path] = None
    
    @abstractmethod
    def extract(self, file_path: Union[str, Path], output_dir: Union[str, Path]) -> ExtractionResult:
        """
        Extract firmware file.
        
        Args:
            file_path: Path to firmware file
            output_dir: Directory to extract to
            
        Returns:
            ExtractionResult with operation status
        """
        pass
    
    def _ensure_output_dir(self, output_dir: Union[str, Path]) -> Path:
        """Ensure output directory exists."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def _create_temp_dir(self, base_dir: Union[str, Path]) -> Path:
        """Create temporary directory for extraction."""
        import tempfile
        
        base_path = Path(base_dir)
        self.temp_dir = Path(tempfile.mkdtemp(dir=base_path, prefix='dumprx_'))
        return self.temp_dir
    
    def _cleanup_temp_dir(self):
        """Clean up temporary directory."""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
            self.temp_dir = None
    
    def _run_command(self, command: List[str], cwd: Optional[Path] = None) -> bool:
        """Run external command."""
        import subprocess
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            return result.returncode == 0
        except Exception as e:
            print_error(f"Command failed: {e}")
            return False