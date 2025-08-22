"""
Archive extractor for standard archive formats (.zip, .rar, .7z, .tar, etc.)
"""

import shutil
from pathlib import Path
from typing import Union

from .base import BaseExtractor, ExtractionResult
from ..utils.console import print_info, print_error, print_step


class ArchiveExtractor(BaseExtractor):
    """Extractor for standard archive formats."""
    
    def extract(self, file_path: Union[str, Path], output_dir: Union[str, Path]) -> ExtractionResult:
        """
        Extract archive file.
        
        Args:
            file_path: Path to archive file
            output_dir: Directory to extract to
            
        Returns:
            ExtractionResult with operation status
        """
        source_path = Path(file_path)
        output_path = self._ensure_output_dir(output_dir)
        
        if not source_path.exists():
            return ExtractionResult(success=False, error=f"File not found: {source_path}")
        
        print_step("Extracting Archive", f"{source_path.name}")
        
        try:
            # Determine extraction method based on extension
            extension = source_path.suffix.lower()
            
            if extension == '.zip':
                return self._extract_zip(source_path, output_path)
            elif extension == '.rar':
                return self._extract_rar(source_path, output_path)
            elif extension == '.7z':
                return self._extract_7z(source_path, output_path)
            elif extension in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz']:
                return self._extract_tar(source_path, output_path)
            else:
                # Try generic extraction with patool or py7zr
                return self._extract_generic(source_path, output_path)
                
        except Exception as e:
            error_msg = f"Archive extraction failed: {e}"
            print_error(error_msg)
            return ExtractionResult(success=False, error=error_msg)
    
    def _extract_zip(self, source_path: Path, output_path: Path) -> ExtractionResult:
        """Extract ZIP file using built-in zipfile module."""
        import zipfile
        
        try:
            with zipfile.ZipFile(source_path, 'r') as zip_ref:
                zip_ref.extractall(output_path)
            
            extracted_files = list(output_path.rglob('*'))
            return ExtractionResult(
                success=True,
                output_dir=output_path,
                extracted_files=extracted_files
            )
            
        except Exception as e:
            return ExtractionResult(success=False, error=f"ZIP extraction failed: {e}")
    
    def _extract_rar(self, source_path: Path, output_path: Path) -> ExtractionResult:
        """Extract RAR file using unrar command."""
        # Try using external unrar command
        if shutil.which('unrar'):
            if self._run_command(['unrar', 'x', '-y', str(source_path), str(output_path)]):
                extracted_files = list(output_path.rglob('*'))
                return ExtractionResult(
                    success=True,
                    output_dir=output_path,
                    extracted_files=extracted_files
                )
        
        # Try using patool as fallback
        try:
            import patool
            patool.extract_archive(str(source_path), outdir=str(output_path))
            extracted_files = list(output_path.rglob('*'))
            return ExtractionResult(
                success=True,
                output_dir=output_path,
                extracted_files=extracted_files
            )
        except ImportError:
            pass
        except Exception as e:
            return ExtractionResult(success=False, error=f"RAR extraction failed: {e}")
        
        return ExtractionResult(success=False, error="No RAR extraction tool available")
    
    def _extract_7z(self, source_path: Path, output_path: Path) -> ExtractionResult:
        """Extract 7z file using py7zr or 7z command."""
        # Try using py7zr first
        try:
            import py7zr
            with py7zr.SevenZipFile(source_path, mode='r') as archive:
                archive.extractall(path=output_path)
            
            extracted_files = list(output_path.rglob('*'))
            return ExtractionResult(
                success=True,
                output_dir=output_path,
                extracted_files=extracted_files
            )
        except ImportError:
            pass
        except Exception as e:
            print_error(f"py7zr extraction failed: {e}")
        
        # Try using external 7z command
        if shutil.which('7z'):
            if self._run_command(['7z', 'x', '-y', f'-o{output_path}', str(source_path)]):
                extracted_files = list(output_path.rglob('*'))
                return ExtractionResult(
                    success=True,
                    output_dir=output_path,
                    extracted_files=extracted_files
                )
        
        return ExtractionResult(success=False, error="No 7z extraction tool available")
    
    def _extract_tar(self, source_path: Path, output_path: Path) -> ExtractionResult:
        """Extract tar file using built-in tarfile module."""
        import tarfile
        
        try:
            with tarfile.open(source_path, 'r:*') as tar_ref:
                tar_ref.extractall(output_path)
            
            extracted_files = list(output_path.rglob('*'))
            return ExtractionResult(
                success=True,
                output_dir=output_path,
                extracted_files=extracted_files
            )
            
        except Exception as e:
            return ExtractionResult(success=False, error=f"TAR extraction failed: {e}")
    
    def _extract_generic(self, source_path: Path, output_path: Path) -> ExtractionResult:
        """Try generic extraction using patool."""
        try:
            import patool
            patool.extract_archive(str(source_path), outdir=str(output_path))
            
            extracted_files = list(output_path.rglob('*'))
            return ExtractionResult(
                success=True,
                output_dir=output_path,
                extracted_files=extracted_files
            )
            
        except ImportError:
            return ExtractionResult(success=False, error="patool not available for generic extraction")
        except Exception as e:
            return ExtractionResult(success=False, error=f"Generic extraction failed: {e}")