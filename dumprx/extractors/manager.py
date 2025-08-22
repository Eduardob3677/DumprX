import os
import shutil
from pathlib import Path
from typing import Dict, List

from dumprx.core.config import Config
from dumprx.core.device import DeviceInfo
from dumprx.utils.console import console, info, success, warning
from dumprx.extractors.archive import ArchiveExtractor
from dumprx.extractors.android import AndroidExtractor
from dumprx.extractors.vendor import VendorExtractor

class ExtractionManager:
    def __init__(self, config: Config):
        self.config = config
        self.extractors = {
            'archive': ArchiveExtractor(config),
            'android': AndroidExtractor(config),
            'vendor': VendorExtractor(config)
        }
        
    def extract(self, input_path: str, output_dir: str) -> None:
        """Main extraction logic"""
        input_path = os.path.abspath(input_path)
        output_dir = os.path.abspath(output_dir)
        
        os.makedirs(output_dir, exist_ok=True)
        
        temp_dir = os.path.join(output_dir, 'tmp')
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        try:
            self._setup_external_tools()
            extracted_path = self._extract_firmware(input_path, temp_dir)
            self._process_extracted_files(extracted_path, output_dir)
            self._generate_device_info(output_dir)
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _setup_external_tools(self) -> None:
        """Setup external tools"""
        from dumprx.core.setup import setup_external_tools
        setup_external_tools()
    
    def _extract_firmware(self, input_path: str, temp_dir: str) -> str:
        """Extract firmware based on file type"""
        file_extension = Path(input_path).suffix.lower()
        
        if os.path.isdir(input_path):
            info("Processing directory input")
            shutil.copytree(input_path, temp_dir, dirs_exist_ok=True)
            return temp_dir
        
        extractor = self._get_extractor(input_path, file_extension)
        return extractor.extract(input_path, temp_dir)
    
    def _get_extractor(self, filepath: str, extension: str):
        """Determine appropriate extractor"""
        filename = os.path.basename(filepath).lower()
        
        # Archive formats
        if extension in ['.zip', '.rar', '.7z', '.tar', '.gz', '.tgz']:
            return self.extractors['archive']
        
        # Vendor-specific formats
        if (extension in ['.kdz', '.dz', '.ozip', '.ofp', '.ops', '.nb0', '.pac'] or 
            filename.startswith('ruu_') or 
            'update.app' in filename):
            return self.extractors['vendor']
        
        # Android formats
        if (extension in ['.img', '.bin', '.dat'] or 
            'payload.bin' in filename or
            'system' in filename or
            'super' in filename):
            return self.extractors['android']
        
        return self.extractors['archive']
    
    def _process_extracted_files(self, extracted_path: str, output_dir: str) -> None:
        """Process and organize extracted files"""
        info("Processing extracted files...")
        
        # Move partition images to temp directory root
        self._flatten_partition_images(extracted_path)
        
        # Process partition images
        self._process_partition_images(extracted_path, output_dir)
        
        # Copy special files
        self._copy_special_files(extracted_path, output_dir)
    
    def _flatten_partition_images(self, temp_dir: str) -> None:
        """Move .img files from subdirectories to temp root"""
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.img'):
                    src = os.path.join(root, file)
                    dst = os.path.join(temp_dir, file)
                    if src != dst and not os.path.exists(dst):
                        shutil.move(src, dst)
    
    def _process_partition_images(self, temp_dir: str, output_dir: str) -> None:
        """Process individual partition images"""
        partitions = [
            'system', 'system_ext', 'system_other', 'systemex', 'vendor', 
            'cust', 'odm', 'oem', 'factory', 'product', 'xrom', 'modem', 
            'dtbo', 'dtb', 'boot', 'vendor_boot', 'recovery'
        ]
        
        android_extractor = self.extractors['android']
        
        for partition in partitions:
            img_file = os.path.join(temp_dir, f"{partition}.img")
            if os.path.exists(img_file):
                info(f"Processing {partition} partition")
                android_extractor.extract_partition(img_file, output_dir, partition)
    
    def _copy_special_files(self, temp_dir: str, output_dir: str) -> None:
        """Copy special files to output directory"""
        special_files = [
            '*Android_scatter.txt',
            '*Release_Note.txt'
        ]
        
        import glob
        for pattern in special_files:
            for file_path in glob.glob(os.path.join(temp_dir, pattern)):
                shutil.copy2(file_path, output_dir)
    
    def _generate_device_info(self, output_dir: str) -> None:
        """Generate device information and metadata"""
        original_cwd = os.getcwd()
        try:
            os.chdir(output_dir)
            device_info = DeviceInfo(output_dir)
            device_data = device_info.extract_device_info()
            
            # Generate README with device info
            self._generate_readme(device_data, output_dir)
            
            success("Device information extracted successfully")
            
        finally:
            os.chdir(original_cwd)
    
    def _generate_readme(self, device_data: Dict[str, str], output_dir: str) -> None:
        """Generate README.md with device information"""
        readme_content = f"""# {device_data.get('brand', 'Unknown')} {device_data.get('model', 'Unknown')} Firmware Dump

## Device Information
- **Brand**: {device_data.get('brand', 'Unknown')}
- **Model**: {device_data.get('model', 'Unknown')}
- **Codename**: {device_data.get('codename', 'unknown')}
- **Platform**: {device_data.get('platform', 'unknown')}
- **Manufacturer**: {device_data.get('manufacturer', 'Unknown')}

## Build Information
- **Android Version**: {device_data.get('android_version', 'Unknown')}
- **Build ID**: {device_data.get('build_id', 'Unknown')}
- **Security Patch**: {device_data.get('security_patch', 'Unknown')}
- **Kernel Version**: {device_data.get('kernel_version', 'Unknown')}

## Build Fingerprint
```
{device_data.get('fingerprint', 'Unknown')}
```

## Build Description
```
{device_data.get('description', 'Unknown')}
```

---
*Extracted using DumprX v2.0*
"""
        
        readme_path = os.path.join(output_dir, 'README.md')
        with open(readme_path, 'w') as f:
            f.write(readme_content)