"""
Android firmware extractor for various Android-specific formats.
"""

from pathlib import Path
from typing import Union

from dumprxbase import BaseExtractor, ExtractionResult
from dumprxutils.console import print_info, print_error, print_step, print_warning


class AndroidExtractor(BaseExtractor):
    """Extractor for Android firmware formats."""
    
    def extract(self, file_path: Union[str, Path], output_dir: Union[str, Path]) -> ExtractionResult:
        """
        Extract Android firmware file.
        
        Args:
            file_path: Path to firmware file
            output_dir: Directory to extract to
            
        Returns:
            ExtractionResult with operation status
        """
        source_path = Path(file_path)
        output_path = self._ensure_output_dir(output_dir)
        
        if not source_path.exists():
            return ExtractionResult(success=False, error=f"File not found: {source_path}")
        
        filename = source_path.name.lower()
        
        print_step("Extracting Android Firmware", f"{source_path.name}")
        
        try:
            # Determine extraction method based on filename/format
            if 'system.new.dat' in filename:
                return self._extract_system_dat(source_path, output_path)
            elif filename == 'payload.bin':
                return self._extract_payload(source_path, output_path)
            elif filename == 'UPDATE.APP':
                return self._extract_update_app(source_path, output_path)
            else:
                print_warning(f"Android extractor not implemented for: {filename}")
                return ExtractionResult(success=False, error="Android format not yet supported")
                
        except Exception as e:
            error_msg = f"Android extraction failed: {e}"
            print_error(error_msg)
            return ExtractionResult(success=False, error=error_msg)
    
    def _extract_system_dat(self, source_path: Path, output_path: Path) -> ExtractionResult:
        """Extract system.new.dat file using sdat2img."""
        print_info("Extracting system.new.dat file...")
        
        # Look for required files
        dat_file = source_path
        transfer_list = source_path.parent / 'system.transfer.list'
        
        if not transfer_list.exists():
            return ExtractionResult(success=False, error="system.transfer.list not found")
        
        output_img = output_path / 'system.img'
        
        try:
            # Import and use the existing sdat2img utility
            # This would integrate with the existing utils/sdat2img.py
            from dumprxutils.sdat2img import main as sdat2img_main
            
            sdat2img_main(str(transfer_list), str(dat_file), str(output_img))
            
            return ExtractionResult(
                success=True,
                output_dir=output_path,
                extracted_files=[output_img]
            )
            
        except Exception as e:
            return ExtractionResult(success=False, error=f"sdat2img extraction failed: {e}")
    
    def _extract_payload(self, source_path: Path, output_path: Path) -> ExtractionResult:
        """Extract payload.bin file."""
        print_warning("payload.bin extraction not fully implemented yet")
        return ExtractionResult(success=False, error="payload.bin extraction not yet supported")
    
    def _extract_update_app(self, source_path: Path, output_path: Path) -> ExtractionResult:
        """Extract UPDATE.APP file using splituapp."""
        print_info("Extracting UPDATE.APP file...")
        
        try:
            # Import and use the existing splituapp utility
            # This would integrate with the existing utils/splituapp.py
            from dumprxutils.splituapp import extract as splituapp_extract
            
            # Change to output directory for extraction
            import os
            original_cwd = os.getcwd()
            os.chdir(output_path)
            
            try:
                splituapp_extract(str(source_path), None)
                extracted_files = list(output_path.glob('*.img'))
                
                return ExtractionResult(
                    success=True,
                    output_dir=output_path,
                    extracted_files=extracted_files
                )
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            return ExtractionResult(success=False, error=f"UPDATE.APP extraction failed: {e}")