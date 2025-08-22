import asyncio
from pathlib import Path
from typing import List, Dict, Any
from lib.core.logger import logger
from lib.core.config import config
from lib.core.exceptions import ExtractionError
from lib.utils.filesystem import ensure_dir
from .detector import FirmwareDetector
from .extractors import (
    ArchiveExtractor, PayloadExtractor, KDZExtractor,
    OZipExtractor, SDATextractor, HuaweiExtractor,
    SuperImageExtractor
)
from .advanced_extractors import (
    OFPExtractor, OPSExtractor, PACExtractor, NB0Extractor,
    SINExtractor, RUUExtractor, ChunkExtractor, RockchipExtractor,
    AMLExtractor, SparseImageExtractor
)
from .device_tree import DeviceTreeGenerator

class ExtractionManager:
    def __init__(self):
        self.detector = FirmwareDetector()
        self.utils_dir = Path(config.get('paths.utils_dir'))
        
        self.extractors = [
            ArchiveExtractor(self.utils_dir),
            PayloadExtractor(self.utils_dir),
            KDZExtractor(self.utils_dir),
            OZipExtractor(self.utils_dir),
            OFPExtractor(self.utils_dir),
            OPSExtractor(self.utils_dir),
            PACExtractor(self.utils_dir),
            NB0Extractor(self.utils_dir),
            SINExtractor(self.utils_dir),
            RUUExtractor(self.utils_dir),
            ChunkExtractor(self.utils_dir),
            RockchipExtractor(self.utils_dir),
            AMLExtractor(self.utils_dir),
            SparseImageExtractor(self.utils_dir),
            SDATextractor(self.utils_dir),
            HuaweiExtractor(self.utils_dir),
            SuperImageExtractor(self.utils_dir)
        ]
    
    async def extract(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        ensure_dir(output_path)
        
        logger.processing(f"Analyzing firmware: {input_path}")
        
        if input_path.is_file():
            return await self._extract_single_file(input_path, output_path)
        elif input_path.is_dir():
            return await self._extract_directory(input_path, output_path)
        else:
            raise ExtractionError(f"Invalid input path: {input_path}")
    
    async def _extract_single_file(self, file_path: Path, output_path: Path) -> Dict[str, Any]:
        firmware_type = self.detector.detect_type(file_path)
        
        if not firmware_type:
            raise ExtractionError(f"Unsupported firmware type: {file_path}")
        
        logger.info(f"Detected firmware type: {firmware_type}")
        
        extractor = self._get_extractor(file_path)
        if not extractor:
            raise ExtractionError(f"No suitable extractor found for {file_path}")
        
        temp_extract_dir = output_path / "extracted"
        ensure_dir(temp_extract_dir)
        
        success = await extractor.extract(file_path, temp_extract_dir)
        
        if success:
            await self._process_extracted_content(temp_extract_dir, output_path)
        
        return {
            'input': str(file_path),
            'output': str(output_path),
            'type': firmware_type,
            'success': success
        }
    
    async def _extract_directory(self, directory: Path, output_path: Path) -> Dict[str, Any]:
        found_firmware = self.detector.analyze_directory(directory)
        
        if not found_firmware:
            logger.warning(f"No recognized firmware files found in {directory}")
            return {'success': False, 'reason': 'No firmware files found'}
        
        results = []
        for firmware_info in found_firmware:
            logger.processing(f"Processing {firmware_info['path'].name}")
            
            extractor = self._get_extractor(firmware_info['path'])
            if extractor:
                temp_dir = output_path / f"extracted_{firmware_info['path'].stem}"
                ensure_dir(temp_dir)
                
                try:
                    success = await extractor.extract(firmware_info['path'], temp_dir)
                    if success:
                        await self._process_extracted_content(temp_dir, output_path)
                    results.append({'file': str(firmware_info['path']), 'success': success})
                except Exception as e:
                    logger.error(f"Failed to extract {firmware_info['path']}: {e}")
                    results.append({'file': str(firmware_info['path']), 'success': False, 'error': str(e)})
        
        return {'results': results, 'success': any(r['success'] for r in results)}
    
    def _get_extractor(self, file_path: Path):
        for extractor in self.extractors:
            if extractor.can_handle(file_path):
                return extractor
        return None
    
    async def _process_extracted_content(self, temp_dir: Path, final_output: Path) -> None:
        await self._extract_partitions(temp_dir, final_output)
        await self._process_boot_images(final_output)
        await self._organize_output(temp_dir, final_output)
        
        device_tree_gen = DeviceTreeGenerator(final_output, self.utils_dir)
        device_info = await device_tree_gen.generate_device_trees()
        
        logger.success("Firmware extraction and processing completed")
    
    async def _extract_partitions(self, source_dir: Path, output_dir: Path) -> None:
        partitions = config.get('extraction.partitions', [])
        
        for partition in partitions:
            partition_files = list(source_dir.glob(f"**/*{partition}*.img"))
            
            for partition_file in partition_files:
                logger.processing(f"Extracting partition: {partition}")
                
                partition_output = output_dir / partition
                ensure_dir(partition_output)
                
                await self._extract_partition_image(partition_file, partition_output)
    
    async def _extract_partition_image(self, img_file: Path, output_dir: Path) -> None:
        from lib.utils.command import run_command
        
        bin_7zz = self.utils_dir / "bin" / "7zz"
        if not bin_7zz.exists():
            bin_7zz = "7zz"
        
        cmd = [str(bin_7zz), "x", "-snld", str(img_file), "-y", f"-o{output_dir}"]
        result = await run_command(cmd)
        
        if result.returncode != 0:
            fsck_erofs = self.utils_dir / "bin" / "fsck.erofs"
            if fsck_erofs.exists():
                logger.processing("Trying EROFS extraction")
                cmd = [str(fsck_erofs), f"--extract={output_dir}", str(img_file)]
                result = await run_command(cmd)
                
                if result.returncode != 0:
                    logger.warning(f"Could not extract {img_file}")
            else:
                logger.warning(f"Could not extract {img_file} with 7z")
        else:
            img_file.unlink()
    
    async def _organize_output(self, temp_dir: Path, output_dir: Path) -> None:
        for item in temp_dir.rglob('*'):
            if item.is_file():
                relative_path = item.relative_to(temp_dir)
                dest_path = output_dir / relative_path
                ensure_dir(dest_path.parent)
                
                if not dest_path.exists():
                    item.rename(dest_path)
    
    async def _process_boot_images(self, output_dir: Path) -> None:
        boot_images = list(output_dir.glob('**/boot*.img'))
        boot_images.extend(list(output_dir.glob('**/recovery*.img')))
        
        for boot_img in boot_images:
            logger.processing(f"Processing boot image: {boot_img.name}")
            
            boot_output = output_dir / f"{boot_img.stem}RE"
            ensure_dir(boot_output)
            
            unpack_script = self.utils_dir / "unpackboot.sh"
            if unpack_script.exists():
                result = await run_command(['bash', str(unpack_script), str(boot_img)], cwd=boot_output)
                if result.returncode == 0:
                    logger.success(f"Unpacked {boot_img.name}")
                else:
                    logger.warning(f"Failed to unpack {boot_img.name}")
            
            await self._extract_kernel_config(boot_output)
    
    async def _extract_kernel_config(self, boot_dir: Path) -> None:
        kernel_files = list(boot_dir.glob('kernel*'))
        if not kernel_files:
            return
        
        extract_ikconfig = self.utils_dir / "extract-ikconfig"
        if not extract_ikconfig.exists():
            return
        
        for kernel_file in kernel_files:
            try:
                result = await run_command([str(extract_ikconfig), str(kernel_file)])
                if result.returncode == 0 and result.stdout:
                    config_file = boot_dir / "ikconfig"
                    with open(config_file, 'w') as f:
                        f.write(result.stdout)
                    logger.success(f"Extracted kernel config to {config_file}")
                    break
            except Exception as e:
                logger.warning(f"Failed to extract kernel config: {e}")